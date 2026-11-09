#!/usr/bin/env python3
"""
One-time SIWC (Sign-in with ChatGPT) authorization for plan-usage billing.

Run this on the machine whose browser you will click in:

    python siwc_authorize.py

What it does:
  1. Starts a tiny local web server on http://127.0.0.1:<free port>/auth/callback (required form:
     literal 127.0.0.1, path exactly /auth/callback).
  2. Opens your browser at OpenAI's authorize endpoint with client_id=dynamic_agent_client
     (self-serve registration) + PKCE. You log in with the ChatGPT account whose plan should pay
     for usage and approve.
  3. OpenAI redirects back with a code AND a newly issued client_id (oaiapp_...).
  4. The script exchanges the code (no client secret needed), validates the granted scopes,
     and fetches the account's model catalog as a sanity check.
  5. It writes siwc_credentials.json next to itself. Transfer that file to the Gateway machine
     (Codespace): drag-drop it into the VS Code Explorer. Never share its contents.

Standard library only (Python 3.8+). No third-party packages.
"""
import base64
import hashlib
import json
import os
import secrets
import socket
import sys
import threading
import urllib.parse
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

AUTHORIZE_URL = "https://auth.openai.com/api/accounts/authorize"
TOKEN_URL = "https://auth.openai.com/api/accounts/oauth/token"
MODELS_URL = "https://api.openai.com/v1/models"
RESOURCE = "https://api.openai.com/v1"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
REQUIRED_SCOPE = "chatgpt.tokens.use.direct"
APP_NAME = "cognigy-grab-gateway"

HERE = os.path.dirname(os.path.abspath(__file__))
HOST_ID_FILE = os.path.join(HERE, "siwc_host_id.json")
CREDS_FILE = os.path.join(HERE, "siwc_credentials.json")

result = {"error": None, "code": None, "client_id": None}


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def load_or_create_host_id() -> str:
    """Stable per-host identifier, required on first registration."""
    if os.path.exists(HOST_ID_FILE):
        try:
            return json.load(open(HOST_ID_FILE))["host_id"]
        except Exception:
            pass
    host_id = f"urn:uuid:{uuid.uuid4()}"
    json.dump({"host_id": host_id, "created_at": datetime.now(timezone.utc).isoformat()},
              open(HOST_ID_FILE, "w"), indent=2)
    return host_id


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if urllib.parse.urlparse(self.path).path != "/auth/callback":
            self.send_response(404)
            self.end_headers()
            return
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "error" in query:
            result["error"] = query.get("error_description", query["error"])[0]
        else:
            result["code"] = query.get("code", [None])[0]
            result["client_id"] = query.get("client_id", [None])[0]
        body = ("<html><body style='font-family:sans-serif'><h3>Authorization received.</h3>"
                "<p>You can close this tab and return to the terminal window.</p></body></html>")
        payload = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):  # silence request logging
        pass


def wait_for_callback(port: int) -> None:
    server = HTTPServer(("127.0.0.1", port), CallbackHandler)
    server.serve_forever(poll_interval=0.2)


def token_exchange(data: dict) -> dict:
    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(data).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_catalog(access_token: str) -> None:
    """Best-effort: show which models the plan account may call on the direct route."""
    try:
        request = urllib.request.Request(MODELS_URL, headers={"Authorization": f"Bearer {access_token}"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        models = payload.get("models") or []
        visible = [m["slug"] for m in models if m.get("visibility") == "list"]
        hidden = [m["slug"] for m in models if m.get("visibility") != "list"]
        print(f"\n  Model catalog ({len(visible)} callable): {', '.join(visible)}")
        if hidden:
            print(f"  hidden entries present ({len(hidden)}), first few: {hidden[0:3]}")
    except Exception as exc:  # non-fatal; region policy or cold cache may 403/503 here
        print(f"\n  Catalog probe failed (non-fatal): {exc}")


def main() -> None:
    port = 8765 if socket.socket().connect_ex(("127.0.0.1", 8765)) != 0 else 0
    redirect_uri = f"http://127.0.0.1:{port}/auth/callback"

    verifier = b64url(secrets.token_bytes(64))
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    host_id = load_or_create_host_id()

    params = {
        "client_id": "dynamic_agent_client",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "resource": RESOURCE,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "agent_name_hint": APP_NAME,
        "ext_agent_host_id": host_id,
    }
    authorize = AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

    threading.Thread(target=wait_for_callback, args=(port,), daemon=True).start()

    print("SIWC one-time authorization (plan usage)")
    print(f"  Listening on {redirect_uri}")
    print("  Opening your browser for the ChatGPT sign-in ...")
    print("  If it does not open by itself, paste this URL into your browser:")
    print(f"\n{authorize}\n")
    try:
        webbrowser.open(authorize)
    except Exception:
        pass

    deadline = 300  # seconds to click through
    import time
    for _ in range(int(deadline / 0.2)):
        time.sleep(0.2)
        if result["error"] or result["code"]:
            break
    else:
        print("\nFAIL: no callback within 5 minutes. Run again and click sooner.")
        return
    if result["error"]:
        print(f"\nFAIL: OpenAI returned an error: {result['error']}")
        return

    issued_client_id = result["client_id"]
    if not issued_client_id or not str(issued_client_id).startswith("oaiap"):
        print("\nWARN: expected an issued client_id from the callback; got something unexpected. "
              "Continuing with what we received.")
    print(f"  Issued client_id: {issued_client_id}")

    print("  Exchanging the code for tokens ...")
    try:
        token = token_exchange({
            "grant_type": "authorization_code",
            "code": result["code"],
            "client_id": issued_client_id,
            "code_verifier": verifier,
            "redirect_uri": redirect_uri,
            "resource": RESOURCE,
        })
    except Exception as exc:
        body = getattr(exc, "read", lambda: b"")()
        print(f"\nFAIL: token exchange error: {exc} {body.decode(errors='replace')[:400]}")
        return

    granted = token.get("scope") or ""
    has_direct = REQUIRED_SCOPE in granted
    print(f"  Granted scope: {granted[:200]}")
    if not has_direct:
        print(f"\nFAIL: the grant is missing {REQUIRED_SCOPE}. Plan-usage billing will not work. "
              "Nothing was saved.")
        return

    credentials = {
        "kind": "siwc-plan-usage-credentials",
        "client_id": issued_client_id,
        "ext_agent_host_id": host_id,
        "refresh_token": token.get("refresh_token"),
        "access_token": token.get("id_token") and token.get("access_token") or token.get("access_token"),
        "scope": granted,
        "obtained_at": datetime.now(timezone.utc).isoformat(),
        "note": "Password-grade material. Refresh token rotates on every refresh; "
                "exactly one process may own it.",
    }
    with open(CREDS_FILE, "w") as handle:
        json.dump(credentials, handle, indent=2)
    try:
        os.chmod(CREDS_FILE, 0o600)
    except Exception:
        pass

    print(f"\nOK — saved {CREDS_FILE}")
    print("  Next: transfer this one file to the Codespace (drag-drop into VS Code Explorer).")
    print("  Then close this script. The Gateway takes it from there.")
    print("\n  (Access-token sanity check of the model catalog follows; errors here are non-fatal.)")
    fetch_catalog(token.get("access_token"))


if __name__ == "__main__":
    main()
