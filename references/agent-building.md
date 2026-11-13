# Build or Extend a Vida Agent

Read this reference for a complete Agent build or a change that adds a business workflow. Use the
focused configuration references for routine edits. Build only the capability the user requested;
a working Agent does not require a demo environment, Canvas, or extra communication channels.

## Define the workflow

Infer the brief from the conversation and existing resources. Ask only for missing decisions that
change ownership, access, business behavior, or launch state:

| Decision | Record |
| --- | --- |
| Target | Vida environment, parent organization, intended Agent account, and target software/tenant |
| Workflow | Trigger, eligible records, actions, decisions, exceptions, and source-system writeback |
| Outcome | One observable result and how to verify it independently |
| Limits | Work per run, business window/timezone, allowed mutations, and escalation conditions |
| Access | Required services, declared credential IDs, Browser authentication, and external callbacks |
| State and files | Authoritative business state, required resources, output destination, and retention |
| Delivery | Requested channels and capabilities; staged/live state and paused/active recurring work |

Translate a business description into a proposed workflow and acceptance criteria. The user should
not have to design the implementation. If production intent is unspecified, prepare a staged
capability with safe representative data and any recurring Task paused. Existing authorization
still applies; do not request the same approval again or expand it to unrelated work.

Keep a compact build record in the existing work log or completion report. Record decisions,
resource IDs, verification evidence, and unresolved dependencies without secrets or short-lived
access tickets. No particular local manifest format is required.

## Resolve ownership and access

1. Follow the authenticated requester preflight in `SKILL.md`, then resolve the exact target.
2. Before creating an Agent account, establish the intended parent organization and existing/new
   account decision. A credential's default organization proves access, not placement intent. Ask
   only if the conversation and selected resources do not establish the intended ownership.
3. Read current configuration and relevant capabilities before changing them. Reuse the intended
   Agent and usable Computer; do not repurpose another Agent or provision a duplicate deployment.
4. Give a newly built Agent a clear business-purpose name. Preserve meaningful existing names.
5. Discover models, functions, Apps, skills, channels, and entitlements in the selected account.
   Load [platform-administration.md](platform-administration.md) only for needed account/hierarchy
   operations and [voice-agent-configuration.md](voice-agent-configuration.md) for configuration.

Discover established access before asking for it. Use managed secrets and supported authorization
flows. For interactive website login, use the Browser ticket flow in
[computer-agent-configuration.md](computer-agent-configuration.md): give the user the returned
`launchRef.href`, state its expiry, then verify the expected signed-in tenant after completion.
A ticket or saved credential alone does not establish working access. Preserve a valid existing
Browser session. Record any external callback or authentication dependency explicitly.

## Choose the implementation

Use existing Vida functions and Apps when they provide the required platform behavior. Ordinary
voice, messaging, and platform actions do not need Computer helpers merely to follow this guide.

For Computer work, follow [computer-agent-build-standard.md](computer-agent-build-standard.md):

```text
Task -> owning Skill -> registered Helpers
```

The Task supplies business inputs, scope, limits, and the requested result. The skill owns the
procedure, helper selection/order, decisions, recovery, and outcome checks. Helpers implement the
defined Computer operations. Agent instructions establish role, boundaries, and routing.

Choose the entry point from the requested timing:

- Repeating work uses a repeating Task with an explicit cadence and timezone where applicable.
- A scheduled single execution uses the documented one-off Task type.
- Chat, channel, and conversational requests use the same skill/helper organization without a
  recurring schedule. A caller that knows the exact operation can execute its registered helper
  directly; it does not need an extra Computer Task.

Use [tasks-contacts-and-communications.md](tasks-contacts-and-communications.md) for exact Task
behavior. `taskContext` names the skill and supplies inputs; it is not a typed skill/helper binding.

## Build and configure the selected capability

For Computer operations:

1. Inventory the owning skill, helpers, required resources, authentication, state, and outputs.
2. Inspect the target software as needed to establish a reliable operation. Use an evidenced API
   where available; Browser exploration and recording are construction tools, not a mandatory step
   for API or file work. Recording-to-helper generation is optional; reviewed source can also be
   authored directly. Do not require a website recording for a Browser-independent helper.
3. Write the skill procedure and helpers together using
   [helper-authoring.md](helper-authoring.md). Choose `@computer_function(...)` for API/file/data
   work and `@browser_function(...)` only when authenticated Browser context is needed.
4. Declare exact business inputs, durable source IDs, result fields, secret IDs, and bounded failure
   behavior. Include complete pagination/eligibility rules where relevant. Keep secrets out of
   source, arguments, Task context, and results.
5. Keep resources and generated outputs with the skill. Declare retention and delivery. Separate
   reusable source from customer outputs when packaging or cloning; follow
   [computer-agent-cloning.md](computer-agent-cloning.md) when replicating a capability.

Use [voice-agent-configuration.md](voice-agent-configuration.md) to stage only required role,
routing, functions, model/voice, channels, and reporting changes. Map conversation values to exact
helper argument names. A Computer Agent uses its own Computer automatically; configure a delegate
only when another Agent's Computer is intended. Keep the multi-step procedure in the skill.

Do not introduce heartbeats, conversational memory, loose scripts, or workspace searching as
operational dependencies. Keep business progress and deduplication in the declared authoritative
state source, with reconciliation before retrying an uncertain mutation.

## Verify the delivered path

Use safe representative data and authorized destinations. A technical integration can use a small
fixture; build a broader synthetic environment only when the requested capability needs it.

- Prove skill discovery separately from helper compilation. For catalog skills, complete setup and
  require `verifiedReady:true`; for authored workspace skills, prove the exact eligible runtime
  entry. Follow the distinct checks in
  [computer-agent-configuration.md](computer-agent-configuration.md).
- Check each required helper's registered contract, then execute representative input. Preserve
  opaque IDs across helper handoffs and verify actual destination effects independently.
- Test the intended Task, on-demand request, or staged conversation in a fresh execution without
  relying on the builder's prior chat or temporary files. Test a relevant blocked/exception case,
  including authentication recovery or uncertain-write handling when it matters to this workflow.
- For recurring work, inspect one controlled run and a second run that proves prior work is skipped
  or reconciled. Check linked conversations and destination state before forcing another run.
- For selected communications, inspect the terminal Task/conversation and source-system writeback.
  Use [logs-conversations-and-reporting.md](logs-conversations-and-reporting.md) for evidence.

Do not treat accepted writes, setup verification, helper refresh, queued Tasks, or login starts as
proof that the business workflow works.

## Publish and hand over

Publish and activate recurring work only within the user's authorization. Verify the live
configuration and the intended execution path afterward. Do not publish an unrelated configuration
or activate a schedule merely because its paused test passed.

For an existing Agent, compare staging with live before publication. Preserve unrelated staged work;
publishing includes those differences too, so resolve the release scope before proceeding.

Report the exact account/configuration, trigger or entry point, owning skill, registered helpers,
state/output locations, staged/live and schedule state, representative evidence, and unresolved
user actions. Include output references through the intended channel. Customers should not need
filesystem access to operate the Agent. Leave any unverified capability pending and identify the
specific dependency that prevents completion.
