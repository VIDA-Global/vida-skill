# Tasks, Contacts, and Communications

Read this reference for Contact-centered work, communication Tasks, Computer work, retry workflows,
repeating or one-off schedules, batches, outbound communication, and inbound email events. Use the
current OpenAPI for complete schemas.

## Contacts and objectives

Use Contacts for work centered on people. Keep inventory, invoices, tickets, documents, and other
business records in their source systems.

Primary operations:

- `GET /api/v2/contact` searches and paginates Contacts.
- `GET /api/v2/contact/{contactId}` reads one Contact.
- `POST /api/v2/contact` creates or updates a Contact.
- `PATCH /api/v2/contact/{contactId}` merges allowed fields.
- `DELETE /api/v2/contact` permanently deletes one Contact.
- `GET /api/v2/contact/list` lists Contact List labels.
- `GET|POST|DELETE /api/v2/contact/list/{listName}` reads or changes membership.
- `PATCH|DELETE /api/v2/contact/{contactId}/list/{listName}/state` manages one objective and its
  matching state atomically.
- `GET /api/v2/contact/{contactId}/logs` returns recent communication references.

Use one concise, stable Contact List name for an ongoing objective. Before creating one, read current
lists and reuse an exact match. The objective-state endpoint uses the same list name below
`customFields`; do not invent a second key.

Compact state may include a current state, next action and `notBefore`, last action/outcome, and small
workflow data. Keep the complete `customFields` object within the documented 8 KB limit. Do not copy
transcripts, API responses, credentials, cookies, or large source records into it.

Vida maintains communication indexes such as `recent`, `recentlyCalled`, `recentlyMessaged`, and
`recentlySentEmail`. Query them when useful, but do not manually maintain them or treat membership as
proof of an outcome.

To continue an objective, read its Contacts, objective state, active/prior Tasks, recent Contact
logs, and any current source-system facts. Perform and verify the next action, then patch the outcome
and next action. Waiting, paused, cooling-down, and blocked Contacts remain enrolled; delete the
state only when the Contact should leave the objective.

## Task model

Primary operations:

- `GET|POST /api/v2/tasks`
- `GET|POST|DELETE /api/v2/tasks/{taskId}`
- `POST /api/v2/tasks/cancel`
- `GET /api/v2/tasks/{taskId}/logs`
- `GET /api/v2/tasks/stats`
- `POST /api/v2/tasks/batches`
- `GET /api/v2/tasks/batches/{batchId}`
- `GET /api/v2/tasks/limits`
- `POST /api/v2/tasks/{taskId}/run`
- `GET /api/v2/tasks/{taskId}/runs`

Common Task types are `call`, `text`, `email`, `ping`, `computer`, `repeating`, and `cronOneOff`.
Communication Tasks normally use public states `pending`, `processing`, `running`, `finished`,
`errored`, and `canceled`; scheduled Tasks also use `active` and `paused`.

Include query `targetAccountId` on Task operations. On create, body `accountId` must identify the
Agent account that will perform the work and normally equals the query scope. `externalTaskId` is
reusable correlation data, not an idempotency key. Reconcile existing Tasks before retrying an
uncertain create.

Use `context` for Contact or situation facts and `taskContext` for instructions about the work.
Task `meta` is retained for filtering and reporting but is not automatically added to the Agent
prompt.

Whenever a Task has an associated Vida room, its response includes `chatRef` with the room ID,
selected Agent account, and a ready-to-use Messages API URL. The field can be absent before a room
has been created. Use `chatRef` for the complete linked chat; use `conversationRef` for one specific
communication attempt and `runsRef` for terminal scheduled-run summaries.

## Communication Tasks and retries

Call, text, and email Tasks require the documented target and channel-specific content. Read Task
limits before creating work. Business hours, daily limits, cooldowns, concurrency, and rate limits
can keep an accepted Task pending; an initial `scheduledFor` outside configured business hours is
rejected.

One retry-enabled Task represents one logical goal and every attempt toward it. Do not create one
Task per attempt.

- `goal.completionCriteria` distinguishes success, explicit negative resolution, and inconclusive
  conversations.
- `retryPolicy.delaysSeconds` defines same-channel delays.
- `retryPolicy.steps` defines increasing channel-specific offsets. Use either delays or steps.
- `retryPolicy.retryOn` contains only outcomes the workflow should retry.
- `retryPolicy.responseTimeoutSeconds` controls how long text or email waits for a response.

Use the exact bounds and enums in OpenAPI. `goal_met` and `terminal_negative` stop retries.
Retry-enabled Tasks are immutable after creation except for cancellation. Read `attemptHistory`,
`result`, `logsRef`, and per-attempt conversation references on the original Task.

Organization `defaultRetryConfiguration` supplies an omitted or null goal or retry policy
independently. Explicit fields replace the corresponding default; they are not field-merged. Supply
both explicitly when the workflow needs an exact goal and cadence.

Outbound call and text Tasks may use a managed number pool only after Vida enables that optional
organization capability. There is no public pool-management API. Verify assigned inventory and run a
representative Task before increasing volume.

## Computer Tasks

Use `type:"computer"` for one bounded piece of work on a provisioned Computer Agent. It requires the
executing `accountId` and complete `taskContext`, and may include title, schedule time, correlation,
and reporting metadata. Do not add communication targets, retry policies, Contact context, or raw
session fields.

Vida creates a dedicated linked chat. Poll the Task to `finished`, `errored`, or `canceled`, then use
its `chatRef` with the Messages API to inspect the complete work, tool activity, and result. Cancel
with a scoped Task update to `state:"canceled"`. Delete only with explicit intent;
deletion stops active work before removing the Task record.

## Repeating and one-off Tasks

Create schedules through the Task API, not private metadata:

- `type:"repeating"` uses `cronSchedule.kind` `cron` or `every`.
- `type:"cronOneOff"` uses `cronSchedule.kind` `at`.
- Both require nonblank `title` and `taskContext`.
- Cron expressions use five-field minute precision; `everyMs` is at least 60,000.
- Create paused when review is required before activation.

Scheduled Task updates accept only the documented title, task context, state, and timing fields.
Run a controlled test with `/tasks/{taskId}/run`; `force` runs regardless of due time while `due`
uses due-only behavior. A `202` proves acceptance, not completion. Inspect `/tasks/{taskId}/runs`;
`/logs` is communication history, not scheduled-run history. Once `chatRef` appears, follow it for
the Agent's live work and tool calls; `/runs` contains compact terminal status, timing, and error
summaries. An empty `/runs` response while work is active is not evidence that nothing ran and is
not a reason to force another run. Delete the Task to remove future execution. Do not manufacture
`meta.cron` or `cron:job:` identifiers.

For every proactive workflow, confirm that its trigger actually exists. A configured helper and
instructions do not create a schedule. For poll-and-act workflows, define timezone, per-run limits,
opaque source identifiers, deduplication, capacity checks, and ambiguity-safe writeback. Create the
repeating Task paused, force one representative run, inspect its linked chat and destination effects,
then activate it deliberately.

## Batches

Before creating a batch, reconcile active and prior Tasks with stable source metadata. Save the
returned `batchId`. For asynchronous acceptance, poll the batch to a terminal state and inspect
inserted, rejected, failed, and skipped rows. A failed synchronous request can already have created
earlier rows; after any timeout, conflict, or server error, query before resubmitting. Reuse the same
idempotency key and payload only where OpenAPI documents asynchronous idempotency.

## Outbound and inbound communication

Convenience operations `POST /api/v2/agent/outboundCall`, `/outboundSms`, and `/outboundEmail`
create Tasks. Use the same Agent in query `targetAccountId` and body `accountId`. Follow OpenAPI for
single versus multiple recipients, message content, subject, attachments, schedule, and spacing.

Before relying on an inbound-triggered email reply, read the Agent's inbound policy and allowlist. In
`allowlist` mode, the exact originating sender must already be listed; otherwise Vida creates no
inbound message, `email.received` event, or Agent work. `open` mode accepts any sender that passes
standard email authentication checks, including DKIM alignment. This gate affects inbound
acceptance, not recipients passed to `/api/v2/agent/outboundEmail`.

For an `email.received` event:

1. Read `roomId`, `messageUuid`, `targetAccountId`, sender, and subject from the event.
2. Fetch `GET /api/v2/messages/{roomId}` in the event's account scope.
3. Select the exact UUID; only fall back to the latest matching inbound email when UUID is absent.
4. Inspect text/HTML metadata, thread headers, and attachments.
5. Fetch attachments from their Vida `content-url`, URL-encoding the filename segment.
6. Reply through `/api/v2/agent/outboundEmail` with the original `roomId` and
   `replyToMessageUuid`; body `accountId` equals the event account.

Do not treat a queue response as delivery, conversation, or goal completion. Verify the terminal
Task and linked communication evidence.

For a complete retry-aware communication workflow, use
`https://vida.io/docs/api-reference/cookbooks/outbound-workflow` with this reference and current
OpenAPI schemas.
