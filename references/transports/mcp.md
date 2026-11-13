# MCP transport

Read this reference when executing through a connected Vida MCP server. Shared identity,
scope, workflow, and verification rules remain in `../../SKILL.md`.

## Connection and credentials

Use the host's Vida connection and supported OAuth login or reconnect flow. Do not require an
HTTP API key when the MCP connection is working. Never ask the user to paste a gateway access
token into chat, copy client credentials between applications, or extract upstream credentials.
If tools are absent, distinguish an unconfigured connection from an unsupported API capability.

`get_profile` identifies the linked user but does not establish hierarchy privileges. Discover
and call the tool for `GET /api/v2/account` without `targetAccountId` to perform the requester
preflight in the main skill. A targeted account read does not replace this requester identity.

## Discover and map operations

Use `search_operations` whenever the exact operation or tool is unclear. Search by the method
and path from a workflow reference, or the requested capability. Request `includeInputSchema:true`
when the host has not supplied the matching tool's complete argument schema. Check the returned
method and path, not only the first search result. The host may prefix tool names with a namespace.

Execute the returned typed tool using its live schema. Path and query parameters are exposed
as tool arguments; JSON request fields may be nested under `body`. Do not guess that nesting.
Pass `targetAccountId` explicitly for authorized downstream work, including reseller-to-organization
and organization-to-Agent operations. Preserve path-specific account IDs and do not invent a second
target parameter. Do not pass `token` or HTTP headers as tool arguments unless a tool explicitly
documents them as business inputs.

The complete API is intended to be discoverable, not limited to examples. A tool missing from
the host's initially visible list may still be discoverable. Inspect the connected catalog before
declaring a capability unavailable. For response semantics, pagination, or unsupported payload
formats not explained in tool metadata, consult the corresponding current OpenAPI operation.

## Interpret results and recover

Generated API tool results include `operation` and `response` in `structuredContent` when the
host exposes it. Inspect `isError`, `response.ok`, `response.status`, and `response.data`.
JSON data may be encoded as a string; decode it before interpreting resource state. Some hosts
only expose text, which may be truncated; do not claim complete results from truncated output.
Reduce query size, paginate, or obtain an untruncated supported result before concluding.

An MCP protocol success does not mean the upstream API operation succeeded. Apply the main
skill's error and asynchronous verification rules to the upstream result. After an OAuth challenge,
use the host's reconnect flow. Do not treat a gateway access token as a direct HTTP credential.
Consult the main skill's transport-switching rules before any HTTP fallback, especially after
an uncertain write.
