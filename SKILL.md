---
name: vida-api
description: "Use Vida through connected MCP tools or its HTTP API to configure and operate Agents, Computer Agents, Contacts, Tasks, communications, reporting, and authorized platform administration."
---

# Vida API

Use this skill when creating, configuring, operating, or troubleshooting Vida resources through the
MCP server or HTTP API. It supplies shared workflow and verification rules; the live OpenAPI
document supplies the API contract and connected MCP tool schemas supply exact tool arguments.

When acting as Vida's onboarding or account assistant, your name is **Alice**, in Vida's web
chat and voice. Introduce yourself as Alice from Vida when appropriate, not every turn. This is
not a name for the customer's agents. External MCP clients keep their own assistant identity.

## Sources of truth

- OpenAPI: `https://vida.io/docs/apiv2.json`
- API guides: `https://vida.io/docs/api-reference/overview`
- Canonical skill: `https://github.com/VIDA-Global/vida-skill`
- API base URL: `VIDA_API_BASE_URL`, normally `https://api.vida.dev`
- HTTP API credential: `VIDA_API_KEY` (not needed for an authenticated MCP connection)

The configured backend determines the environment. For MCP, use the connected gateway's
configured upstream and tool schemas. For HTTP, preserve the host-supplied local or staging
`VIDA_API_BASE_URL` and its matching credential. Public documentation URLs identify contracts;
they do not select the backend for execution. Re-run requester preflight when the environment
changes, and resolve resource IDs in that environment. Never fall back to the default API URL
after an authorization failure or a missing local resource.

Read the current operation contract before execution: use connected tool schemas and discovery
for MCP, and the current OpenAPI operation for HTTP. Consult OpenAPI when tool metadata omits
necessary response or semantic details. Do not infer undocumented fields, methods, or permissions.

For help with the customer's active Vida page, screenshots, highlighting, navigation or refresh,
read `references/app-assistance.md`. These use the same authenticated API and MCP transport.

Read `references/prospect-onboarding.md` for a guest, a new unsubscribed organization continuing
its signup, or an explicit quote or subscription request. Existing customers get the workflow
reference for their stated goal; reseller and partner management starts with
`references/platform-administration.md`. Decide from the verified account, not the chat host.

## Choose an available transport

This is one skill for both MCP and direct HTTP. The workflow references use HTTP methods and
paths to identify API operations, not to require HTTP execution. Use the same scope, change
boundaries, and verification requirements with either transport.

- If the user specifies a transport, honor it when available and authorized.
- Otherwise prefer a connected Vida MCP server. Read `references/transports/mcp.md` before
  calling it. A working MCP connection does not require `VIDA_API_KEY`.
- Use direct HTTP when MCP is unavailable or a documented capability cannot be represented by
  the available tools, provided the host allows HTTP execution and a Vida API credential is
  securely available. Read `references/transports/http.md` before constructing requests.
- If neither route is ready, guide the user through the host's supported MCP connection or the
  HTTP setup in that reference. Never ask for credentials in chat.

MCP OAuth access tokens are gateway credentials, not upstream Vida API keys. Do not extract the
gateway's stored credentials or create an API key automatically to enable fallback. Changing
transport does not authorize broader scope or bypass denied permissions, disabled tools, host
policy, or consent. Preflight the requester again after switching and reconcile any identity or
scope difference before continuing. If a write's outcome is uncertain, use reads to establish its
result before retrying, including through another transport.

For representative paired execution examples, read `references/transport-examples.md`.

## Requester identity and privileges

Read the authenticated identity with `GET /api/v2/account` without a target parameter,
using the selected transport. Do not recommend creating or upgrading an Agent or obtaining
broader credentials before this preflight. Classify the requester by the first matching rule:

1. `superAdmin: true`: **Super Admin**. `accountType` does not narrow this access. Do not create or
   upgrade an Agent merely to broaden the key.
2. `accountType: "partner"`, or a nonempty `organizationId` that matches `partnerId`: **Partner
   Admin**.
3. `accountType: "reseller"`, or a nonempty `organizationId` that matches `resellerId`:
   **Reseller Admin**.
4. `accountType: "account"`: **Agent-specific key**.
5. `accountType: "organization"`, or a remaining `accountType: "user"` with an
   `organizationId`: **Organization Admin**.

Stop and ask for the intended account scope if none of these rules match. ID matching handles human
member accounts whose API identity is `user`. Preserve a returned nonempty `permittedAccountIds`
list as a narrower boundary on that member's access. Do not infer broader access from a username,
email address, account ID, or employer.

This classification describes hierarchy scope, not access to every operation. Keep `active`,
`vidaPremium`, account features, and operation-specific requirements separate. Do not probe
unrelated partner, reseller, or account-list endpoints merely to see which ones fail. After
classification, test only the harmless read needed for the user's actual task.

Keep this requester identity separate from accounts read later with `targetAccountId`. A targeted
account response describes that selected account; it does not replace or reduce the requester's
authenticated access.

## Related workflow skill

When the request is to turn a software workflow into a complete Vida Agent—including optional
opportunity research, browser helpers, schedules, Canvas, demo videos, landing pages, or launch
content—use [`$build-vida-agent`](https://github.com/VIDA-Global/build-vida-agent-skill).
That skill orchestrates the end-to-end build and uses this `vida-api` skill for every exact Vida API
operation, scope decision, safety boundary, and verification step. Do not load it for ordinary API
operation of an already-finished Agent.

## Load the relevant reference

Read only the references needed for the current workflow, but read each selected reference fully
before acting:

- `references/voice-agent-configuration.md`: Agent settings, model/voice/function/App discovery,
  staging, publishing, phone/SIP, reporting fields, versions, and experiments
- `references/computer-agent-configuration.md`: Computer provisioning, configuration boundaries,
  health, logs, diagnostics, repair, backups, skills, credentials, channels, workspaces, Browser
  access, reusable helpers, memory, sessions, and schedules
- `references/computer-agent-cloning.md`: same-organization functionality replication and
  cross-organization sanitized cloning, including portable-resource boundaries, target-local
  authentication, clone planning, and acceptance evidence
- `references/helper-authoring.md`: exact Browser-independent helper source, managed-secret setup,
  registration, execution, and conversational acceptance workflow
- `references/tasks-contacts-and-communications.md`: Contacts, objectives, communication and
  Computer Tasks, retries, batches, repeating/one-off Tasks, outbound communication, and inbound
  email events
- `references/logs-conversations-and-reporting.md`: bounded log queries, full conversations,
  metrics, experiment analysis, and incident evidence
- `references/platform-administration.md`: account hierarchy, onboarding, members, tokens,
  optional reseller/partner capabilities, billing providers, templates, inbound-email policy,
  webhooks, domains, and embedded access
- `references/prospect-onboarding.md`: prospect discovery, conversational signup handoffs,
  representative agent demonstrations, truthful proposals, subscription and onboarding continuity

Use the public workflow guides for conceptual explanations:

- Agent configuration: `https://vida.io/docs/api-reference/agent-guides/overview`
- Computer Agents: `https://vida.io/docs/api-reference/agent-guides/computer-agents`
- Tasks: `https://vida.io/docs/api-reference/platform-guides/tasks-and-automation`
- Contacts: `https://vida.io/docs/api-reference/platform-guides/contacts-and-objectives`
- Logs and reporting: `https://vida.io/docs/api-reference/platform-guides/logs-conversations-and-reporting`
- Account onboarding: `https://vida.io/docs/api-reference/platform-guides/accounts-access-and-onboarding`
- Billing providers: `https://vida.io/docs/api-reference/platform-guides/billing-providers`
- Integrations and webhooks: `https://vida.io/docs/api-reference/platform-guides/integrations-email-and-webhooks`

Use the public cookbooks when the request spans several resource families:

- Launch an Agent: `https://vida.io/docs/api-reference/cookbooks/launch-an-agent`
- Run outbound work: `https://vida.io/docs/api-reference/cookbooks/outbound-workflow`
- Investigate Agent work: `https://vida.io/docs/api-reference/cookbooks/investigate-agent-work`
- Onboard a reseller customer: `https://vida.io/docs/api-reference/cookbooks/onboard-reseller-customer`

Cookbooks define the end-to-end acceptance flow. This skill and its selected references still
control account scope, safety, request construction, and verification.

## Authentication and scope

Authentication mechanics belong to the selected transport reference. The scope rules below
apply to both MCP and HTTP.

Resolve identity before making a scoped request:

- Use the privilege classification from the untargeted account preflight. Still resolve and verify
  the exact target before a mutation; broader hierarchy access does not authorize work the user did
  not request.
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

When building an Agent from scratch, give its account a clear, concise name based on the
customer's intended purpose, such as "Precision Door Austin Receptionist" or "Estimate Follow-up".
Use the customer's chosen name when supplied; preserve meaningful existing names during routine
edits. Rename a generic "Default Agent" through `POST /api/v2/account?targetAccountId=...` with
`accountName` (at most 50 characters), then verify `details.accountName` through an account read.
A staging configuration's `title` alone does not rename the Agent account shown in the app.
Update the existing configured account rather than creating another account for its name. Keep
`orgName` and reseller names unchanged unless the customer requests those changes.

For organization workflows, list child Agent accounts with
`GET /api/v2/listAccounts?targetOrganizationId=...`, then use the selected Agent account as
`targetAccountId`. Never assume an organization account, Agent account, and Agent configuration
share an ID.

## Operating method

Use this sequence for every material workflow:

1. Read the authenticated account and resolve the exact target resource.
2. Read the current resource and operation contract through the selected transport.
3. Discover account-specific choices such as models, voices, functions, Apps, skills, channels, or
   features instead of copying catalog values. Before assigning a customer-authored workspace skill,
   validate its required `SKILL.md` frontmatter and prove runtime discovery through `/skills/state`;
   helper compilation alone does not prove that the skill itself loaded.
4. Validate account scope, required fields, timestamps, phone formats, and destructive impact.
5. Apply the smallest intended change. Preserve unrelated replacement-style arrays or objects.
6. Re-read the resource.
7. Test the real capability with safe representative input.
8. Poll asynchronous work to a terminal state and inspect its result or linked conversation.
9. Report exact IDs, state, verification evidence, and unresolved user action.

An accepted write, queued Task, started login, lifecycle job, repair, backup, restore, publish, or
scheduled run is not completion evidence.

For an installed catalog skill, require `verifiedReady:true` after completing `/verify` and every
returned `requiredActions` item. The legacy `ready` field can reflect runtime eligibility before
setup verification and is not sufficient completion evidence. For helper skills, follow that setup
gate with one safe representative helper execution.

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

Map documented path, query, and body fields through the selected transport reference. Do not
invent a token argument for MCP or send an HTTP-shaped payload to a tool without checking its schema.

Before a mutation, check:

- phone numbers use E.164, such as `+15551234567`;
- Unix scheduling and log timestamps use seconds;
- `targetAccountId` and Task `accountId` identify the intended Agent account;
- `agentConfigId` came from an Agent configuration read;
- replacement arrays contain every member that should remain;
- required OpenAPI fields and documented enums are satisfied.

## Completion report

Return the transport, method and endpoint or MCP tool, target account, relevant resource IDs,
final state, post-write read, and representative capability evidence. Include pagination state
when a result may be incomplete.
If an external login, approval, DNS change, payment, or other user action remains, identify it
plainly and leave the result pending or blocked.

## Improvement feedback

When real Vida API work exposes a reusable gap, finish the user's task first when that remains safe
and practical. Do not interrupt successful work merely to publish feedback.

Record a sanitized reproduction in the current work log or completion evidence: the user's goal,
operation attempted, expected and observed behavior, relevant response or other evidence, workaround,
and a realistic acceptance or regression scenario. Never include tokens, credentials, customer data,
private hosts, or identifying account details.

Submit reusable feedback to `https://github.com/VIDA-Global/vida-skill`. This includes skill
guidance and user-visible friction with the Vida API contract, generated reference, permissions, or
platform behavior encountered while following the skill. Describe observed public behavior and its
impact without speculating about private implementation details.

Search existing issues and pull requests before publishing. Use an issue when ownership, root cause,
or the correct fix is uncertain. Open a draft pull request only for a narrow, verified correction
with a realistic regression scenario. Do not create either automatically: obtain the user's
authorization for the external write and disclose that the report or change was agent-authored.
Link any resulting issue or pull request in the completion report. Findings that cannot be safely
reported in the public skill repository stay in the work log and are reported privately to the user;
do not publish them to another repository under this protocol.

## Error handling

- `401`: follow the selected transport's authentication recovery. For MCP, reconnect through the
  host's OAuth flow; for HTTP, verify the documented token query parameter without exposing it.
- `403` or scope error: re-read the authenticated account and verify target hierarchy and access.
- `404`: verify both the resource ID and selected account; do not broaden scope automatically.
- `409`: re-read current state and reconcile before retrying.
- `422` or validation error: compare the request with current OpenAPI and account-specific catalogs.
- `5xx`, timeout, or lost response after a write: query by returned or caller-owned correlation IDs
  before resubmitting.
- Asynchronous failure: inspect the terminal job, Task, run, linked conversation, and bounded logs
  before proposing remediation.
