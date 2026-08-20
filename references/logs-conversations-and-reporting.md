# Logs, Conversations, and Reporting

Read this reference for troubleshooting, conversation inspection, metrics, experiments, and
evidence-backed reporting.

## Choose the right record

- Use a conversation when each completed interaction is one observation.
- Use a Task attempt when unanswered, failed, or delivery-only attempts belong in the population.
- Use one terminal Task outcome when a retry sequence should count once.

Do not use a Task enqueue, outbound request, or summary log as proof that a conversation occurred or
that its goal was met.

## Query logs

Use `GET /api/v2/logs` with the intended `targetAccountId` and bounded Unix-second `start` and `end`
for routine work. Select only required fields and filters. Follow pagination for JSON and use CSV for
large exports. Request field metadata when building a new integration instead of assuming every
account produces the same reporting fields.

Use comparison suffixes and exact filter values only as documented in OpenAPI. A Contact log or Task
attempt can include `conversationRef`; follow it instead of guessing room or message identifiers.

## Expand conversations

- `GET /api/v2/conversation/{roomId}/{uuid}` returns one complete conversation.
- `POST /api/v2/conversation/batch` expands a bounded set.
- `GET /api/v2/messages/{roomId}` returns room messages.
- Computer Tasks and sessions expose linked Vida chats containing work, tool calls, and results.

Keep room, message, Task, Contact, Agent-account, and Agent-configuration IDs distinct in analysis.

## Metrics and reporting fields

Define measurement before publishing an Agent or starting an experiment:

1. Name the business outcome and observation unit.
2. Use a standard log field when one exists; otherwise add a stable typed `reportingFields` entry.
3. Define when a value is null rather than turning unknown results into false.
4. Test successful, negative, and inconclusive cases.
5. Confirm the emitted values in bounded logs.
6. Validate the metric through `POST /api/v2/logs/timeSeries` before saving it.

Keep numerator, denominator, filters, formula, aggregation, scaling, and time range explicit. Review
the returned event count with the metric value. For retry workflows, decide whether the denominator
is attempts or terminal Tasks. Use `minimumSampleSize` when small groups should not produce a result.

Organization dashboard definitions live in `settings.metrics`. Read the organization, preserve
unrelated definitions, upsert by stable name, save the complete intended array, and re-read it.
Agent-authored reporting fields remain in Agent staging; effective inherited fields are read-only.

Useful patterns:

- For a boolean reporting-field rate, filter the field with `isset`, use the field as the formula,
  aggregate with `avg`, and scale by 100. The denominator is only records where the field is not null.
- For a choice count, filter the field to the exact choice, use formula `1`, and aggregate with
  `count`.
- For attempt-based metrics, filter `taskAttemptId` with `isset`. Do not require a transcript when
  failed or unanswered attempts belong in the denominator.
- To count one final outcome per retry Task, use the documented terminal `task_goal` outcome filter
  and validate it against underlying Tasks before saving the definition.

For experiments, compare like-for-like populations and time ranges using `experiments.id`,
`experiments.variant`, and `experiments.versionId`. Keep the same reporting definitions across
variants and report sample size and guardrails with every conclusion.

## Incident evidence

For a customer-impacting event:

1. Query the exact account and bounded time window.
2. Identify affected Task, room, conversation, Contact, and Agent IDs.
3. Expand relevant conversations and Task attempts.
4. Establish a source-timestamp timeline.
5. Separate observed impact from inferred cause.
6. Inspect Computer health, service logs, or diagnostics only when that runtime is involved.
7. Recommend a bounded remediation and a verification step.

A useful incident report identifies scope, timestamps, evidence references, current state, customer
impact, and remaining uncertainty. Keep raw diagnostics separate from the customer-facing conclusion.
