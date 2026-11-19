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

## Reusable implementation

[assets/helper_timing.py](../assets/helper_timing.py) is a standard-library template. Copy it into
the owning skill's `helpers/helper_timing.py` and import it from the helper. It supports nested spans,
async-context parent isolation, a compact phase summary, bounded private trace files, and retention
limited to its own filenames. It is not an installed Vida runtime module. Adapt or reuse an existing
collector when the workflow already has one.

```python
from pathlib import Path
from helper_timing import HelperTiming

def example_helper(customer_id):
    timing = HelperTiming(
        "example_helper",
        output_dir=Path(__file__).resolve().parent.parent / "outputs" / "helper-timing",
    )
    response = None
    try:
        # The implementation owns business errors, confirmations, and retry policy.
        response = run_business_work(customer_id, timing)
        return response
    finally:
        diagnostics = timing.finish(
            response["status"] if response is not None else "failed",
            response.get("reason") if response is not None else "unexpected_error",
        )
        if response is not None:
            response.setdefault("result", {})["diagnostics"] = diagnostics

def run_business_work(customer_id, timing):
    with timing.span("customer_lookup", kind="phase"):
        with timing.span("customer_request", kind="http") as request_span:
            response = perform_existing_request(customer_id)
            request_span.annotate(http_status=response.status)
        with timing.span("parse_customer_response"):
            customer = parse_existing_response(response)
    return {"status": "done", "summary": "Lookup complete.", "result": customer}
```

This sketch shows placement; [helper-authoring.md](helper-authoring.md) has a complete registered
example. The template's defaults are 256 child spans, 200 retained runs, and seven days of retention;
choose limits appropriate to the workflow. `trace_ref` is relative to its configured output directory.
`elapsed_ms` includes final persistence, while the detailed root's `body_elapsed_ms` ends before
persistence. `instrumentation_ms` measures collector bookkeeping/writing and overlaps total elapsed
time. It is not extra time to add to that total. An unfinished or truncated trace must say so.

Trace write failures must not discard a successful business result, swallow a business exception,
or cause another submission. Keep the collector local and lightweight. Measure instrumentation
overhead on representative work; avoid remote log uploads or per-poll disk writes in the hot path.

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
