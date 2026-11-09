# Cognigy Grab POC — Domain Glossary

Language for the project's goal: self-hosting an LLM gateway that lets Cognigy bots
use a ChatGPT consumer session instead of a paid OpenAI API key.

## Language

**Gateway**:
The self-hosted, OpenAI-compatible server that Cognigy connects to; it accepts an `sk-…` key and a Custom URL, exactly like a commercial OpenAI endpoint.
_Avoid_: proxy (reserved for upstream translation tools), server, relay

**Session credential**:
Browser-session material from a ChatGPT consumer account (the JWT `accessToken` and opaque `sessionToken` from `/api/auth/session`) used in place of an API key.
_Avoid_: session account, OAuth session, cookie (too narrow)

**Upstream**:
The OpenAI/ChatGPT backend the Gateway actually calls with a Session credential in place of a paid API key.
_Avoid_: backend, provider

**Plan-usage grant (SIWC)**:
The official Sign-in-with-ChatGPT OAuth grant (`chatgpt.tokens.use.direct`) that allows a registered app to call the OpenAI Responses API with usage billed against a ChatGPT consumer plan instead of API credits.
_Avoid_: session token, sk replacement, free API

**Access grant**:
A short-lived OAuth access token minted from a stored refresh credential and used as the Gateway's Upstream bearer token.
_Avoid_: access token (ambiguous with the browser-session JWT)

**Adapter**:
The small translation layer between the Gateway and the Upstream that converts OpenAI-API requests into whatever the session-authenticated backend accepts.
_Avoid_: bridge, connector

**Cognigy connection**:
The Generative AI Connection object in Cognigy's LLM Editor (provider type OpenAIProvider) configured with the Gateway's Custom URL, a model name, and an API-type setting.
_Avoid_: LLM connection, provider config

**Port forwarding**:
Exposing the Gateway running inside this workspace to the internet so Cognigy's cloud can reach it.
