---
name: vida-api
description: "Use the Vida API to configure and operate Agents, Computer Agents, Contacts, Tasks, communications, reporting, and authorized platform administration."
---

# Vida API

Use this skill when creating, configuring, operating, or troubleshooting Vida resources through the
API. It supplies workflow and verification rules; the live OpenAPI document supplies exact request
and response schemas.

## Sources of truth

- OpenAPI: `https://vida.io/docs/apiv2.json`
- API guides: `https://vida.io/docs/api-reference/overview`
- Canonical skill: `https://github.com/VIDA-Global/vida-skill`
- API base URL: `VIDA_API_BASE_URL`, normally `https://api.vida.dev`
- API token: `VIDA_API_KEY`

Read the current OpenAPI operation before constructing a request. Do not infer a field, method,
permission, or response shape from memory when the operation is documented.

## Load the relevant reference

Read only the references needed for the current workflow, but read each selected reference fully
before acting:

- `references/voice-agent-configuration.md`: Agent settings, model/voice/function/App discovery,
  staging, publishing, phone/SIP, reporting fields, versions, and experiments
- `references/computer-agent-configuration.md`: Computer provisioning, configuration boundaries,
  health, logs, diagnostics, repair, backups, skills, credentials, channels, workspaces, Browser
  access, reusable helpers, memory, sessions, and schedules
- `references/tasks-contacts-and-communications.md`: Contacts, objectives, communication and
  Computer Tasks, retries, batches, repeating/one-off Tasks, outbound communication, and inbound
  email events
- `references/logs-conversations-and-reporting.md`: bounded log queries, full conversations,
  metrics, experiment analysis, and incident evidence
- `references/platform-administration.md`: account hierarchy, onboarding, members, tokens,
  optional reseller/partner capabilities, templates, inbound-email policy, webhooks, domains, and
  embedded access

Use the public workflow guides for conceptual explanations:

- Agent configuration: `https://vida.io/docs/api-reference/agent-guides/overview`
- Computer Agents: `https://vida.io/docs/api-reference/agent-guides/computer-agents`
- Tasks: `https://vida.io/docs/api-reference/platform-guides/tasks-and-automation`
- Contacts: `https://vida.io/docs/api-reference/platform-guides/contacts-and-objectives`
- Logs and reporting: `https://vida.io/docs/api-reference/platform-guides/logs-conversations-and-reporting`
- Account onboarding: `https://vida.io/docs/api-reference/platform-guides/accounts-access-and-onboarding`
- Integrations and webhooks: `https://vida.io/docs/api-reference/platform-guides/integrations-email-and-webhooks`

## Authentication and scope

Vida API authentication uses the `token` query parameter:

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/account?token=$VIDA_API_KEY"
```

Resolve identity before making a scoped request:

- `targetAccountId` selects an authorized Vida account. Use it on account-scoped operations unless
  the account is already in the path or the operation explicitly uses another scope parameter.
- `accountId` owns a newly created Task. For Agent work it normally matches `targetAccountId`.
- `agentConfigId` identifies a staging, live, or saved Agent configuration. It is never an account
  ID. Use this public name consistently.
- `versionId` identifies a saved Agent configuration snapshot.
- Computer operations use `/api/v2/computer/accounts/{targetAccountId}/...`; do not add a different
  account ID in the query or body unless that operation explicitly requires it.
- Organization, reseller, and partner scope parameters are not interchangeable. Use only the
  hierarchy levels the authenticated account actually has.

For organization workflows, list child Agent accounts with
`GET /api/v2/listAccounts?targetOrganizationId=...`, then use the selected Agent account as
`targetAccountId`. Never assume an organization account, Agent account, and Agent configuration
share an ID.

## Operating method

Use this sequence for every material workflow:

1. Read the authenticated account and resolve the exact target resource.
2. Read the current resource and the current OpenAPI operation.
3. Discover account-specific choices such as models, voices, functions, Apps, skills, channels, or
   features instead of copying catalog values.
4. Validate account scope, required fields, timestamps, phone formats, and destructive impact.
5. Apply the smallest intended change. Preserve unrelated replacement-style arrays or objects.
6. Re-read the resource.
7. Test the real capability with safe representative input.
8. Poll asynchronous work to a terminal state and inspect its result or linked conversation.
9. Report exact IDs, state, verification evidence, and unresolved user action.

An accepted write, queued Task, started login, lifecycle job, repair, backup, restore, publish, or
scheduled run is not completion evidence.

## Change boundaries

- Read operations are the default starting point.
- Publishing, account creation, number purchase/return, provisioning, deprovisioning, restore,
  credential deletion, memory deletion, session reset, channel logout, Task deletion, and other
  destructive or billable changes require clear user intent.
- Do not retry an uncertain create or batch request until reads prove what was created.
- Use managed-secret APIs for declared sensitive skill values. Do not put those values in Agent
  configuration, Task context, helper arguments, workspace files, or setup state.
- Prefer purpose-built Computer endpoints over generic tool invocation. Invoke only a tool returned
  by the selected Agent's tool catalog and verify its effect.
- Do not claim a capability is unavailable until the relevant catalog, entitlement, status, and
  verification endpoints have been checked.

## Request construction

Use URL encoding for token and query values, JSON for documented JSON bodies, and multipart only
where OpenAPI declares it. Typical scoped JSON request:

```bash
curl -s -X POST \
  "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @request.json
```

Before a mutation, check:

- phone numbers use E.164, such as `+15551234567`;
- Unix scheduling and log timestamps use seconds;
- `targetAccountId` and Task `accountId` identify the intended Agent account;
- `agentConfigId` came from an Agent configuration read;
- replacement arrays contain every member that should remain;
- required OpenAPI fields and documented enums are satisfied.

## Completion report

Return the method and endpoint, target account, relevant resource IDs, final state, post-write read,
and representative capability evidence. Include pagination state when a result may be incomplete.
If an external login, approval, DNS change, payment, or other user action remains, identify it
plainly and leave the result pending or blocked.

## Error handling

- `401`: verify the token is present as the documented query parameter.
- `403` or scope error: re-read the authenticated account and verify target hierarchy and access.
- `404`: verify both the resource ID and selected account; do not broaden scope automatically.
- `409`: re-read current state and reconcile before retrying.
- `422` or validation error: compare the request with current OpenAPI and account-specific catalogs.
- `5xx`, timeout, or lost response after a write: query by returned or caller-owned correlation IDs
  before resubmitting.
- Asynchronous failure: inspect the terminal job, Task, run, linked conversation, and bounded logs
  before proposing remediation.
