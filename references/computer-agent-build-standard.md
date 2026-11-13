# Computer Agent Build Standard

Read this reference before creating, extending, or reorganizing a Computer Agent workflow through
the Vida skill.

## Required delivery structure

Build every Computer Agent workflow as **Task → Skill → Helpers**.
Repeating Tasks trigger recurring work; skills define the procedure; helpers perform its Computer
operations, including Browser operations. On-demand workflows use the same skills and helpers
without an unnecessary schedule. A known operation can also be invoked through its exact registered
helper. Ordinary Vida communication and other platform actions continue to use their documented
functions and APIs.

This is a build and organization standard, not an API removal or a new API schema. Workspace,
Browser, session, diagnostic, and other management APIs remain available for construction and
authorized maintenance. Their availability does not make them a suitable foundation for a delivered
workflow. Do not make customers manage files, memory, sessions, or heartbeats to operate the Agent.

## One home for the skill and its files

Give each workflow an owning skill with a stable, lowercase hyphenated slug. Reuse an appropriate
existing skill before creating another. Keep its source, required resources, and generated files
together, with separate subdirectories for their different lifetimes:

```text
skills/{skillSlug}/
  SKILL.md                  # Workflow procedure and dependency declarations
  helpers/                  # Registered Computer and Browser helper source
  references/               # Optional detailed procedures or domain rules
  assets/                   # Optional required templates or static resources
  outputs/{runId}/           # Retained generated files, such as reports, CSVs, or PDFs
  tmp/{runId}/               # Optional disposable scripts, downloads, and intermediate files
```

This layout is an authoring convention, not an API requirement; `runId` is a chosen run identifier,
not an additional Task or helper request field. Create only the directories the workflow needs. Follow
[computer-agent-configuration.md](computer-agent-configuration.md) for required frontmatter,
runtime discovery, assignment, and publication. Helper registration alone does not prove the skill
loaded.

The owning `SKILL.md` must identify every required resource and any dependency on another skill's
registered helpers. Keep shared helpers in one named owning skill rather than copying them. Use
skill-relative resource references; do not depend on an operator's home directory, incidental
working directory, or an absolute container path. Keep required instructions, scripts, and templates
out of loose workspace-root files and miscellaneous project directories.

On the Computer, write generated file deliverables to the owning skill's `outputs/{runId}/` and
disposable work to its `tmp/{runId}/`. Use a distinct run directory so later executions do not
overwrite earlier results. Helpers return the resulting file paths or artifact references with a
compact summary. A customer can still receive the result through its configured delivery channel
or external destination; they do not need to browse the workspace.

Reports, CSVs, PDFs, and other retained results are outputs, not scratch. Preserve them according to
the workflow's retention requirements and account for them explicitly when transferring the skill.
Only `tmp/` is disposable; neither helpers nor skill procedures may depend on files there after a
build or run. Keep the builder's local manifest, work log, and evidence in its host-side run record.
Vida-managed recording and generation APIs choose their own evidence roots; preserve their returned
references and do not move those bundles. Optional Canvas source remains under its documented
`app/` path.

## Skill procedure and helper contracts

Write the owning skill so a fresh execution can follow the workflow without the builder's chat
history. Include:

- the trigger, business inputs, scope, and success criteria;
- exact registered helper names, their order or selection rules, and input/output handoffs;
- eligibility, decisions, per-run limits, and output or writeback destinations;
- bounded retry, stop, escalation, and authentication-recovery behavior;
- durable source identifiers, deduplication, and reconciliation after uncertain mutations;
- required skill resources, managed-secret IDs, and external services or authentication dependencies.

Use `@computer_function(...)` for API, file, and data operations independent of Browser state;
use `@browser_function(...)` when the live Browser context is required. Prefer an evidenced API
operation over UI interaction when possible. Both kinds remain registered, skill-owned helpers with
declared inputs, results, and secret requirements. Follow [helper-authoring.md](helper-authoring.md).

Agent-level instructions set the role, boundaries, and routing to skills. Do not maintain a second
copy of the workflow in the Agent prompt or Task context. Keep business state in its authoritative
source system or an appropriate documented Vida resource; use Contacts only for person-centered
state. Do not use conversational memory or loose progress files as an operational database. If the
workflow processes files, declare their source, destination, ownership, and retention explicitly and
access them through helpers. Store required static resources in `assets/`, retained generated files
in `outputs/`, and disposable intermediates in `tmp/`. A workflow that consumes a prior output must
declare that input explicitly; it must not search old runs or scratch to infer its state.

## Task and on-demand entry points

For recurring work, use a repeating Task with an explicit cadence and timezone where applicable.
Use the documented one-off Task type for a scheduled single execution. Task `taskContext` names the
owning skill and provides business inputs, scope, limits, and the requested outcome; the procedure
stays in the skill. The current Task schema has no typed skill/helper binding: do not invent fields
such as `skillId` or `helperName` on Task creation. See
[tasks-contacts-and-communications.md](tasks-contacts-and-communications.md).

For example, a Task can say: "Use the `invoice-follow-up` skill for the configured tenant. Process
at most 20 eligible invoices and report completed, skipped, and blocked records to the configured
destination." The skill supplies the actual helper sequence and outcome checks.

For on-demand work, route the request to the same skill and registered helpers. A caller that
already knows the exact operation can use `/helpers/execute` with the registered name and business
arguments, including for Browser helpers. This is separate from `/tasks/execute`, which creates an
ordinary Computer Task. Do not add a generic Browser action for a registered-helper workflow.

## Construction tools and existing capabilities

During construction, use workspace inspection and editing, Browser exploration and recording,
temporary Computer Tasks, and logs or session inspection as needed to learn, implement, and debug
the workflow. Turn a proven operation into a registered helper before delivery; ad hoc code and
general Computer delegation must not remain the routine execution path.

Do not introduce heartbeat-based business schedules, runtime memory dependencies, or instructions
to browse the workspace to discover what to do. Use explicit Tasks and skill procedures instead.
Existing memory, heartbeat, and other management APIs can still support an explicitly requested
investigation or maintenance task; this standard does not authorize disabling or deleting existing
customer behavior. For a scoped extension, apply the standard to the changed workflow and record
any remaining legacy dependency rather than silently reorganizing the whole Agent.

## Delivery acceptance

Record a compact workflow inventory in the build record or completion report: trigger/Task ID or
on-demand entry point → skill slug and source path → exact helpers, plus required resources,
secret IDs (never values), authentication dependencies, state sources, and output destinations.
Identify the skill's output and temporary directories separately from its source and build evidence.

Before calling the workflow complete:

1. Read the skill package back, prove runtime discovery, and verify helper registration and contracts.
2. Execute each required helper with safe representative input and verify its result and destination
   effect. Setup verification and compilation do not replace execution evidence.
3. Test the intended entry point in a fresh execution, without relying on the builder's conversational
   session, memory, or scratch files. Reuse declared business state and authenticated Browser
   profiles as intended; do not reset an existing customer session to test this.
4. For recurring work, create the Task paused, inspect one controlled run, and verify a second run
   skips or reconciles prior work. Activate only within the user's authorized scope.
5. Account for every authored runtime dependency in the skill inventory. Check that no required
   procedure or script remains outside its owning skill or depends on `tmp/`. Clean only this
   build/run's disposable files in its `tmp/` directory when appropriate. Preserve `outputs/` under
   the declared retention policy; never sweep an existing workspace or delete customer results as
   automatic build cleanup.

If a required operation, state store, callback, or authentication flow cannot meet this structure,
record the exact dependency and unresolved limitation. Do not hide it behind a freeform prompt or
claim the workflow is ready to transfer to another execution system.
