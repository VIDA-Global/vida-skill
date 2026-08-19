---
name: vida-api
description: "Operational guide for Vida API usage only: auth, contacts, tasks, Computer Agent setup and operations, logs, and conversation details."
---

# Vida API Skill

Use this skill only for Vida API operations.

## Table of Contents

- [Source of Truth](#source-of-truth)
- [Authentication and Request Rules](#authentication-and-request-rules)
- [Input Validation Checklist](#input-validation-checklist)
- [Computer Agent setup and operations](#computer-agent-setup-and-operations)
- [Common Vida Workflows](#common-vida-workflows)
  - [Contacts](#2-manage-contacts-and-ongoing-contact-centric-work)
  - [Tasks](#4-create-update-or-cancel-tasks)
  - [Outbound calls, SMS, and email](#5-queue-outbound-calls-sms-and-email)
  - [Agent configuration, reporting fields, metrics, and experiments](#6-edit-and-publish-agents)
  - [Logs and conversations](#7-find-logs-for-troubleshooting-and-reporting)
- [Ready-to-use Request Templates](#ready-to-use-request-templates)
- [Response Contract](#response-contract)
- [Error Handling Rules](#error-handling-rules)

## Source of Truth

- OpenAPI (primary source): `https://vida.io/docs/apiv2.json`
- API base URL: environment variable `VIDA_API_BASE_URL`
- Skill source and updates: `https://github.com/VIDA-Global/vida-skill`
- Installed copies are Vida-managed. When maintaining this skill, update the source repository
  rather than editing a bundled copy.

If endpoint behavior is unclear, read the OpenAPI file first and follow it over assumptions.

Load the smallest relevant reference before configuration work:

- `references/voice-agent-configuration.md` for Agent settings, discovery catalogs, staging,
  publishing, versions, experiments, functions, apps, voices, and reporting fields
- `references/computer-agent-configuration.md` for durable Computer Agent behavior and the
  boundary between Agent configuration and operational Computer resources

## Authentication and Request Rules

- Auth is query param only: `token=<VIDA_API_KEY>`
- Token source: environment variable `VIDA_API_KEY`
- Always include `targetAccountId` when using an account-scoped API, except where the account ID is
  already part of the route path or the route explicitly uses another scope such as
  `targetOrganizationId`.
- Computer Agent account routes include `targetAccountId` in the URL path. For those routes, use
  `/api/v2/computer/accounts/{targetAccountId}/...` and the token query parameter; do not put a
  different account id in the query string or body.
- For Task creation and outbound call/SMS/email helpers, include query `targetAccountId` and body
  `accountId`, both set to the agent account that will perform the work.
- Do not include campaign/config override fields for normal task or email sending.
- For organization workflows, list child agent accounts with `GET /api/v2/listAccounts?targetOrganizationId=<orgAccountId>`, then use the selected agent account ID as `targetAccountId`.
- Prefer GET/read endpoints before mutation endpoints

Example URL shape:
`$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=123`

ID rules:

- `targetAccountId`: query parameter that scopes the API request to the Vida agent account.
- Organization account IDs contain child agent accounts; they are not the normal edit scope for a Computer Agent.
- `agentConfigId` identifies an Agent configuration record; do not use it as `targetAccountId`.
- `accountId`: body field that owns the created task and controls which agent account sends call/SMS/email tasks.
- For the current Computer Agent, `accountId` should normally equal `targetAccountId`.
- For configuration and version route paths, the path value named `agentConfigId` is an Agent
  configuration ID, not an account ID.

## Input Validation Checklist

Before mutation calls, validate:

- phone numbers are E.164 (`+15551234567`)
- unix-second timestamps for scheduling fields (`scheduledFor`, `start`, `end`)
- account scope (`targetAccountId`) and task owner (`accountId`) are correct
- required fields from OpenAPI are present

## Computer Agent setup and operations

Read `references/computer-agent-configuration.md` before setting durable Computer Agent behavior.
It identifies what belongs in Agent staging/publish and what belongs in the operational APIs below.

The authenticated Computer Agent API is rooted at:

`/api/v2/computer/accounts/{targetAccountId}`

Use it to provision, inspect, and operate Computer Agents without SSH.
Normal Vida agent configuration still belongs in the staging/publish flow under
`/api/v2/agentEventRules` and `/api/v2/agent`.

### Safe setup sequence

1. Resolve the exact child agent account with `GET /api/v2/listAccounts` or list provisioned
   Computer Agents with `GET /api/v2/computer/accounts`. Use the response's `accounts` array. If
   the requested child account does not exist, create one only after the user confirms the name and
   understands that account creation may affect billing or entitlements. Use
   `POST /api/v2/createAccount` with body
   `{"accountName":"..."}` and, when the API key is not already scoped to the organization,
   query `targetAccountId={organizationAccountId}`. Save the returned `account.id`.
2. Create or update the agent's staging configuration, publish it when approved, and verify the
   published configuration before provisioning. The child account ID is the `targetAccountId` for
   all of these steps.
3. Read `GET /api/v2/computer/accounts/{targetAccountId}/status`.
4. Provision only when no usable deployment exists. A provision/restart/upgrade response is
   asynchronous; poll status until the lifecycle job is terminal.
5. Verify `GET /api/v2/computer/accounts/{targetAccountId}/runtime/health` before runtime writes.
6. Use `GET /config` and its returned `revision` before changing Computer Agent settings. Apply the
   smallest structured change with `POST /config/patch`, then read the configuration again.
7. Use `GET /runtime/diagnostics` when health and logs do not explain a problem. Run
   `POST /runtime/repair` only with explicit user approval and poll status until the repair job is
   terminal.
8. Read each resource immediately before changing it, make the smallest change, and re-read it.
9. Verify capabilities from their actual surfaces: channel status, skill verification, Task run
   history, workspace reads, bounded runtime logs, or helper results.
10. Report the account id, endpoint, returned job/resource ids, and verification evidence.

Never claim an accepted lifecycle job, channel login start, cron-backed Task run request, backup, restore,
or skill verification job is complete until its status/result proves it.

### Lifecycle, runtime, and backups

Primary endpoints:

- `GET  /api/v2/computer/accounts`
- `GET  /api/v2/computer/accounts/{targetAccountId}/status`
- `POST /api/v2/computer/accounts/{targetAccountId}/provision`
- `POST /api/v2/computer/accounts/{targetAccountId}/restart`
- `POST /api/v2/computer/accounts/{targetAccountId}/upgrade`
- `POST /api/v2/computer/accounts/{targetAccountId}/deprovision`
- `GET  /api/v2/computer/accounts/{targetAccountId}/runtime/health`
- `GET  /api/v2/computer/accounts/{targetAccountId}/runtime/logs`
- `GET  /api/v2/computer/accounts/{targetAccountId}/runtime/service-logs`
- `GET  /api/v2/computer/accounts/{targetAccountId}/runtime/diagnostics`
- `POST /api/v2/computer/accounts/{targetAccountId}/runtime/repair`
- `GET  /api/v2/computer/accounts/{targetAccountId}/config`
- `GET  /api/v2/computer/accounts/{targetAccountId}/config/schema`
- `POST /api/v2/computer/accounts/{targetAccountId}/config/patch`
- `GET  /api/v2/computer/accounts/{targetAccountId}/backups`
- `POST /api/v2/computer/accounts/{targetAccountId}/backup`
- `GET  /api/v2/computer/accounts/{targetAccountId}/backup-jobs/{jobId}`
- `POST /api/v2/computer/accounts/{targetAccountId}/restore`
- `GET  /api/v2/computer/accounts/{targetAccountId}/restore-jobs/{jobId}`

Use `/runtime/logs` with non-negative `cursor`, `limit` from 1..5000, and `maxBytes` from 1..1000000;
page with the returned cursor. For recent service-startup diagnostics, use `/runtime/service-logs`
with `tail` (1..1000, default 200) and optional `sinceSeconds` (0..604800). Use backups before
destructive lifecycle work. A normal deprovision preserves saved state; body `{"wipeState":true}`
permanently removes it and requires explicit user intent. Restore accepts optional `snapshotId` and
`delete`; it stops the Computer Agent while restoring, then starts it again. Confirm the snapshot,
poll the restore job, and verify both account status and health.

The configuration read returns complete redacted `authoredConfig` and `effectiveConfig` objects,
the `revision` required for the next update, and the agent ids included on the same computer. Omit
redacted settings from a patch unless the user explicitly intends to replace them. A configuration
patch uses `{revision, patch}` and may include `replacePaths` only when replacing an array is
intentional. Full raw replacement is not part of the customer API.

Diagnostics are read-only and return stable finding codes, severity, and affected paths. Repair
accepts only `{"confirm":true}`. It is a bounded lifecycle operation; it does not provide arbitrary
commands or repair flags. Poll `/status`, then rerun diagnostics and verify the affected capability.

For durable heartbeat behavior, update `heartbeatInstructions`, `heartbeatEvery`, and any advanced
`heartbeatConfig` through agent staging, publish, and verify the live/default config. The advanced
object replaces the prior advanced override set: start from the current object and preserve keys you
do not intend to change, omit it to preserve staging, or send `{}` to clear all advanced overrides.
An `activeHours` value must contain `start` and `end` in 24-hour `HH:MM` format and may include
`timezone` set to `user`, `local`, or an IANA timezone. Supported advanced keys are `activeHours`,
`model`, `session`, `target`, `to`, `accountId`, `directPolicy`, `includeReasoning`,
`includeSystemPromptSection`, `ackMaxChars`, `suppressToolErrorWarnings`, `timeoutSeconds`,
`lightContext`, `isolatedSession`, and `skipWhenBusy`; use OpenAPI for their exact types.
Set `suppressToolErrorWarnings: true` for customer-facing heartbeat destinations when automatic raw
failure notices should remain private. This does not suppress a deliberate final alert from the
agent; heartbeat instructions should require a concise final alert when an unrecovered failure
materially blocks a due check, and `HEARTBEAT_OK` when the check succeeds or recovers.
`heartbeatEvery` remains the cadence and `heartbeatInstructions` remains HEARTBEAT.md content.
Use `POST /prompts/sync` to restore the published instructions when they have drifted, and inspect
every returned per-agent failure. `POST /session/resolve` returns the
Vida room for an authorized session; an explicit sessionKey must belong to the selected agent.

### Workspace files, helpers, and browser automation

Use the workspace endpoints for customer-authored project files, skill files, data, and automation
artifacts. Vida-managed root configuration files are not workspace content: they do not appear in
workspace discovery and workspace operations reject them. Change instructions, heartbeat behavior,
and other durable agent configuration through the agent staging and publish flow instead.

Read and discovery:

- `POST /workspace/read` with a workspace-relative file `path`
- `POST /workspace/list` with an optional workspace-relative directory `path` and optional `limit`;
  omit `path` to list the workspace root
- `POST /workspace/find` with a name `pattern`, optional workspace-relative `path`, and optional
  `limit`; omit `path` to find matching files and folders across the workspace
- `POST /workspace/search` with required `path` and plain-text `pattern`; optional `glob`,
  `ignoreCase`, `context` (0..5), and `limit` (1..200)
- `GET  /helpers`

Text mutations:

- `POST /workspace/write` with `path` and complete text `content`
- `POST /workspace/edit` with `path`, exact `oldText`, and replacement `newText`; only the first
  exact match is replaced, and an empty `newText` removes that match

Preview, download, upload, and delete use the same workspace path model:

- `GET  /workspace/preview?path=...`
- `GET  /workspace/download?path=...`
- `POST /workspace/upload` as multipart with `path`, a file, and optional `overwrite=true`
- `DELETE /workspace/delete?path=...` with the workspace-relative path URL-encoded in the query

All paths above are relative to the selected agent workspace. Read/list first and verify afterward.
Uploads protect existing files unless `overwrite=true` is explicit. Directories must be empty, so
remove their contents explicitly before deleting them. Workspace operations block Vida-managed
configuration and internal/system roots.

Reusable helper endpoints:

- `GET  /helpers`
- `POST /helpers/execute` with an exact registered `name` and optional object `arguments`

Helpers are reusable Computer Agent functions. A helper may use Browser access or may run without a
browser for API, file, or data work. Treat the helper listing as the callable contract: it includes
the argument schema, `requiresBrowser`, owning `skillSlug`, and IDs of any `requiredSecrets`. Never
send secret values to `/helpers/execute`; Vida resolves only the declared IDs from the selected
Agent's managed secrets, using an organization value only as an inherited fallback.

Reusable source belongs with its skill under `skills/{skillSlug}/helpers/*.py`. Use
`@browser_function(...)` for Browser-backed helpers and include a stable `start_url`. Use
`@computer_function(...)` for helpers that do not need Browser access. Declare credentials as
`required_secrets=["secret/id"]` and read them at invocation time with
`from vida_helper_runtime import managed_secret`; do not accept credentials as helper arguments,
read arbitrary environment variables, or persist values in code. The runtime generates
`helper-workspace/helpers.json`; older Agents may still use the legacy Browser workspace and registry
names. Do not edit generated registries or move a legacy workspace by hand.

Installing, updating, or uninstalling a skill refreshes its registered helpers. Browser recording
generation also refreshes the registry. After either workflow, re-read `/helpers` and execute a
safe representative call. Helper execution is synchronous; an `ok` transport response is not a
substitute for checking the returned helper status and business result.

Browser automation endpoints:

- `POST /browser/ticket` for short-lived interactive access; open the returned `launchRef.href`
- `POST /browser/automation-sessions` with optional `ttlSeconds` from 60..1800
- `GET  /workflow-recordings/status`
- `POST /workflow-recordings/start` with the automation session's `slot` as `slotId`
- `POST /workflow-recordings/stop`
- `POST /workflow-recordings/{domainKey}/generate` with optional `skillName`
- `POST /workflow-recordings/{domainKey}/{recordingId}/delete`

Use a browser automation session when the task needs direct browser control or a new reusable
helper. Its response contains `cdpUrl`, a `headers` object, `slot`, and `expiresAt`. Request
`{cdpUrl}/json/version` with the returned header, then connect browser tooling to that response's
`webSocketDebuggerUrl` before the session expires.

Use a browser ticket when a person needs to interact with the Computer Agent's browser, such as to
sign in to a website. The ticket response includes a short-lived `launchRef`; give that link to the
user or open it in a browser without constructing another URL. A ticket grants temporary browser
access, so create it only for the intended recipient and do not reuse it after the flow ends.

To create a reusable helper:

1. Read recording status; do not start while another recording or generation is active.
2. Start recording with the session's exact `slot` as `slotId`.
3. Perform the workflow through the returned CDP connection.
4. Stop recording and retain its returned `domainKey` and `recordingId`.
5. Start generation for that domain and poll recording status until generation is terminal. When
   the domain contains customer-specific information or would make a poor reusable name, supply a
   neutral `skillName`; save the returned `skillSlug` for reporting and reset verification.
6. Use the generation's `conversationRef.resolve` request to find its Vida chat while work is in
   progress; the resolution response's `chatRef` points to the replicated messages and tool calls.
7. Re-read `/helpers`, then execute the registered helper with representative
   arguments and verify the result.

Only execute helpers returned by the helper listing or otherwise known to be registered.
Delete a recording only when the user intends to discard it; do not reset a generated domain merely
to retry a failed run.

### Skills, authentication, and managed secrets

Use this skill lifecycle:

1. Read `GET /skills/catalog`, the selected `GET /skills/catalog/{skillSlug}`, and
   `GET /skills/state`. Use the catalog's exact `skillSlug` and installation choices.
2. Install with `POST /skills/install` body `{"skillSlug":"..."}`. Include `installId` only when
   the detail lists more than one installation option. The optional `timeoutMs` is 1000..300000.
3. Verify immediately with `POST /skills/{skillSlug}/verify`. Prefer synchronous verification. If
   body `{"async":true}` returns `202`, poll the catalog detail's `verificationJob` until it is
   `completed` or `failed`, then verify synchronously to obtain the current result.
4. Treat `verification.result.requiredActions` as the authoritative setup plan. Process pending
   actions by ascending `order` and do not start an action until every ID in `dependsOn` is complete.
5. For `enter_value` and `select_option`, first read
   `GET /skills/{skillSlug}/setup-values?storageKey=...`. Save non-sensitive editable values with
   `POST /skills/{skillSlug}/setup-state` body `{"storageKey":"...","value":...}`. For a sensitive
   value, use the Computer Agent secret endpoint indicated by its `storageKey`; never place a secret
   in setup-state, workspace files, logs, or chat.
6. For `upload_file`, upload the requested file to the exact declared workspace path and verify it.
   For `oauth` or `device_code`, start `POST /skills/{skillSlug}/auth/{actionId}/start`, present any
   returned `browserNavigateUrl` or `capturedDeviceCode` to the user, and poll the matching `GET`
   until `succeeded`, `failed`, or `cancelled`. Use cancel only to stop an active attempt.
7. For `manual_confirmation`, ask the user to complete or confirm the described external step. Do
   not mark it complete based on an assumption.
8. Verify again after every setup or authentication change. Finish only when verification reports
   `setupComplete:true` and the catalog detail reports the skill ready. Re-read `/skills/state` as
   final evidence. Disable or uninstall only with explicit intent.

Additional endpoints:

- `POST /skills/{skillSlug}/disable`
- `POST /skills/{skillSlug}/uninstall`
- `GET|POST /secrets`
- `POST /secrets/check`, `/secrets/reapply`, and `/secrets/delete`

Managed-secret list/check responses confirm whether a value is configured. Check deployment after
create/update; use reapply for drift. Deleting a secret can disable a skill or connection, so inspect dependencies first.
Restricted runtime tokens cannot use managed-secret CRUD.

### Channels

Primary endpoints:

- `GET  /channels/catalog`
- `GET  /channels/status` with optional `probe=true`
- `POST /channels/configure`
- `POST /channels/logout`
- `POST /channels/web-login/start`
- `POST /channels/web-login/wait`

Read the catalog and status before changing a channel. Configure with the catalog's `connection` and
`access` fields plus `enabled`; Vida assigns the connection and inbound routing to the selected
`targetAccountId`. Do not supply a separate channel account or raw channel configuration. A web-login
start accepts optional `accountId`, `force`, `verbose`, and `timeoutMs` (1000..120000); wait accepts
optional `accountId` and `timeoutMs` (1000..180000). Starting is not proof of a working connection;
wait for the flow and then probe status. Use `force` only to replace a stuck login. Logout disconnects
the selected Computer Agent's channel session.

### Agent schedules as Tasks

Repeating and one-off Computer Agent schedules use the standard Tasks resource:

- `GET|POST /api/v2/tasks`
- `GET|POST|DELETE /api/v2/tasks/{taskId}`
- `POST /api/v2/tasks/{taskId}/run`
- `GET /api/v2/tasks/{taskId}/runs`

Creation requires query `targetAccountId` and body `accountId` set to the same executing agent.
Include `targetAccountId` on every Task read, update, delete, run, and run-history request. Use `type:repeating` with
`cronSchedule.kind` `cron` or `every`, and `type:cronOneOff` with kind `at`. Creation also requires a
nonblank `title` and `taskContext`. Cron expressions use five-field minute precision; `everyMs` must be
at least 60000. A Task is active by default. Set `state:"paused"` explicitly when it must not run
before verification, then enable it with `POST /api/v2/tasks/{taskId}` body `{"state":"active"}`.

Cron-backed Task updates accept only `title`, `taskContext`, `state` (`active` or `paused`), and
`cronSchedule`. Delete removes the schedule. Run-now defaults to `mode=force`; use
`mode=due` only for due-only behavior. A `202` run response proves enqueue/acceptance, not completion;
verify with `/runs`. `/logs` is communication history, not cron run history. Task ids outside the
selected account scope return not found. Vida verifies ownership and blocks unsafe imported schedules
before updates, deletion, or manual runs.

### Memory, sessions, conversations, tools, and policy

Use `/memory/explorer` to inspect managed memory. Create/update/delete routes under
`/memory` are appropriate for compact durable facts, including deliberate manual migration; do not
store credentials, transcripts, or large artifacts. A memory update accepts at least one of `text`,
`category`, or `importance`; category is `preference`, `fact`, `decision`, `entity`, or `other`, and
importance is 0..1. Memory delete is permanent.

Use `GET /api/v2/computer/sessions` to list requester-authorized managed sessions and
`POST /api/v2/computer/sessions/reset` with required `sessionKey` and optional `reason` only when
conversational context should be discarded. `POST /session/resolve` accepts an optional `sessionKey`
and otherwise resolves the selected agent's direct session. Use the returned room identifiers with
`GET /api/v2/messages/{roomId}` or the returned conversation reference to inspect the replicated
messages, tool calls, and results.

Use `GET /tools/catalog` before `POST /tools/policy` or `/tools/invoke`. Prefer purpose-built routes.
Invoke a catalogued tool only when a purpose-built route does not cover the requested action. Keep
the request narrowly scoped and verify the resulting state. Tool invocation requires `tool` and may
include object `args`, `action`, `dryRun`, and `sessionKey`.

## Common Vida Workflows

### 1) Auth and scope sanity check

Use a simple read call first:

- `GET /api/v2/account`
- Then run one scoped read using `targetAccountId` (for example `GET /api/v2/tasks`)

If the scoped read fails, do not continue with writes.

### 2) Manage Contacts and ongoing contact-centric work

Use Contacts for objectives centered on people, such as outreach, follow-up,
renewals, appointment preparation, collections, recruiting, and customer
success. Do not force inventory, documents, invoices, tickets, or other
non-contact records into Contacts.

Primary endpoints:

- `GET /api/v2/contact`
- `GET /api/v2/contact/{contactId}`
- `POST /api/v2/contact`
- `PATCH /api/v2/contact/{contactId}`
- `DELETE /api/v2/contact`
- `GET /api/v2/contact/list`
- `GET|POST|DELETE /api/v2/contact/list/{listName}`
- `PATCH|DELETE /api/v2/contact/{contactId}/list/{listName}/state`
- `GET /api/v2/contact/{contactId}/logs`

#### Finding Contacts

`GET /api/v2/contact` performs server-side filtering and pagination.

Supported filters include:

- `q`: search name, phone, or email
- exact `id`, `phone`, `email`, `status`, `source`, or `leadSource`
- `list`: Contact List membership
- `customFieldPath` with `customFieldValue`
- `page`, `pageSize`, `sort`, and `order`

Use the returned pagination metadata. Do not assume the first page contains
every matching Contact.

#### Ongoing objectives

A Contact List identifies the contacts managed by an objective. Use one
concise, stable list name for that objective. Before establishing a new one,
read existing lists and reuse an exact match rather than creating a synonymous
label. Prefer lowercase kebab-case for new objective names.

The same list name is used by the API as the matching key in each Contact's
`customFields`.

Use this endpoint to enroll a Contact and merge its current objective state:

`PATCH /api/v2/contact/{contactId}/list/{listName}/state`

The request body is the state to merge. The API ensures list membership,
preserves unrelated Contact fields and objective state, and returns the
persisted Contact. Do not invent a separate custom-field key.

Example:

```json
{
  "state": "waiting",
  "nextAction": {
    "type": "call",
    "notBefore": 1784600000
  },
  "lastActionAt": 1784000000,
  "lastOutcome": "no_answer",
  "data": {
    "attemptCount": 1
  }
}
```

These names are recommended vocabulary, not a universal state machine. Use
only what the objective needs and keep established values consistent.

Tasks represent concrete work supported by Vida Tasks. Record `nextAction`
when work remains even if it cannot be represented by a Task. Skills, user
instructions, and cron jobs define business rules and execution timing.

To continue an objective:

1. Load Contacts from its list.
2. Read each Contact's matching state.
3. Read relevant pending Tasks and recent Contact logs.
4. Consult the source application when current source data affects the decision.
5. Respect `nextAction.notBefore` unless new information requires reevaluation.
6. Perform and verify the action.
7. Patch the outcome and next action.
8. Verify the persisted Contact before reporting success.

Do not mark work completed merely because it was attempted or queued.

Use `DELETE /api/v2/contact/{contactId}/list/{listName}/state` only when the
Contact should leave the objective. Waiting, paused, cooling-down, and blocked
Contacts should remain enrolled and express that condition in state.

#### Communication history

Use `GET /api/v2/contact/{contactId}/logs` to inspect recent inbound and
outbound communication. It supports `page`, `pageSize`, `start`, `end`,
`type`, `eventType`, and `direction`.

When a log includes `conversationRef`, use its `href` or returned `roomId` and
`uuid` with the conversation API for full details. Do not treat a queued Task
as proof that communication occurred.

#### System-maintained lists

Vida maintains these communication activity indexes:

- `recent`
- `recentlyCalled`
- `recentlyMessaged`
- `recentlySentEmail`

Agents may query them but must not manually maintain them, use them as
objective state keys, or treat membership as proof of an outcome.

Do not depend on legacy `recentlyScheduled`, `recentlySentSms`,
`recentlySentWebhook`, `recentlySentWebhook-*`, or
`recentlySentPaymentRequest` labels.

#### Storage rules

Contact state stores compact facts needed for the next decision. Do not store
transcripts, complete communication history, full API responses, copied source
records, credentials, cookies, or large generated summaries. Keep the complete
`customFields` object within its documented 8 KB limit.

### 3) Query communication and scheduled tasks

Primary endpoints:

- `GET /api/v2/tasks`
- `GET /api/v2/tasks/{taskId}`
- `GET /api/v2/tasks/{taskId}/logs`
- `GET /api/v2/tasks/stats`
- `GET /api/v2/tasks/batches/{batchId}`
- `GET /api/v2/tasks/limits`

Useful query params on list:

- `limit`, `offset`
- `since`, `until` (unix seconds)
- `sort` (`createdAt`, `updatedAt`, `scheduledFor`)
- `order` (`asc`, `desc`)
- exact `id`, `type`, `state`, `contactId`, `accountId`, `batchId`,
  `externalTaskId`, or `contactListName`
- nested metadata such as `meta.source` or `meta.crm.leadId`
- `outcome`: `goal_met`, `terminal_negative`, `goal_incomplete`, or
  `retries_exhausted`

Task types commonly used: `call`, `text`, `email`, `ping`, `computer`,
`repeating`, and `cronOneOff`.

One retry-enabled Task represents one logical goal and all attempts toward it.
Read `attemptHistory`, `result`, `logsRef`, and `conversationRef` from the Task
instead of treating each attempt as a separate Task.

Public communication Task states are `pending`, `processing`, `running`,
`finished`, `errored`, and `canceled`; cron-backed Tasks also use `active` and
`paused`. A queued or accepted Task is not proof that an
attempt occurred; inspect its current state and attempt history.

### 4) Create, update, or cancel tasks

- Create: `POST /api/v2/tasks`
- Create a batch: `POST /api/v2/tasks/batches`
- Update: `POST /api/v2/tasks/{taskId}`
- Cancel pending Tasks: `POST /api/v2/tasks/cancel`
- Delete: `DELETE /api/v2/tasks/{taskId}`

Typical create fields:

- `type`
- `target` (required for call/text/email)
- `context`
- `message` (text/email body when using generic tasks)
- `greeting`
- `waitToGreet`
- `scheduledFor`
- `externalTaskId`
- `goal`
- `retryPolicy`
- `meta`
- `meta.email.subject` (email subject when `type` is `email`)
- `meta.email.attachments` (SendGrid-style attachment objects with base64 `content`)

#### Computer Tasks

Use `type:"computer"` for one piece of work that a provisioned Computer Agent
should complete now or at `scheduledFor`. Create it one at a time with:

- `accountId`: the provisioned Computer Agent that will do the work
- `taskContext`: complete, actionable instructions
- optional `title`, `scheduledFor`, `externalTaskId`, and reporting `meta`

Do not include a communication target, retry policy, Contact context, schedule,
or session fields. Vida creates a dedicated chat for the work and returns its
`roomId` and `chatRef` on the Task once execution starts. Read the Task until it
reaches `finished` or `errored`, then follow `chatRef.href` or read
`GET /api/v2/messages/{roomId}` for the complete linked chat.

After creation, a Computer Task can only be canceled with
`POST /api/v2/tasks/{taskId}?targetAccountId={accountId}` and body
`{"state":"canceled"}`. Cancellation stops active work. Delete any Computer
Task with `DELETE /api/v2/tasks/{taskId}?targetAccountId={accountId}`; deletion
also stops active work before removing the Task.

#### Goals and retries

Use one retry-enabled Task when several attempts pursue the same outcome. Do
not create one Task per attempt or schedule duplicate follow-up Tasks yourself.

- `goal.completionCriteria` tells Vida how to evaluate a connected
  conversation. Make it specific enough to distinguish success, an explicit
  negative response, and an inconclusive conversation.
- `retryPolicy.delaysSeconds` schedules same-channel retries after resolved
  attempts. Each delay is 60 seconds through 30 days; the cumulative cadence
  must remain within 90 days.
- `retryPolicy.steps` schedules channel-specific attempts at increasing offsets
  from the first attempt. Each step requires `offsetSeconds` and `channel`, and
  may include `target`, `responseTimeoutSeconds`, and channel-specific
  `content`. A target is required when switching between phone and email. Use
  either `delaysSeconds` or `steps`, never both.
- `retryPolicy.retryOn` selects retryable dispositions. `goal_incomplete`
  requires `goal.completionCriteria`.
- `retryPolicy.responseTimeoutSeconds` controls how long text or email attempts
  wait for a response.
- `goal_met` and `terminal_negative` always stop the cadence. Retry policies
  support up to 10 retries within a 90-day horizon.

Valid `retryOn` values are `busy`, `delivery_failed`, `goal_incomplete`,
`no_answer`, `no_response`, `no_speech`, `rejected`, `transient_failure`, and
`voicemail`. Include only outcomes the workflow should actually retry.

For step `content`, call supports `context`, `taskContext`, `greeting`, and
`waitToGreet`; text supports `message`; email supports `subject`, `message`,
`cc`, and `bcc`. Step offsets must be strictly increasing. Text/email response
timeouts may be 60 seconds through 7 days.

Before creating Tasks, read `GET /api/v2/tasks/limits`. For call, text, and
email Tasks, an omitted or `null` `goal` or `retryPolicy` independently inherits
that component from `defaultRetryConfiguration` when configured. Explicit
values replace the corresponding default; they are not field-merged. Supply
both fields explicitly when a workflow requires an exact goal and cadence.

Use `context` and `taskContext` for information the agent needs while doing the
work. `meta` is retained for filtering and reporting but is not added to the
agent prompt.

`externalTaskId` is reusable correlation/grouping data, not an idempotency key.
Do not rely on it to prevent duplicate Tasks.

`meta.cron` and `externalTaskId` values beginning with `cron:job:` are reserved
for server-managed Computer Agent schedule projections. Create and manage schedules
with `type`, `cronSchedule`, and the Task routes instead of manufacturing or
rewriting those reserved fields.

#### Recurring and batch work

Before submitting work from a recurring source:

1. Query existing Tasks using stable source metadata, `externalTaskId`, or
   another exact correlation field.
2. Skip targets with an active Task (`pending`, `processing`, or `running`) and
   apply the workflow's rules to prior terminal outcomes.
3. Submit all remaining eligible targets in one explicit `tasks` array to
   `POST /api/v2/tasks/batches`.
4. Save the returned `batchId` and verify rejected or skipped items before
   reporting success.

The batch endpoint accepts up to 10,000 Tasks. Submissions over 1,000 require
an `Idempotency-Key` header and are created asynchronously. The API also
rejects overlapping active retry-enabled Tasks for the same agent and
normalized phone or email target; this is a safety boundary, not a substitute
for reconciliation.

For an asynchronous `202` response, poll
`GET /api/v2/tasks/batches/{batchId}` until it reaches `completed`,
`completed_with_errors`, `failed`, or `canceled`. Inspect `inserted`, `rejected`,
and `errors`; do not equate acceptance with successful Task creation.

After a timeout, `409`, or `5xx` from any batch submission, query Tasks by the
submitted correlation fields before retrying the request. A failed synchronous
request may have created earlier rows in the batch, while repeating an
asynchronous request is safe only when the same `Idempotency-Key` and payload
are reused.

Communication Task processing respects configured business hours, daily limits, per-target
cooldowns, call concurrency, and calls-per-second limits. These may leave an
accepted Task pending until it is eligible. An initial `scheduledFor` outside
configured business hours is rejected rather than silently moved.

Retry-enabled Tasks are immutable after creation except for cancellation.
Cancellation does not interrupt an attempt already in flight, and retry Task
history is retained rather than deleted. Re-read the Task before follow-up or
handoff actions because a late text, email, or correlated inbound response can
change its terminal outcome.

Email task notes:

- Outbound email is available only when the sending agent account has email enabled.
- Email `message` content may contain basic HTML.
- Attachments must be provided as SendGrid-compatible objects, for example `{ "filename": "report.pdf", "type": "application/pdf", "content": "BASE64_CONTENT", "disposition": "attachment" }`.

### Inbound Email Received Workflow

When you receive a Vida event with `event: "email.received"`:

1. Do not web search for Vida API shape. Use this skill.
2. Read `roomId`, `messageUuid`, `messageTimestamp`, `targetAccountId`, `from`, and `subject` from the event payload.
3. Fetch the room once:
   `GET /api/v2/messages/{roomId}?token=$VIDA_API_KEY&targetAccountId={targetAccountId}`
4. Select the message with `uuid === messageUuid`. If `messageUuid` is missing, use the latest message in the room where `source === "email"` and `from` is not the agent account.
5. Inspect the selected message:
   - `message` / `summary` for text preview
   - `metadata.emailSubject` for subject
   - `metadata.emailFrom`, `metadata.emailTo`, and `metadata.emailCc` for visible participants
   - `metadata.emailMessageId`, `metadata.emailInReplyTo`, and `metadata.emailReferences` for email thread headers
   - `metadata.emailHtml` for full HTML email attachment
   - `attachments` for files
6. To fetch attachments:
   - Prefer `attachments[].content-url`.
   - Build the URL as `$VIDA_API_BASE_URL + attachments[i]["content-url"]`.
   - Example: `$VIDA_API_BASE_URL/api/v1/chat/media/d4a717bd-fd3b-40b4-a961-822bac90fe61.png/Org%20Chart.png`
   - URL-encode spaces and special characters in the filename path segment when using curl/fetch.
   - Do not use `attachments[].location` or `attachments[].cdn-url` as the primary fetch URL; those may be protected S3/CDN locations and can fail from the Computer Agent runtime.
   - Use `content-type` and `filename` to decide how to inspect the file after downloading it.
7. Decide whether to reply based on the email content and your instructions.
8. If replying, use `/api/v2/agent/outboundEmail` with `roomId` and `replyToMessageUuid` from the selected email message. Body `accountId` must equal the event `targetAccountId`.

Inbound email fetch example:

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/messages/$ROOM_ID?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID"
```

Attachment fetch example:

```bash
curl -L "$VIDA_API_BASE_URL/api/v1/chat/media/d4a717bd-fd3b-40b4-a961-822bac90fe61.png/Org%20Chart.png" -o "Org Chart.png"
```

Email reply example:

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/agent/outboundEmail?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "accountId": $TARGET_ACCOUNT_ID,
  "roomId": "$ROOM_ID",
  "replyToMessageUuid": "$MESSAGE_UUID",
  "content": "<p>Your reply here.</p>"
}
EOF
```

For one email to multiple recipients, use `to`, `cc`, and `bcc`. Do not use `targets[]` unless you intentionally want separate email tasks/messages.

### 5) Queue outbound calls, SMS, and email

These endpoints create tasks:

- `POST /api/v2/agent/outboundCall`
- `POST /api/v2/agent/outboundSms`
- `POST /api/v2/agent/outboundEmail`

Common fields:

- `accountId` (set to the same Vida agent account id as `targetAccountId`)
- `target` or `targets`
- `content` (SMS required)
- `subject` (email required)
- `attachments` (email optional, SendGrid-style base64 attachment objects)
- `context` / `taskContext`
- `scheduledFor`
- `scheduleSpacingSec` (for batch staggering)

### 6) Edit and publish agents

Read `references/voice-agent-configuration.md` before editing an Agent. It is the complete workflow
for current configuration fields, dynamic catalogs, versions, experiments, functions, apps, voice,
language, and source-attributed reporting fields.

Agent writes are staging-first. Read staging, discover dynamic choices, change only intended
writable settings, re-read staging, test, publish only with explicit intent, and verify live. Never
use an `agentConfigId` as account scope. Treat response-only function eligibility, active slots,
and effective reporting fields as read-only annotations.

#### Dashboard metrics

Organization dashboard metrics are stored in the organization account's
`settings.metrics` array. They query logs through
`POST /api/v2/logs/timeSeries`. Retry-enabled Task attempts are represented in
those logs, including attempts that did not produce a conversation.

Use this flow:

1. Read the organization with `GET /api/v2/account?targetAccountId=<orgId>`.
2. Preserve every existing metric not owned by the requested change. If the
   stored metric array is empty, remember that the frontend may currently be
   showing built-in defaults; the first custom save must retain any default
   cards the user still expects.
3. Validate each proposed definition with `POST /api/v2/logs/timeSeries`.
4. Upsert metrics by stable `name`; do not append duplicate definitions.
5. Save with `POST /api/v2/account?targetAccountId=<orgId>` and body
   `{"settings":{"metrics":[...]}}`. The v2 account route merges settings and
   replaces the supplied metrics array.
6. Re-read the account and verify the stored names and definitions.

A stored metric includes `name`, `title`, `filters`, `formula`, `fieldTypes`,
`aggregation`, `scale`, `format`, `precision`, and `dateFilter`.

For a boolean reporting-field rate, filter the field with `isset`, use the
field as the formula, aggregate with `avg`, and scale by 100. Its denominator
is only conversations where the field is non-null. For a choice count, filter
the field with `eq`, use formula `1`, and aggregate with `count`.

Task-attempt metrics must filter `taskAttemptId` with `isset`. Do not also
require a transcript or reporting field when attempts without a conversation
belong in the denominator. For contact rate, average a boolean formula that
maps the workflow's live-contact dispositions to true over all applicable
attempt logs; missing values then count as false. Keep this separate from an
acceptance rate whose denominator is only contacts that made a decision.

Every final retry attempt has one `task_goal` outcome with `terminal: true`,
including retry exhaustion. To limit a metric to one final attempt per Task,
store this filter:

```json
{
  "outcome": {
    "op": "eq",
    "value": "{\"type\":\"task_goal\",\"terminal\":true}||json"
  }
}
```

Use that terminal-attempt denominator for overall workflow yield. Validate the
definition against live log data before saving it; do not substitute
answered-conversation counts for Task-attempt counts.

Saved versions and experiments use the live `agentConfigId`, not the account ID. Create candidate
versions before an experiment, preserve assignments across retries, keep reporting definitions
consistent across variants, and report sample size and denominator. The reference contains the full
route and lifecycle contract.

### 7) Find logs for troubleshooting and reporting

Endpoint:

- `GET /api/v2/logs`

Important query params:

- `start`, `end` (Unix seconds; default is the complete authorized history through now, so specify a
  bounded range for routine analysis)
- `fields` (comma-separated)
- `pageSize` (max 10000), `page`
- `includeFields` (returns schema)
- `format=json|csv`
- `targetAccountId`
- additional log-field query params are filters; append operators such as `__gte`, `__in`,
  `__icontains`, or `__isnull` as documented in OpenAPI

Use `format=csv` for exports and large analysis pulls. Use
`POST /api/v2/logs/timeSeries` for aggregate, time-bucketed, organization, or agent metrics; send
its required `targetAccountId` in the JSON body with the metric definition and bounded time range.

### 8) Access conversation and message details

Primary endpoints:

- `GET /api/v2/conversations`
- `GET /api/v2/junkConversations`
- `GET /api/v2/messages/recent`
- `GET /api/v2/messages/{roomId}`
- `GET /api/v2/conversation/{roomId}/{uuid}`

For full conversation detail, use the `roomId` and `uuid` returned by a log entry with
`GET /api/v2/conversation/{roomId}/{uuid}`. Use `POST /api/v2/conversation/batch` for up to 200
lookups at once.

### 9) Build audit-ready incident packets

Use this workflow when troubleshooting customer-impacting events:

1. Query logs in the incident window using `GET /api/v2/logs`
2. Extract `roomId` and `uuid` identifiers from relevant log rows
3. Expand transcripts with:
   - `GET /api/v2/conversation/{roomId}/{uuid}` for one item, or
   - `POST /api/v2/conversation/batch` for multiple items
4. Return an incident packet with:
   - timeline
   - affected scope (`targetAccountId`, `accountId` when creating tasks)
   - artifact refs (`roomId`, `uuid`, `taskId`)
   - recommended remediations

### 10) Run operating health checks

For recurring business operations checks:

- Inbox pressure: `/api/v2/messages/recent`
- Task health: `/api/v2/tasks/stats`, `/api/v2/tasks/dailyCounts`, `/api/v2/tasks/limits`
- Usage/cost posture: `/api/v2/stats/usage`
- Reporting detail: `/api/v2/logs`

Use read-first checks before proposing mutations.

## Ready-to-use Request Templates

Use these templates and adjust placeholders.

### Create a child agent account

Only run this after the user confirms the new account name and any billing or entitlement impact.
Use the organization account ID in the query, then save the returned `account.id` as the new
`TARGET_ACCOUNT_ID`.

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/createAccount?token=$VIDA_API_KEY&targetAccountId=$ORGANIZATION_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "accountName": "$NEW_AGENT_ACCOUNT_NAME"
}
EOF
```

### Inspect a Computer Agent before mutation

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/status?token=$VIDA_API_KEY"
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/runtime/health?token=$VIDA_API_KEY&probe=true"
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/config?token=$VIDA_API_KEY"
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/runtime/diagnostics?token=$VIDA_API_KEY"
```

### Update Computer Agent settings

Read the configuration first and copy its `revision`. Omit redacted settings unless the user
explicitly intends to replace them.

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/config/patch?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "revision": "$CONFIG_REVISION",
  "patch": {
    "agents": {
      "list": [
        {
          "id": "$TARGET_ACCOUNT_ID",
          "heartbeat": { "every": "30m" }
        }
      ]
    }
  }
}
EOF
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/config?token=$VIDA_API_KEY"
```

### Run an approved Computer Agent repair

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/runtime/repair?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  --data '{"confirm":true}'
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/status?token=$VIDA_API_KEY"
```

### Read and verify a workspace file

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/workspace/read?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "path": "projects/customer-runbook/README.md"
}
EOF
```

### Upload a workspace file without accidental overwrite

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/workspace/upload?token=$VIDA_API_KEY" \
  -F "path=reference/customer-runbook.pdf" \
  -F "file=@customer-runbook.pdf"
```

If replacement is explicitly intended, first inspect the current destination and then add
`-F "overwrite=true"`. Read or preview the destination afterward.

### Open short-lived interactive browser access

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/browser/ticket?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  -d '{}'
```

Open or share the returned `launchRef.href` before its `expiresAtMs`. Do not construct the launch
route manually or reuse an expired ticket.

### Read and configure a Computer Agent channel

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/channels/catalog?token=$VIDA_API_KEY"
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/channels/configure?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "channel": "slack",
  "connection": {
    "mode": "socket",
    "botToken": "$SLACK_BOT_TOKEN",
    "appToken": "$SLACK_APP_TOKEN"
  },
  "access": {
    "dmPolicy": "disabled",
    "groupPolicy": "allowlist",
    "targets": ["$SLACK_CHANNEL_ID"],
    "requireMention": true
  },
  "enabled": true
}
EOF
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/channels/status?token=$VIDA_API_KEY&probe=true"
```

The selected `TARGET_ACCOUNT_ID` owns the connection and receives its inbound traffic. Do not add
an `accountId` to the request body.

### Check an existing skill setup value

```bash
curl -sG "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/skills/$SKILL_SLUG/setup-values" \
  --data-urlencode "token=$VIDA_API_KEY" \
  --data-urlencode "storageKey=$STORAGE_KEY"
```

Reuse `currentValue` only when `valueVisibility` is `plaintext`. For redacted values, `hasValue:true`
means the value is already configured even though its contents are not returned.

### Install and discover a skill's setup plan

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/skills/catalog/$SKILL_SLUG?token=$VIDA_API_KEY"
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/skills/install?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "skillSlug": "$SKILL_SLUG"
}
EOF
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/computer/accounts/$TARGET_ACCOUNT_ID/skills/$SKILL_SLUG/verify?token=$VIDA_API_KEY" \
  -H "content-type: application/json" \
  -d '{}'
```

Use the verification response's pending `requiredActions` as the setup plan. After completing each
action through its documented setup, secret, upload, or auth endpoint, verify again until the result
reports `setupComplete:true` and the catalog detail reports the skill ready.

### Create and verify an agent schedule Task

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "type": "repeating",
  "accountId": $TARGET_ACCOUNT_ID,
  "title": "Hourly operations review",
  "taskContext": "Review the last complete hour and act only on material, verified issues.",
  "cronSchedule": {
    "kind": "cron",
    "expr": "0 * * * *",
    "tz": "America/Chicago"
  },
  "state": "paused"
}
EOF
```

Re-read the returned Task id, inspect `cronSchedule`, then enable only when ready. To request a
controlled run and verify its authoritative history:

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/tasks/$TASK_ID?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID"
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks/$TASK_ID/run?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  -d '{"mode":"force"}'
curl -s "$VIDA_API_BASE_URL/api/v2/tasks/$TASK_ID/runs?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID&limit=20"
```

### Assign and verify Computer Agent work

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "type": "computer",
  "accountId": $TARGET_ACCOUNT_ID,
  "title": "Review account operations",
  "taskContext": "Review current account operations and summarize only material, verified issues. Do not change anything."
}
EOF
```

Save the returned Task id. Poll the Task with the executing account scope; once
`roomId` is present, the linked chat contains the Computer Agent's work and
results.

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/tasks/$TASK_ID?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID"
curl -s "$VIDA_API_BASE_URL/api/v2/messages/$ROOM_ID?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID"
```

### Upsert contact (create or update)

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/contact?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  -d '{
    "phone": "+15551234567",
    "name": "Jordan Buyer",
    "status": "new-lead",
    "leadSource": "web-form",
    "contactSource": "landing-page",
    "tags": ["demo-request"],
    "agentContext": "Prefers SMS first. Asks for budget options."
  }'
```

### Search and paginate Contacts

```bash
curl -sG "$VIDA_API_BASE_URL/api/v2/contact" \
  --data-urlencode "token=$VIDA_API_KEY" \
  --data-urlencode "targetAccountId=$TARGET_ACCOUNT_ID" \
  --data-urlencode "q=Jordan" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=100"
```

### Enroll a Contact in an objective and merge its state

```bash
curl -s -X PATCH "$VIDA_API_BASE_URL/api/v2/contact/$CONTACT_ID/list/lease-renewal-follow-up/state?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  -d '{
    "state": "waiting",
    "nextAction": {
      "type": "call",
      "notBefore": 1784600000
    },
    "lastOutcome": "no_answer",
    "data": {
      "attemptCount": 1
    }
  }'
```

### Read recent communication logs for a Contact

```bash
curl -sG "$VIDA_API_BASE_URL/api/v2/contact/$CONTACT_ID/logs" \
  --data-urlencode "token=$VIDA_API_KEY" \
  --data-urlencode "targetAccountId=$TARGET_ACCOUNT_ID" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=100"
```

### Query communication and scheduled tasks

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID&limit=100&offset=0&sort=scheduledFor&order=desc"
```

### Create call task

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "type": "call",
  "accountId": $TARGET_ACCOUNT_ID,
  "target": "+15551234567",
  "context": "Follow up on open issue",
  "scheduledFor": 1770600000
}
EOF
```

### Create a retry-enabled call batch

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks/batches?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "tasks": [
    {
      "type": "call",
      "accountId": $TARGET_ACCOUNT_ID,
      "target": "+15551234567",
      "externalTaskId": "source-record-123",
      "context": "Current facts the calling agent needs about this person and opportunity.",
      "taskContext": "Explain the opportunity and determine whether the person wants to continue.",
      "goal": {
        "description": "Determine interest",
        "completionCriteria": "The person clearly agrees to continue or requests the proposed next step. A clear refusal is a terminal negative outcome."
      },
      "retryPolicy": {
        "delaysSeconds": [604800, 604800],
        "retryOn": ["busy", "no_answer", "no_speech", "transient_failure", "voicemail", "goal_incomplete"]
      },
      "meta": {
        "source": "source-system",
        "sourceRecordId": "123"
      }
    },
    {
      "type": "call",
      "accountId": $TARGET_ACCOUNT_ID,
      "target": "+15557654321",
      "externalTaskId": "source-record-456",
      "context": "Current facts the calling agent needs about this person and opportunity.",
      "taskContext": "Explain the opportunity and determine whether the person wants to continue.",
      "goal": {
        "description": "Determine interest",
        "completionCriteria": "The person clearly agrees to continue or requests the proposed next step. A clear refusal is a terminal negative outcome."
      },
      "retryPolicy": {
        "delaysSeconds": [604800, 604800],
        "retryOn": ["busy", "no_answer", "no_speech", "transient_failure", "voicemail", "goal_incomplete"]
      },
      "meta": {
        "source": "source-system",
        "sourceRecordId": "456"
      }
    }
  ]
}
EOF
```

### Inspect one Task and its attempts

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/tasks/$TASK_ID?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID"
```

Use the returned `logsRef.href` and per-attempt `conversationRef.href` rather
than guessing log or conversation identifiers.

### Create text task

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "type": "text",
  "accountId": $TARGET_ACCOUNT_ID,
  "target": "+15551234567",
  "context": "Send status update",
  "message": "Quick update from Vida"
}
EOF
```

### Create email task

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/tasks?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "type": "email",
  "accountId": $TARGET_ACCOUNT_ID,
  "target": "person@example.com",
  "message": "<p>Hello <strong>there</strong>.</p>",
  "meta": {
    "email": {
      "subject": "Follow-up from Vida",
      "attachments": [
        {
          "filename": "report.pdf",
          "type": "application/pdf",
          "content": "BASE64_CONTENT",
          "disposition": "attachment"
        }
      ]
    }
  }
}
EOF
```

### Queue outbound email

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/agent/outboundEmail?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "accountId": $TARGET_ACCOUNT_ID,
  "to": ["person@example.com", "second@example.com"],
  "cc": ["visible-copy@example.com"],
  "bcc": ["hidden-copy@example.com"],
  "subject": "Follow-up from Vida",
  "content": "<p>Hello <strong>there</strong>.</p>",
  "attachments": [
    {
      "filename": "report.pdf",
      "type": "application/pdf",
      "content": "BASE64_CONTENT",
      "disposition": "attachment"
    }
  ]
}
EOF
```

### Edit agent configuration

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/agentEventRules/staging?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" > staging-agent.json
# Inspect staging-agent.json, then send only the writable settings you intend to change:
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/agent?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  --data-binary @- <<EOF
{
  "agentInstructions": "Complete updated instructions",
  "timezone": "America/Chicago"
}
EOF
```

### Publish agent

```bash
curl -s -X POST "$VIDA_API_BASE_URL/api/v2/agent/publish?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID" \
  -H "content-type: application/json" \
  -d '{}'
```

### Find logs with filters

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/logs?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID&start=$START_UNIX&end=$END_UNIX&page=1&pageSize=200&eventType=message.created"
```

CSV export:

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/logs?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID&start=$START_UNIX&end=$END_UNIX&format=csv" > vida-logs.csv
```

### Get conversation details

```bash
curl -s "$VIDA_API_BASE_URL/api/v2/conversation/$ROOM_ID/$UUID?token=$VIDA_API_KEY&targetAccountId=$TARGET_ACCOUNT_ID"
```

## Response Contract

For every operation, return:

1. endpoint and method used
2. account scope used (`targetAccountId`, and `accountId` for created tasks)
3. key IDs returned (task IDs, room IDs, conversation IDs, agent account IDs)
4. pagination state (`page`, `pageSize`, `totalCount`, `hasMore`) when listing
5. next recommended action
6. `os_artifacts` summary with concrete references used to support claims

If no system artifact proves completion, report the result as pending or blocked, not complete.

## Error Handling Rules

- `401` or auth failures: verify `VIDA_API_KEY` and token query param usage
- scope failures: verify `targetAccountId` and caller permissions
- write mismatch risk: re-read affected resource immediately after mutation
- when uncertain about payload schema: consult OpenAPI URL and correct request before retrying
- if an endpoint shape seems changed, re-check the OpenAPI source of truth before additional retries
