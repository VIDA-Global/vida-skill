# Computer Agent Configuration

Read this reference when configuring the durable behavior of a Computer Agent or deciding whether a setting belongs in Agent staging or a purpose-built Computer Agent API.

## Configuration source of truth

Use the normal Agent staging and publish flow for durable agent-owned behavior:

- `agentInstructions`: primary operating instructions and persona
- `agentModel`: model used for Computer Agent LLM requests through Vida
- `heartbeatInstructions`, `heartbeatEvery`, and `heartbeatConfig`: proactive work
- `links`: published web knowledge
- `skills`: assigned skill instructions synchronized at publish time
- `computerDelegateAccountId`: Computer Agent delegated to by another Vida Agent

Follow [voice-agent-configuration.md](voice-agent-configuration.md) for the complete read/change/verify/publish workflow. A Computer Agent does not have a separate public runtime-model setting; its LLM requests use the Agent configuration's `agentModel`.

Do not directly edit Vida-managed prompt files to make a durable change. Publishing synchronizes the managed instruction, heartbeat, knowledge, and assigned-skill content. Use `POST /api/v2/computer/accounts/{targetAccountId}/prompts/sync` only to repair drift from the already-published configuration.

## Operational resources

These are not versioned Agent settings and use purpose-built APIs:

| Resource | API area |
| --- | --- |
| Provision, restart, upgrade, health, backups | Computer account lifecycle |
| Channel connections and web login | `/channels` |
| Skill package installation, setup, OAuth/device flows | `/skills` |
| Managed credentials | `/secrets` |
| Customer-authored project and skill files | `/workspace` |
| Canvas source, publishing, and access | `/canvas` plus `/workspace` |
| Browser access, recording, and reusable helpers | `/browser`, `/workflow-recordings`, `/helpers` |
| Memory | `/memory` |
| Immediate or scheduled work | standard `/api/v2/tasks` |
| Sessions and replicated chats | `/session`, `/api/v2/computer/sessions`, `/api/v2/messages` |
| Diagnostics and bounded repair | `/runtime/diagnostics`, `/runtime/repair` |

Read the existing resource before mutation, make the smallest change, and verify through that same resource's status or read endpoint.

Create a reusable helper when another Agent needs one stable callable operation. Store its source
with the owning skill, use `@computer_function(...)` when Browser access is unnecessary, configure
its declared Agent secrets, and verify its exact contract through `/helpers`. To use it during voice
or messaging conversations, configure the conversational Agent's `computerDelegateAccountId` and
`computer` action through the normal staging and publish flow.

## Initial setup order

1. Resolve the exact child account and its `targetAccountId`.
2. Create or update Agent staging with instructions, an available `agentModel`, heartbeat behavior, and assigned skill instructions.
3. Read staging back. Publish only when approved and verify live.
4. Read the Computer account status and provision only if no usable deployment exists.
5. Wait for lifecycle completion and verify runtime health.
6. Install and verify required skills; complete their setup actions and authentication in dependency order.
7. Configure channels and complete any user login flow; probe status.
8. Add customer-authored workspace artifacts or browser helpers.
9. Create Tasks or schedules only after the required capabilities are verified.
10. Run a representative task and inspect its linked replicated chat, tool calls, result, and relevant resource state.

## Lifecycle, health, diagnostics, and backups

The Computer API is rooted at `/api/v2/computer/accounts/{targetAccountId}`. Important operations
include:

- `GET /api/v2/computer/accounts` for authorized Computer Agent accounts;
- `GET /status` and `POST /provision`, `/restart`, `/upgrade`, or `/deprovision`;
- `GET /runtime/health`, `/runtime/logs`, `/runtime/service-logs`, and `/runtime/diagnostics`;
- `POST /runtime/repair` with explicit confirmation;
- `GET /config`, `GET /config/schema`, and `POST /config/patch`;
- `GET /backups`, `POST /backup`, backup job reads, `POST /restore`, and restore job reads.

Lifecycle, repair, backup, and restore operations can be asynchronous. Poll account or job status to a
terminal state, then verify health and the affected capability. Use paginated activity logs for
Agent work and bounded service logs for startup or service failures. Diagnostics are read-only and
return stable finding codes even when their human-readable details vary.

The configuration read returns redacted authored/effective settings and a `revision`. Patch only
supported Computer-wide settings with that current revision. Preserve redacted values by omission;
replace an array only when the user intends complete replacement. Durable Agent instructions, model,
heartbeat, knowledge, and assigned skills still belong in staging and publish.

Create a backup before destructive lifecycle work. Normal deprovisioning preserves saved state;
`wipeState:true` permanently removes it and requires explicit intent. Confirm the exact restore
snapshot and deletion behavior, wait for completion, then verify both status and health.

## Skills, setup, and credentials

Use this lifecycle for every Computer skill:

1. Read `/skills/catalog`, the selected `/skills/catalog/{skillSlug}`, and `/skills/state`.
2. Install the exact catalog choice through `/skills/install`.
3. Verify with `/skills/{skillSlug}/verify`.
4. Treat returned `requiredActions` as the setup plan. Complete them in `order` after every
   `dependsOn` action.
5. Read a declared setup value before changing it. Store non-sensitive editable values through
   `/skills/{skillSlug}/setup-state`.
6. Store sensitive declared values through `/secrets`, then check deployment. Use `/secrets/reapply`
   for drift and inspect dependencies before `/secrets/delete`.
7. For OAuth or device authorization, start the exact `/skills/{skillSlug}/auth/{actionId}/start`
   action, present the returned browser URL or device code, and poll the matching status operation to
   `succeeded`, `failed`, or `cancelled`.
8. Verify again until setup is complete and the installed state reports ready.

The Agent configuration's `skills[]` supplies Agent-specific usage instructions; it does not install
or authenticate the package. Restricted Computer runtime credentials cannot manage secrets.

## Channels

Read `/channels/catalog` and `/channels/status` before changing a connection. Configure only fields
declared by the selected catalog entry through `/channels/configure`; Vida assigns the connection and
inbound routing to the Agent in the path. Do not add a separate Agent account in raw channel config.

For Browser/device login channels, start `/channels/web-login/start`, present the returned user
action, wait through `/channels/web-login/wait`, then probe channel status. A started login is not a
working connection. Use `/channels/logout` only with explicit intent and verify disconnection.

## Workspace files and reusable helpers

Workspace routes manage customer-authored project, skill, data, and automation files. Vida-managed
root configuration and runtime-state files are hidden and blocked from customer workspace APIs;
change durable Agent behavior through Agent configuration instead.

- `/workspace/read`, `/workspace/list`, `/workspace/find`, and `/workspace/search` inspect content.
- `/workspace/write` writes complete text.
- `/workspace/edit` replaces the first exact `oldText` match.
- `/workspace/preview` and `/workspace/download` read arbitrary supported files.
- `/workspace/upload` is multipart and does not overwrite unless explicitly requested.
- `DELETE /workspace/delete?path=...` removes one file or empty directory. There is no recursive
  public deletion.

Paths are relative to the selected Agent workspace. Read or list first and verify after every write.

Canvas is the Computer Agent's static React application. Its editable source is under `app/`, which
is intentionally omitted from ordinary workspace-root listings but can be addressed directly with
the workspace read, list, find, search, write, edit, upload, preview, download, and single-path
delete operations. Treat `public/` as protected generated output; do not edit it directly.

Read `GET /canvas` before Canvas work. It returns the effective `public`, `private`, or `off`
visibility, source and published paths, and a ready-to-open reference when access is available. A
public Canvas has a stable `publicUrl`; a private Canvas has only a short-lived `launchRef`; an off
Canvas has neither. Visibility currently follows the Computer's existing setting and is read-only
through the Canvas API. After editing source, call `POST /canvas/publish`, require
`published:true`, then read `/canvas` again and open the returned URL to verify the actual result.
Keep credentials and privileged operations out of browser-delivered Canvas code; use managed
secrets and helpers for those operations.

Reusable helper source belongs with its owning skill under `skills/{skillSlug}/helpers/`. Use
`@computer_function(...)` for API, file, and data work that does not require Browser access, and
`@browser_function(...)` only when the Computer Agent's Browser session is required. Declare exact
`required_secrets`, read them through the helper runtime, and accept only business inputs as helper
arguments. Helper secrets are Agent-scoped; the runtime resolves the selected Agent first and may use
an organization-level value only as an inherited fallback. Do not pass secret values as helper
arguments. Do not edit generated helper registries.

The current helper and recording root is `helper-workspace`. Older Computers can still use the
legacy `browser-harness-workspace` name; do not move or copy evidence manually. Recorder and
generation status return the selected workspace-relative `evidenceRoot`, and starting new work
adopts finalized legacy recording bundles when a canonical root already exists. Skill lifecycle and
Browser generation refresh registration for either supported layout.

List helpers with `GET /helpers`; the returned name, argument schema, `requiresBrowser`, owner, and
required-secret IDs are the callable contract. Execute an exact name with `POST /helpers/execute`
and verify both its structured result and its destination effect.

To expose a helper during a voice or messaging conversation, set the conversational Agent's
`computerDelegateAccountId`, add the exact allowed `computer` action returned by Agent function
discovery, and map conversation values to the helper's registered arguments. Use ordinary Computer
delegation for novel multi-step work.

## Browser access and workflow generation

- `POST /browser/ticket` returns a short-lived `launchRef.href` for a person who must interact with
  the Computer Agent's Browser.
- `POST /browser/automation-sessions` returns a short-lived CDP URL, required headers, slot, and
  expiry for authorized automation tooling.
- `/workflow-recordings/status`, `/start`, `/stop`, and `/{domainKey}/generate` create reusable
  Browser helpers.
- `/{domainKey}/{recordingId}/delete` deletes one recording; domain reset is destructive.

Use the returned launch link directly rather than constructing a Browser URL. For automation,
request the returned CDP `/json/version` with its header and connect to the returned WebSocket before
expiry.

Before recording, confirm no recording or generation is active. Start with the automation session's
exact slot, perform one representative workflow, stop, retain `domainKey`, `recordingId`, and the
returned `evidenceRoot`, then generate. Supply a neutral `skillName` when a domain contains customer
information or would create a poor reusable name. Follow the generation conversation reference
while it runs. When terminal, re-list helpers and run a safe representative invocation.

## Memory, sessions, tools, and scheduled work

Use `/memory/explorer` to inspect memory and the `/memory` create/update/delete operations for compact
durable facts. Do not store credentials, transcripts, or large artifacts. Deletion is permanent.

Use `GET /api/v2/computer/sessions` to list authorized sessions and the session reset operation only
when conversational context should be discarded. `/session/resolve` returns the linked Vida room for
the selected Agent's direct or explicit authorized session. Read its messages to inspect work and
tool activity.

Read `/tools/catalog` before changing `/tools/policy` or using `/tools/invoke`. Prefer a purpose-built
route and invoke only a returned, allowed tool with narrowly scoped arguments.

Immediate Computer work and repeating/one-off schedules use the standard Task API. Load
`tasks-contacts-and-communications.md` for creation, cancellation, run history, and deletion rules.

## Heartbeats

`heartbeatInstructions` should define useful proactive work, evidence thresholds, and when to remain quiet. Avoid routine noise. Report only a legitimate operational issue or a concrete, measurable improvement. Use `heartbeatEvery` for cadence.

Advanced `heartbeatConfig` is a replacement-style authored object when supplied. Start from the current object and preserve keys the user did not ask to remove. `suppressToolErrorWarnings: true` prevents raw automatic tool-error notices from reaching customer-facing destinations; it does not suppress an intentional final alert written by the agent.

After publish, verify the live Agent configuration and the synchronized heartbeat state. If they disagree, use prompt sync and inspect every returned per-agent result.

## Completion evidence

A complete Computer Agent setup report identifies:

- account and live Agent configuration
- provisioned lifecycle and health state
- installed and verified skills
- channel connection/probe state
- heartbeat configuration and synchronization result
- representative Task ID and terminal state
- linked replicated Vida chat containing the work and tool calls
- any unresolved requirement or user action

Do not infer completion from an accepted job, login start, Task enqueue, or repair request.
