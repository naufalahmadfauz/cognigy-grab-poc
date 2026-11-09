# Gateway Runbook

Self-hosted Gateway: Cognigy → this Codespace → ChatGPT plan usage (no API key).
Design decision: `docs/adr/0001-siwc-plan-usage-gateway.md`.

## Stack (what runs where)

```
Cognigy (OpenAIProvider, API Type Responses)
  → https://<random>.trycloudflare.com            (cloudflared Quick Tunnel — machine-safe, see note)
    → gateway/adapter.py   (127.0.0.1:4002, OpenAI-compatible + sk-… Bearer auth)
      → https://api.openai.com/v1/responses   (SIWC plan-usage grant, billed to the Plus plan)
```

**Why a Quick Tunnel instead of the Codespaces port forward:** GitHub's
`*-4002.app.github.dev` public forward serves a browser-style "Codespaces Access Port"
consent wall to callers without browser cookies — problematic for server-side API callers
like Cognigy's cloud, which then sees intermittent 401s with no body. The Quick Tunnel
exposes plain HTTPS with no consent logic. Caveat: the hostname changes on every tunnel
start, so after a Codespace restart point Cognigy's Custom URL at the new one. (The
long-term fix is a named tunnel from the user's own machine — ADR-0001's hosting note.)

There is no LiteLLM in this stack yet; the Adapter plays the LiteLLM role
(sk- keys, /v1/models, /v1/chat/completions, /v1/responses, stream + non-stream).
LiteLLM can be slotted in front later without touching the Cognigy connection
(use LiteLLM master_key as the Cognigy key, the current public key as the internal one).

## Files

| Path | Meaning |
|---|---|
| `gateway/adapter.py` | the Gateway (credential owner + translator) |
| `gateway/start_gateway.sh` | idempotent start |
| `gateway/siwc_authorize.py` | one-time (or re-)authorization helper, runs on the user's PC |
| `.credentials/siwc_credentials.json` | issued `client_id` + refresh grant (mode 600, git-ignored) |
| `.credentials/siwc_access_grant.json` | live access grant; **rotates on refresh — single owner is the Adapter** |
| `.credentials/adapter_keys.json` | Adapter keys: `internal` (for a future LiteLLM) + `public` (`sk-cognigy-…` this is the Cognigy key) |
| `.credentials/siwc_reauth_required.json` | appears if the refresh grant dies |

## Runbook

**Model called fine before, now Cognigy errors with `reauth_required`:**
1. Download `gateway/siwc_authorize.py` again if needed, run `python siwc_authorize.py` on the PC
   that owns the ChatGPT login, approve.
2. Drag-drop the fresh `siwc_credentials.json` into the Explorer (it lands at repo root;
   `git status` should show it as untracked-and-ignored), then restart the Adapter:
   `pkill -f "adapter[.]py"` in one command, then `bash gateway/start_gateway.sh`
   (the Adapter reads the credential file at start-up).

**Codespace was stopped (gateway unreachable):**
1. `bash gateway/start_gateway.sh` — starts Adapter **and** the Quick Tunnel, prints
   `TUNNEL URL: https://…trycloudflare.com`.
2. In Cognigy, set Custom URL to that printed hostname (bare host, no path).
3. Old `…-4002.app.github.dev` forwards still work for interactive poking, but treat
   them as diagnostics only.

**Check health:** `curl http://127.0.0.1:4002/healthz` — expect `{"ok": true, "credential_state": "ok"}`.
Errors/rotation events: `tail -f /tmp/opencode/adapter.log` (secrets never logged; tagged
`gw=` lines mark every request with durations — the trace for timeout hunts).

**Path rules the Adapter accepts:** any of `/responses`, `/v1/responses`, `/v1/chat/completions`,
bare-root POST, single or doubled slashes — so Cognigy-style base URLs just work.

**Instrumentation note (for diagnosing):** tagged `gw=recv` / `gw=done` / `gw=streamdone` /
`gw=authfail` lines in `/tmp/opencode/adapter.log` were added while chasing the GitHub-forward
instability; they're permanent ops logging now (request path, stream flag, client, duration).

## Known limits (per ADR 0001)

- **SSE framing (stream responses).** SSE has no `Content-Length`/chunked framing, so under
  HTTP/1.1 keep-alive a client cannot tell a "paused" stream from an "ended" one. All stream
  responses (raw passthrough and chat-transform) therefore send `Connection: close` and set
  `close_connection` so the socket ends when the relay does. Found 2026-10-17: without this,
  model calls completed in ~3 s but Cognigy's client hung on an open connection until its own
  cancel/retry kicked in — the "hangs, then errors" symptom. Never remove these two lines.
- **Latency budget (the timeout race).** Upstream output throughput differs by model slug:
  `gpt-5.6-terra` ≈ 40 tok/s, `gpt-5.6-luna` ≈ 74 tok/s (measured 2026-10-17, plan-usage route).
  Long generations therefore take 50–110 s and can exceed Cognigy's LLM-node timeout: the
  symptom is Cognigy hanging, then reporting a provider error ("terminated"). Fixes, in order:
  1. prefer `*.luna` slugs for chatty flows,
  2. raise the node's response timeout,
  3. enable streaming in the Cognigy node if available (first bytes ~2.4 s),
  4. keep requested output sizes modest.
  Effect of the SIWC-`reasoning.effort` parameter on total time: none measured (effort low vs
  medium on a 3.5k-token essay: 109.2 s vs 103.3 s) — generation speed dominates, not reasoning.

- **Dev/testing scope.** Usage draws from the Plus plan the account uses normally; the 5-hour and
  weekly caps are shared (Settings → Usage shows the app-level caps).
- **One refresh owner.** Never run two Adapters against one credential — rotation is single-use with
  reuse detection; a racing process kills the grant (terminal → runbook above).
- **Cognigy retries** up to 3× on non-200; plan-shape 429s surface as
  `subscription_sharing_usage_limit_exceeded` (pausing, not model-empty).
- Treat `siwc_credentials.json` and `adapter_keys.json` as passwords. They are git-ignored; don't
  open them in shared chats.
