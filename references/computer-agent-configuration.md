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
| Browser access, recording, and reusable helpers | `/browser`, `/workflow-recordings`, `/browser-functions` |
| Memory | `/memory` |
| Immediate or scheduled work | standard `/api/v2/tasks` |
| Sessions and replicated chats | `/session`, `/api/v2/computer/sessions`, `/api/v2/messages` |
| Diagnostics and bounded repair | `/runtime/diagnostics`, `/runtime/repair` |

Read the existing resource before mutation, make the smallest change, and verify through that same resource's status or read endpoint.

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

## Heartbeats

`heartbeatInstructions` should define useful proactive work, evidence thresholds, and when to remain quiet. Avoid routine noise. Report only a legitimate operational issue or a concrete, measurable improvement. Use `heartbeatEvery` for cadence.

Advanced `heartbeatConfig` is a replacement-style authored object when supplied. Start from the current object and preserve keys the user did not ask to remove. `suppressToolErrorWarnings: true` prevents raw automatic tool-error notices from reaching customer-facing destinations; it does not suppress an intentional final alert written by the agent.

After publish, verify the live Agent configuration and the synchronized heartbeat state. If they disagree, use prompt sync and inspect every returned per-agent result.

## Skills and credentials

The Agent configuration's `skills[]` assigns agent-specific instructions; it does not install or authenticate the runtime package. Use the skill catalog, installation, verification, setup-value, auth, workspace, and secret endpoints for operational setup.

Never put a sensitive value in Agent configuration, skill instructions, setup-state, workspace files, or chat. Use the declared managed-secret storage key and verify deployment after saving it.

## Runtime configuration and repair

The Computer configuration read returns redacted authored and effective runtime configuration plus a `revision`. This exists for diagnostics and supported Computer-wide settings, not as the normal front door for agent-owned behavior. Use a structured patch with the current revision; omit redacted values unless explicitly replacing them. Do not use runtime configuration to override instructions, model selection, heartbeat, knowledge, or assigned skills that belong in Agent staging.

Use diagnostics when health and bounded logs do not explain a problem. Diagnostics return stable findings even when human-readable details vary. Repair requires explicit confirmation, is asynchronous, and must be followed by status, health, and diagnostic verification.

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
