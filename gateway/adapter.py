#!/usr/bin/env python3
"""
Gateway Adapter: owns the SIWC plan-usage credential and exposes an OpenAI-compatible surface.

Responsibilities (per ADR 0001):
  * single owner of the rotating refresh credential (thread-locked, atomic persistence)
  * forcesUpstream the SIWC body rules on POST /v1/responses (store:false, stream:true,
    instructions instead of system items, strips unsupported params)
  * translates OpenAI chat/completions <-> Responses format
  * buffers upstream SSE into plain JSON when the caller asks for non-stream
  * Bearer token auth (internal key for LiteLLM, public sk- keys for direct use)

Endpoints:
  GET  /healthz
  GET  /v1/models                 -> standard OpenAI list shape
  POST /v1/responses              -> SIWC direct route
  POST /v1/chat/completions       -> translated

Stdlib only.
"""
import json
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------------------------------------------------------- configuration
CREDS_DIR = "/workspaces/cognigy-grab-poc/.credentials"
CREDS_FILE = f"{CREDS_DIR}/siwc_credentials.json"
GRANT_FILE = f"{CREDS_DIR}/siwc_access_grant.json"          # written by adapter on first refresh
REAUTH_FLAG = f"{CREDS_DIR}/siwc_reauth_required"

TOKEN_URL = "https://auth.openai.com/api/accounts/oauth/token"
MODELS_URL = "https://api.openai.com/v1/models"
INFER_URL = "https://api.openai.com/v1/responses"
RESOURCE = "https://api.openai.com/v1"
DIRECT_SCOPE = "chatgpt.tokens.use.direct"
UPSTREAM_TIMEOUT = 180

TERMINAL_REFRESH_CODES = {
    "invalid_grant", "invalid_refresh_token", "token_expired", "refresh_token_expired",
    "refresh_token_invalidated", "refresh_token_reused",
}

# params the SIWC direct route rejects; we silence them here so Cognigy/LiteLLM bodies pass
STRIP_TOP = {
    "background", "conversation", "max_output_tokens", "max_tool_calls", "metadata",
    "moderation", "multi_agent", "prompt", "prompt_cache_retention", "safety_identifier",
    "temperature", "top_logprobs", "top_p", "truncation",
    "previous_response_id", "user",
}

log_lock = threading.Lock()


def log(*parts):
    with log_lock:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{stamp}]", *parts, file=sys.stderr, flush=True)


def atomic_write(path, payload):
    tmp = f"{path}.tmp-{secrets.token_hex(4)}"
    with open(tmp, "w") as handle:
        json.dump(payload, handle, indent=2)
    try:
        os_chmod06(tmp)
    except Exception:
        pass
    os_replace(tmp, path)


def os_chmod06(path):
    import os
    os.chmod(path, 0o600)


def os_replace(a, b):
    import os
    os.replace(a, b)


# ---------------------------------------------------------------- credential store
class RefreshOwner:
    """Thread-safe owner of the rotating SIWC refresh credential."""

    def __init__(self):
        self.lock = threading.Lock()
        self._access = None
        self._expires = 0.0
        self._base = None       # static parts of siwc_credentials.json
        self._refresh = None    # live refresh token (rotates)
        self.state = "ok"
        self.last_error = None
        self._load_base()
        self._load_cached_grant()

    def _load_base(self):
        with open(CREDS_FILE) as handle:
            self._base = json.load(handle)
        self._refresh = self._base.get("refresh_token")
        if not self._refresh:
            raise RuntimeError("siwc_credentials.json has no refresh_token")

    def _load_cached_grant(self):
        try:
            with open(GRANT_FILE) as handle:
                grant = json.load(handle)
            if grant.get("refresh_token") and grant.get("access_token"):
                self._refresh = grant["refresh_token"]
                self._access = grant["access_token"]
                self._expires = float(grant.get("expires_at_epoch") or 0)
                log("loaded cached access grant (expires_at",
                    datetime.fromtimestamp(min(self._expires, 2**31), timezone.utc).isoformat(), ")")
        except FileNotFoundError:
            pass
        except Exception as exc:
            log("WARN: could not load cached grant:", repr(exc))

    # -- refresh machinery ---------------------------------------------------
    def _persist(self, access, expires_in, refresh):
        grant = {
            "kind": "siwc-access-grant",
            "client_id": self._base.get("client_id"),
            "access_token": access,
            "refresh_token": refresh,
            "expires_at_epoch": time.time() + expires_in - 60,
            "rotated_at": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write(GRANT_FILE, grant)

    def _do_refresh(self):
        form = {
            "grant_type": "refresh_token",
            "client_id": self._base["client_id"],
            "refresh_token": self._refresh,
            "resource": RESOURCE,
        }
        request = urllib.request.Request(
            TOKEN_URL,
            data=urllib.parse.urlencode(form).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:400]
            code = ""
            try:
                code = json.loads(body).get("error", "")
            except Exception:
                code = str(exc)
            log("REFRESH FAILED:", exc.code, code)
            if str(code) in TERMINAL_REFRESH_CODES:
                self.state = "reauth_required"
                self.last_error = f"{code}: run gateway/siwc_authorize.py again to re-bind"
                atomic_write(REAUTH_FLAG, {"error": code, "at": datetime.now(timezone.utc).isoformat()})
                raise RuntimeError(f"refresh terminal: {code}") from None
            self.state = "transient_error"
            self.last_error = f"HTTP {exc.code}: {body}"
            raise
        new_access = payload.get("access_token")
        new_refresh = payload.get("refresh_token") or self._refresh
        expires_in = int(payload.get("expires_in") or 3600)
        if not new_access:
            raise RuntimeError("refresh response had no access_token")
        # persist BEFORE serving anything with the new refresh token (rotation is single-use)
        self._access = new_access
        self._expires = time.time() + expires_in - 60
        self._refresh = new_refresh
        self._persist(new_access, expires_in, new_refresh)
        self.state = "ok"
        log("access grant renewed; rotation persisted; expires_at_epoch set (+" + str(expires_in) + "s)")

    def access_token(self) -> str:
        now = time.time()
        if self._access and now < self._expires - 30:
            return self._access
        with self.lock:
            if not (self._access and time.time() < self._expires - 30):
                self._do_refresh()
            return self._access


# ---------------------------------------------------------------- translation
def body_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text") or part.get("content") or "")
        return "".join(parts)
    return ""


def chat_to_responses(body: dict) -> dict:
    instructions = []
    items = []
    for message in body.get("messages") or []:
        role = message.get("role")
        text = body_text(message.get("content"))
        if role in ("system", "developer"):
            if text:
                instructions.append(text)
        elif role == "assistant":
            items.append({"type": "message", "role": "assistant",
                          "content": [{"type": "output_text", "text": text}]})
        else:  # user (and anything else) -> user turn
            items.append({"type": "message", "role": "user",
                          "content": [{"type": "input_text", "text": text}]})
    upstream = {
        "model": body.get("model"),
        "input": items,
        "store": False,
        "stream": True,
    }
    if instructions:
        upstream["instructions"] = "\n\n".join(instructions)
    if body.get("tools"):  # function/custom tools only on this route
        upstream["tools"] = body["tools"]
    return upstream


def sanitize_responses_body(body: dict) -> dict:
    upstream = dict(body)
    system_bits = []
    raw_input = upstream.get("input")
    if isinstance(raw_input, str):
        upstream["input"] = [{"type": "message", "role": "user",
                              "content": [{"type": "input_text", "text": raw_input}]}]
    elif isinstance(raw_input, list):
        cleaned = []
        for item in raw_input:
            if isinstance(item, dict) and item.get("role") == "system":
                system_bits.append(body_text(item.get("content")))
            else:
                cleaned.append(item)
        upstream["input"] = cleaned
    instructions = upstream.pop("instructions", "") or ""
    if system_bits:
        instructions = (instructions + "\n\n" + "\n\n".join(system_bits)).strip()
    if instructions:
        upstream["instructions"] = instructions
    for key in STRIP_TOP:
        upstream.pop(key, None)
    upstream["store"] = False
    upstream["stream"] = True
    return upstream


def collect_output_text(response_obj: dict) -> str:
    text = []
    for item in response_obj.get("output") or []:
        if item.get("type") == "message":
            for chunk in item.get("content") or []:
                if chunk.get("type") == "output_text" and chunk.get("text"):
                    text.append(chunk["text"])
    return "".join(text)


def usage_to_chat(usage: dict | None) -> dict:
    usage = usage or {}
    prompt = usage.get("input_tokens") or 0
    completion = usage.get("output_tokens") or 0
    return {"prompt_tokens": prompt, "completion_tokens": completion,
            "total_tokens": usage.get("total_tokens") or prompt + completion}


def chat_completion_from_response(model: str, response_obj: dict) -> dict:
    return {
        "id": response_obj.get("id") or "chatcmpl-siwc",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": collect_output_text(response_obj)},
            "finish_reason": "stop",
        }],
        "usage": usage_to_chat(response_obj.get("usage")),
    }


def sse_parse(line: bytes):
    """Return (event_name_or_None, data_str_or_None, is_comment)."""
    text = line.decode("utf-8", "replace").rstrip("\r\n")
    if not text:
        return None, None, True
    if text.startswith(":"):
        return None, None, True
    if text.startswith("event:"):
        return ("event", text[6:].strip(), False)
    if text.startswith("data:"):
        return ("data", text[5:].strip(), False)
    return None, text, False


# ---------------------------------------------------------------- HTTP plumbing
def read_json(handler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length) if length and length < 16_000_000 else None
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid JSON body: {exc}")


def send_json(handler, status: int, payload: dict):
    body = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def map_upstream_error(shape: dict) -> int:
    code = str(shape.get("code") or (shape.get("error") or {}).get("code") or "")
    if "usage_limit_exceeded" in code:
        return 429
    if "not_eligible" in code or "route_not_supported" in code or "invalid_user" in code:
        return 403
    return 502


class UpstreamError(Exception):
    def __init__(self, status: int, payload):
        self.status = status
        self.payload = payload
        super().__init__(f"upstream {status}")


# ---------------------------------------------------------------- upstream calls
def post_upstream(url: str, payload: dict, token: str, accept: str):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": accept,
        },
        method="POST",
    )
    return urllib.request.urlopen(request, timeout=UPSTREAM_TIMEOUT)


def buffered_response(owner: RefreshOwner, payload: dict) -> dict:
    """Run one plan-usage SSE call and return the final response object."""
    for attempt in (1, 2):
        try:
            with post_upstream(INFER_URL, payload, owner.access_token(), "text/event-stream") as response:
                event = None
                final = None
                error_shape = None
                data_buffers = []
                done_items = {}  # output_index -> item (upstream ships empty output on completed)
                for raw in response:
                    kind, value, blank = sse_parse(raw)
                    if blank or kind is None:
                        continue
                    if kind == "event":
                        event = value
                        data_buffers = []
                    elif kind == "data":
                        data_buffers.append(value)
                        if value == "[DONE]":
                            continue
                        try:
                            parsed = json.loads("".join(data_buffers)) if data_buffers else None
                        except Exception:
                            parsed = None
                        if not isinstance(parsed, dict):
                            continue
                        kind_parsed = parsed.get("type") or event
                        if kind_parsed == "response.output_item.done":
                            index = parsed.get("output_index")
                            done_items[index if index is not None else len(done_items)] = parsed.get("item")
                        elif kind_parsed == "response.completed":
                            final = parsed.get("response")
                        elif kind_parsed == "response.failed":
                            error_shape = (parsed.get("response") or {}).get("error") or \
                                          {"message": "upstream reported failure"}
                if final:
                    if final.get("output") in (None, []) and done_items:
                        final["output"] = [done_items[key] for key in sorted(done_items)]
                    return final
                if error_shape:
                    raise UpstreamError(map_upstream_error(error_shape), {"error": error_shape})
                raise UpstreamError(504, {"error": {"message": "stream ended without completion"}})
        except UpstreamError:
            raise
        except urllib.error.HTTPError as exc:
            try:
                shape = json.loads(exc.read().decode(errors="replace"))
            except Exception:
                shape = {"error": {"message": f"upstream HTTP {exc.code}"}}
            enriched = shape.get("error") or {}
            code = shape.get("code") or enriched.get("code") or ""
            # expired access grant mid-life: the refresh owner rotates once per terminal-like 401
            if exc.code == 401 and attempt == 1 and owner.state == "ok":
                log("upstream 401; forcing refresh and retrying once")
                with owner.lock:
                    owner._do_refresh()  # noqa: SLF001 — controlled single retry
                continue
            log("upstream error:", exc.code, code)
            raise UpstreamError(exc.code if exc.code != 401 else 403, shape) from None
    raise UpstreamError(502, {"error": {"message": "exhausted upstream retries"}})


def stream_passthrough(owner: RefreshOwner, payload: dict, handler, timeout_tag=True):
    """responses->responses streaming: forward upstream SSE verbatim."""
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    # SSE has no Content-Length/chunked framing — under HTTP/1.1 keep-alive a
    # client cannot tell "paused" from "ended". Declare close-framing explicitly.
    handler.send_header("Connection", "close")
    handler.close_connection = True  # server closes the socket when the handler returns
    handler.end_headers()
    try:
        with post_upstream(INFER_URL, payload, owner.access_token(), "text/event-stream") as response:
            for chunk in iter(lambda: response.read(4096) or None, None):
                handler.wfile.write(chunk)
                handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError):
        log("client hung up mid-stream")


def stream_chat_transform(owner: RefreshOwner, payload: dict, handler, model: str):
    """chat SSE out of a responses SSE: translate on the fly."""
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    # Same close-framing rule as stream_passthrough (see comment there).
    handler.send_header("Connection", "close")
    handler.close_connection = True
    handler.end_headers()

    def chat_frame(delta=None, finish=None, usage=None):
        frame = {"id": f"chatcmpl-siwc-{secrets.token_hex(6)}", "object": "chat.completion.chunk",
                 "created": int(time.time()), "model": model,
                 "choices": [{"index": 0, "delta": ({} if delta is None and finish else delta or {}),
                              "finish_reason": finish}]}
        if usage:
            frame["usage"] = usage
        return b"data: " + json.dumps(frame).encode() + b"\n\n"

    sent_role = False
    try:
        with post_upstream(INFER_URL, payload, owner.access_token(), "text/event-stream") as response:
            event, data_parts = None, []
            for raw in response:
                kind, value, blank = sse_parse(raw)
                if blank:
                    continue
                if kind == "event":
                    event, data_parts = value, []
                elif kind == "data":
                    data_parts.append(value)
                    blob = "".join(data_parts)
                    if blob == "[DONE]":
                        continue
                    try:
                        parsed = json.loads(blob)
                    except Exception:
                        continue
                    kind_parsed = parsed.get("type")
                    if kind_parsed == "response.output_text.delta":
                        if not sent_role:
                            handler.wfile.write(chat_frame({"role": "assistant", "content": ""}))
                            sent_role = True
                        handler.wfile.write(chat_frame({"content": parsed.get("delta") or ""}))
                        handler.wfile.flush()
                    elif kind_parsed == "response.completed":
                        usage = usage_to_chat((parsed.get("response") or {}).get("usage"))
                        handler.wfile.write(chat_frame(finish="stop", usage=usage))
                        handler.wfile.write(b"data: [DONE]\n\n")
                        handler.wfile.flush()
                        return
    except (BrokenPipeError, ConnectionResetError):
        log("client hung up mid-chat-stream")


# ---------------------------------------------------------------- request handler
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # auth: internal key (LiteLLM) or any public sk- key (direct Cognigy use)
    def authorized(self):
        header = self.headers.get("Authorization") or ""
        token = header[7:] if header.startswith("Bearer ") else ""
        keys = self.server.accepted_keys
        return bool(token) and token in keys

    def do_GET(self):  # noqa: N802
        owner = self.server.owner
        path = self.server.route(self.path)
        if path == "healthz":
            send_json(self, 200, {"ok": self.server.healthy, "credential_state": owner.state,
                                  "last_error": owner.last_error})
            return
        if not self.authorized():
            log(f"gw=authfail method=GET path={self.path[:80]} "
                f"client={self.client_address[0]} auth={(self.headers.get('Authorization') or '')[:14]}…")
            send_json(self, 401, {"error": {"message": "missing or unknown Bearer key"}})
            return
        if path == "models":
            try:
                request = urllib.request.Request(MODELS_URL,
                                                 headers={"Authorization": f"Bearer {owner.access_token()}"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.load(response)
            except urllib.error.HTTPError as exc:
                send_json(self, exc.code, {"error": {"message": f"catalog error {exc.code}"}})
                return
            models = [m for m in (payload.get("models") or []) if m.get("visibility") == "list"]
            data = [{"id": m.get("slug"), "object": "model",
                     "created": 0, "owned_by": "openai",
                     "display_name": m.get("display_name")} for m in models]
            send_json(self, 200, {"object": "list", "data": data})
            return
        send_json(self, 404, {"error": {"message": "not found"}})

    def do_POST(self):  # noqa: N802
        owner = self.server.owner
        path = self.server.route(self.path)
        if not self.authorized():
            log(f"gw=authfail method=POST path={self.path[:80]} "
                f"client={self.client_address[0]} auth={(self.headers.get('Authorization') or '')[:14]}…")
            send_json(self, 401, {"error": {"message": "missing or unknown Bearer key"}})
            return
        owner.access_token()
        if owner.state == "reauth_required":
            send_json(self, 403, {"error": {"message": "SIWC grant dead — re-run gateway/siwc_authorize.py",
                                            "code": "reauth_required"}})
            return
        if path not in ("responses", "chat"):
            allowed = {
                "responses": "POST /v1/responses",
                "chat": "POST /v1/chat/completions",
                "models": "GET /v1/models",
                "healthz": "GET /healthz",
            }
            send_json(self, 404, {"error": {"message": "not found; try one of " +
                                            ", ".join(allowed.values())}})
            return
        try:
            body = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": {"message": str(exc)}})
            return

        try:
            if path == "responses":
                if not body.get("model"):
                    send_json(self, 400, {"error": {"message": "model is required"}})
                    return
                upstream_body = sanitize_responses_body(body)
                t0 = time.time()
                cf = self.headers.get("Cf-Connecting-Ip") or "-"
                in_sz = len(body.get("instructions") or "") + len(json.dumps(body.get("input") or ""))
                if body.get("stream"):
                    log(f"gw=recv path={path} stream=1 model={body.get('model')} in={in_sz} "
                        f"client={cf} orig={self.client_address[0]}")
                    stream_passthrough(owner, upstream_body, self)
                    log(f"gw=streamdone path={path} model={body.get('model')} "
                        f"dur={time.time() - t0:.1f}s")
                    return
                log(f"gw=recv path={path} stream=0 model={body.get('model')} in={in_sz} "
                    f"client={cf} orig={self.client_address[0]}")
                response_obj = buffered_response(owner, upstream_body)
                response_obj.setdefault("status", "completed")
                log(f"gw=done path={path} model={body.get('model')} "
                    f"dur={time.time() - t0:.1f}s upstream_status={response_obj.get('status')}")
                send_json(self, 200, response_obj)
                return
            if path == "chat":
                if not body.get("model"):
                    send_json(self, 400, {"error": {"message": "model is required"}})
                    return
                upstream_body = chat_to_responses(body)
                t0 = time.time()
                if body.get("stream"):
                    log(f"gw=recv path={path} stream=1 model={body.get('model')} "
                        f"client={self.client_address[0]}")
                    stream_chat_transform(owner, upstream_body, self, body.get("model"))
                    log(f"gw=streamdone path={path} model={body.get('model')} "
                        f"dur={time.time() - t0:.1f}s")
                    return
                log(f"gw=recv path={path} stream=0 model={body.get('model')} "
                    f"client={self.client_address[0]}")
                response_obj = buffered_response(owner, upstream_body)
                log(f"gw=done path={path} model={body.get('model')} "
                    f"dur={time.time() - t0:.1f}s")
                send_json(self, 200, chat_completion_from_response(body.get("model"), response_obj))
                return
        except UpstreamError as exc:
            send_json(self, exc.status if exc.status in (429, 400, 403) else 502, exc.payload)
            return
        except Exception as exc:  # noqa: BLE001 — last-resort JSON error
            log("adapter internal error:", repr(exc))
            send_json(self, 502, {"error": {"message": f"adapter error: {exc}"}})
            return
        send_json(self, 404, {"error": {"message": "not found"}})

    def log_message(self, *args):
        pass


class AdapterServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, owner, accepted_keys):
        self.owner = owner
        self.accepted_keys = accepted_keys
        self.healthy = True
        super().__init__(address, Handler)

    @staticmethod
    def route(path: str) -> str:
        """Normalize: collapse slashes, ignore /v1 prefix depth, map to canonical route."""
        parsed = urllib.parse.urlparse(path)
        segments = [s for s in parsed.path.strip("/").split("/") if s]
        # drop any number of leading version segments
        while segments and segments[0] == "v1":
            segments.pop(0)
        last = segments[-1] if segments else ""
        if last == "responses" or last == "":
            return "responses"
        if last == "completions" and len(segments) >= 2 and segments[-2] == "chat":
            return "chat"
        if last == "models":
            return "models"
        if last == "healthz":
            return "healthz"
        return last  # unknown -> callers answer 404


def main():
    with open(f"{CREDS_DIR}/adapter_keys.json") as handle:
        keys = json.load(handle)
    accepted = {keys["internal"], *keys["public"]}
    owner = RefreshOwner()
    server = AdapterServer(("127.0.0.1", 4002), owner, accepted)
    public_count = len(keys["public"])
    log(f"adapter on 127.0.0.1:4002 | internal key + {public_count} public key(s) accepted")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("shutting down")


if __name__ == "__main__":
    main()
