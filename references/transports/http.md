# Direct HTTP transport

Read this reference when using Vida's HTTP API. Shared identity classification, scope,
workflow, and verification rules remain in `../../SKILL.md`.

## Secure access and setup

Check whether `VIDA_API_KEY` is available in the current runtime without printing
its value. If the user is setting up this skill for the first time, use the
[repository setup guide](https://github.com/VIDA-Global/vida-skill#readme) to
install the complete skill directory, then actively give the user the applicable
key setup instructions from that guide in chat. If they use a local Bash CLI,
show the private terminal input commands and explain that they must launch the
agent from that same terminal. If they use a desktop or remote agent, guide them
to that host's private secret mechanism, or offer the local CLI path if none is
available. Ask which environment they use if it is unclear. A key exported in a
different terminal or stored on the user's machine is not necessarily available to
this runtime.
Have the user enter the key privately; never ask them to disclose it in chat or
echo it in a command result. Resume the account preflight after they have done so.

If the key is missing, guide the signed-in user through creating a key for the narrowest account
scope that can complete the work:

- **One Agent:** open the Agent, then **Settings → Developer → API Keys**
  (`https://vida.io/app/agent/{agentAccountId}/settings/developer`). This key is appropriate for
  operating that Agent account.
- **Reseller and its customers:** open **For Developers → API Keys**
  (`https://vida.io/app/reseller/{resellerAccountId}/forDevelopers/developer`). Use a reseller key
  when the work requires the reseller's authorized downstream organizations or Agents.
- **Partner and its resellers:** open **Settings → Advanced → API Keys**
  (`https://vida.io/app/partner/{partnerAccountId}/settings/developer`). Use this only for an
  eligible partner-level workflow.

Have the user select **New Key**, give it a recognizable purpose, and store the returned value in a
secure environment or secret manager as `VIDA_API_KEY`. Never ask the user to paste the key into
chat, a workspace file, a Task, or a work log. Do not reveal it through environment inspection,
shell tracing, full request URLs, or tool output. Since Vida uses a `token` query parameter,
avoid logging the constructed URL and redact it from errors and reports. If the API Keys item or
key creation is unavailable, do not assume a paid upgrade is necessary or select a broader account
silently. Use Vida support to establish the missing access or eligibility when no authenticated
preflight is possible. See
`https://vida.io/docs/api-reference/authentication`.

The first key cannot be created through `/api/v2/tokens` because that operation already requires
authentication. After the user securely supplies the key, restart this preflight with
`GET /api/v2/account` before performing scoped work.

## Authentication

Vida API authentication uses the `token` query parameter:

```text
GET /api/v2/account?token=<URL-encoded VIDA_API_KEY>
```

Use a request method that reads the key from the runtime secret or environment and keeps the
expanded URL out of command arguments, shell traces, logs, and error messages. The example shows
the API shape, not a URL to print or paste. Do not use verbose HTTP tracing with this token.

## Request construction

Read the live OpenAPI operation for exact methods, parameters, request bodies, response schemas,
and pagination. Resolve local schema references as needed. A missing MCP tool does not mean
the corresponding HTTP operation is unsupported.

Use URL encoding for token and query values, JSON for documented JSON bodies, and multipart only
where OpenAPI declares it. Typical scoped JSON request shape:

```text
POST /api/v2/tasks?token=<URL-encoded VIDA_API_KEY>&targetAccountId=<Agent account ID>
Content-Type: application/json

<JSON body matching the current OpenAPI operation>
```

Do not follow redirects to another origin with credentials. Treat HTTP status, response body,
pagination, and asynchronous state as evidence; a successful network request alone is not
workflow completion. Never print a raw account response without inspecting its fields for secrets.
