# Helper Timing and Subtask Tracing

Read this when creating or changing a Computer helper, including Browser helpers. Build timing
into the helper rather than adding it only after a slow-call complaint. These are helper-authored
diagnostic conventions, not new Vida API parameters or built-in runtime features. Reuse equivalent
existing instrumentation instead of adding a second collector.

## Instrument the work inside the helper

Every helper records total elapsed milliseconds. A helper with multiple operations also records
named phases and the meaningful subtasks inside each phase. A single total or one span around a
large block does not explain its bottleneck. A trivial validation-only helper does not need an
artificial phase hierarchy. Use a monotonic clock for durations and start offsets.

For example, instrument a booking helper at these boundaries, recording duration and outcome at
every level. These names illustrate a workflow; use the actual operations of the helper being built:

```text
book_appointment
  authenticate
  check_availability
    navigate_calendar
    select_technician
    wait_for_calendar_data
    read_events
  select_customer
    open_form
    search_customer
    wait_for_matching_result
    select_match
  complete_form
    select_service
    enter_details
    validate_fields
  submit
    save_request
    wait_for_save_response
  verify_saved_record
    read_exact_record
    compare_saved_values
```

Time Browser calls, external requests, readiness waits, fixed sleeps, and fallback paths separately
where those operations exist. A wait records its outcome and polling-attempt count; aggregate repeated
polls or cap their detail to keep traces bounded. Record the fallback's reason with a static code so
an investigator can distinguish a slow primary path from recovery work. Instrument important field
groups or individual fields that can wait; do not add a span for every expression or string operation.

Give each invocation an opaque trace ID. Each detailed span has a span ID, parent span ID, static
operation name/kind, relative start time, duration, and outcome. Child spans retain their parent even
when asynchronous subtasks overlap. Nested durations are inclusive: a phase already contains its
Browser, HTTP, and wait spans. Do not add them together. Keep success, normal empty results, blocked
outcomes, timeouts, and exceptions distinguishable. Finalize diagnostics on every handled return,
including early validation failures, and close spans in finally/context-manager paths.

## Keep the conversational result compact

Declare the fields used in the helper's result metadata. Put the compact summary under
`result.diagnostics` and verify it survives the actual conversation adapter; top-level fields alone
may not be retained. A useful summary contains:

- `trace_id` and `elapsed_ms`;
- a bounded `phase_ms` map of top-level phase durations;
- a failure `code` and `phase` when applicable;
- a `trace_ref` when detailed output was written, plus truncation/write-failure indicators.

Store detailed spans in a dedicated directory under the owning skill's `outputs/`. Declare that
directory and how to resolve `trace_ref` in its procedure. Keep span count, output size, run count,
and retention age bounded. Do not automatically load trace files into the voice prompt, read them
aloud, or add model turns to collect or explain them during a call. Diagnostics are troubleshooting
evidence, never the business state used to decide whether to submit an action.

Use static, code-authored labels and safe outcome codes. Exclude customer values, source record IDs,
credentials, headers, cookies, arguments, URLs with query strings, bodies, page dumps, and raw
exception text. For HTTP evidence, record a safe operation label and numeric status when available;
an endpoint template may be used by a separate vetted collector. Avoid invasive global interception
when timing the helper's own known request or Browser call provides the necessary evidence.

## Examples of timing evidence

Implement or reuse instrumentation inside the owning skill's helper source. Choose an approach
that fits that workflow; there is no required timer package or additional Vida runtime import.
The examples below describe the evidence to produce, not additional API request fields.

For an illustrative customer-selection operation, the compact helper result could contain:

```json
{
  "status": "done",
  "summary": "Customer selected.",
  "result": {
    "diagnostics": {
      "trace_id": "example-trace",
      "elapsed_ms": 2150,
      "phase_ms": {"select_customer": 2000},
      "trace_ref": "outputs/example-run/helper-timing.json"
    }
  }
}
```

Declare the chosen diagnostic fields in that helper's result schema. The corresponding detailed
trace shows the individual subtasks and their parent relationships:

```json
{
  "trace_id": "example-trace",
  "inclusive_durations": true,
  "spans": [
    {"span_id": "helper", "parent_span_id": null, "name": "select_customer_helper", "kind": "helper", "start_ms": 0, "duration_ms": 2150, "outcome": "ok"},
    {"span_id": "selection", "parent_span_id": "helper", "name": "select_customer", "kind": "phase", "start_ms": 100, "duration_ms": 2000, "outcome": "ok"},
    {"span_id": "navigation", "parent_span_id": "selection", "name": "open_form", "kind": "browser", "start_ms": 100, "duration_ms": 600, "outcome": "ok"},
    {"span_id": "request", "parent_span_id": "selection", "name": "search_customer", "kind": "http", "start_ms": 700, "duration_ms": 500, "outcome": "ok", "http_status": 200},
    {"span_id": "wait", "parent_span_id": "selection", "name": "wait_for_matching_result", "kind": "wait", "start_ms": 1200, "duration_ms": 700, "outcome": "ok", "attempts": 3},
    {"span_id": "select", "parent_span_id": "selection", "name": "select_match", "kind": "browser", "start_ms": 1900, "duration_ms": 200, "outcome": "ok"}
  ]
}
```

The selection phase takes 2,000 ms; its subtasks are already included in that duration. The remaining
150 ms is outside the shown phase. In a complete implementation, label meaningful validation or
finalization work when measurable; do not assign an unmeasured remainder to a particular service.
These numbers and short IDs are illustrative. Generate opaque IDs for real invocations and spans.

For a failed wait, retain a compact failure code and the specific subtask, for example
`code="search_timeout"` and `phase="select_customer.wait_for_matching_result"`, along with elapsed
time and the same trace reference. The detailed wait span should report timeout and attempts.
A successful empty search instead remains a normal `done` result with a distinguishing `no_match`
code; it must not become a timeout. For a fallback, record the primary outcome and reason, then a
separate fallback span and its outcome. A recovered helper can succeed while retaining that history.

Use finally/context-manager paths to finish each started span after normal completion, early return,
or exception. Assemble diagnostics through a common result finalizer so error paths include them
as well. Preserve the helper's existing exception and mutation-reconciliation behavior.

Choose and document span/output limits and retention appropriate to the workflow; explicitly mark
truncated or unfinished traces. Define whether total timing includes the final trace write.
Measure collection overhead and state whether it overlaps the reported total, rather than adding
it twice. Trace write failures must not discard a successful business result, swallow a business
exception, or cause another submission. Keep collection local and lightweight; avoid remote log
uploads or per-poll disk writes in the hot path.

## Separate helper timing from the rest of the response

Measure helper execution, API-client round trip, and conversational response cycles separately.
Capture model request/first-token/completion times, turn counts, token usage, and orchestration
spans only when the relevant runtime actually exposes them. Correlate them using returned invocation
or trace identifiers when available; do not invent platform fields or copy customer identifiers into
trace labels. A helper's local clock cannot measure work before its entry or after its return.

Browser-observed HTTP duration includes network and client overhead; it is not server processing
time. A UI wait is not evidence of an API's response time. Missing spans mean unknown coverage,
not zero duration or proof that the model, Vida, or the external service caused the remainder.
Use only spans on a common clock to calculate uncovered intervals; do not subtract timestamps
from unrelated hosts. Do not call a response-cycle measurement audible silence without audio evidence.

## Acceptance evidence

Within the authorized test scope, verify a normal result, an empty/blocked result, an early return,
and a timeout/error path. Check nested parent relationships, separately visible waits/fallbacks,
and the final failure phase. Confirm the declared compact diagnostics survive the intended result
path without full trace contents entering the conversation. Test truncation, retention, and an
unwritable trace directory; the original business result/exception and number of submissions must
remain unchanged. Record helper and end-to-end measurements with their coverage and instrumentation
overhead. Do not replay a production mutation merely to obtain a timing sample.
