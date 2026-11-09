# Self-hosted Gateway with SIWC Plan-usage upstream (not user-supplied recipe is settled)

Context: the project needs Cognigy bots to run model calls without a paid API key, using a ChatGPT
Plus plan as the source of usage. We evaluated three Upstream routes: (1) the browser-session token
against api.openai.com — empirically dead (403 scope gates, verified with our own credential);
(2) the reverse-engineered conversation backend — rejected on Terms grounds and Cloudflare fragility;
(3) the official Sign-in-with-ChatGPT "plan usage" OAuth grant (`chatgpt.tokens.use.direct`) against
api.openai.com/v1/responses — sanctioned, self-serve, Plus-eligible.

Decision: the Gateway uses the SIWC Plan-usage grant as its only Upstream, with one rotating refresh
credential owned exclusively by the Gateway's Adapter. The Codex-OAuth route remains a documented
fallback; the conversation route is permanently out of scope. The Gateway is single-user, dev/testing
scope, without pooling or resale of plan usage.

Considered Options: paid API key (rejected: zero-marginal-cost is a hard user requirement);
chat2api-style conversation proxies (rejected: Terms, fragility); Codex-OAuth-to-backend-api/codex
(fallback: works but datacenter-IP Cloudflare risk and unofficial).

Consequences: the Gateway depends on OpenAI's plan-availability catalog and per-app usage caps; 429s
are plan-shaped (`subscription_sharing_usage_limit_exceeded`) rather than API-shaped; credential
storage sites that are not the user's local machine sit in an unresolved SIWC-Terms grey zone
(accepted for dev use in this Codespace, re-authorization is cheap if revoked).
