# Computer Helpers in Voice Conversations

Read this reference when building or optimizing Computer helpers that run while a caller waits.
Use it with [computer-agent-build-standard.md](computer-agent-build-standard.md) and
[helper-authoring.md](helper-authoring.md). It supplements their registration, authentication, and
verification requirements; exact API and function capabilities still come from current discovery.

## Choose boundaries around the conversation

Give each helper one bounded business purpose: the next fact the caller needs or the action they
have confirmed. Separate identification, appointment lookup, availability, and booking when the
caller needs to confirm identity, choose a result, or authorize a change between those steps.
Return to the caller at those decision points. Run later stages only when needed and after their
required input or confirmation; reuse answers already given. General availability or information
requests need not identify a customer.

Keep the live checks required for a mutation, its submission, and verified readback in one helper.
Splitting those steps can create a stale decision or an unverified outcome. Internal UI primitives
can remain ordinary functions inside that helper; each click does not need a separate remote call.
Small means limited responsibility, not a line-count limit or a universal execution deadline.
Background and batch work can have different boundaries from an interactive voice workflow.

When the operation maps to a registered helper, configure the conversational `computer` action to
call its exact name with complete `helper.arguments`, supplying `task` and `preFunctionReply` according
to the discovered function contract. Task text does not populate helper arguments. Avoid extra model
delegation to reinterpret an already known operation. Preserve one execution of each confirmed
mutation; silence is not evidence that it needs to be called again.

## Reuse identifiers through explicit contracts

Discovery helpers must return the stable source identifiers needed downstream. Later helpers must
accept those identifiers directly rather than requiring another phone, name, or address search.
Preserve the exact values, entity types, source system, and account scope. Numeric page IDs and
opaque API IDs are different identifiers unless their relationship has been verified.

The calling agent retains confirmed values within the current conversation and passes them into
the next helper explicitly. Declare these inputs and outputs in the helper metadata and owning
skill procedure. Do not create a dependency on persistent conversational memory, old trace files,
or a new scratch database. A separate callback resolves its context from the authoritative system.

Reuse does not remove live ownership or freshness checks. Read the exact record to verify it belongs
to the confirmed customer and account before changing it; recheck availability before committing a
booking. If direct ownership data is unavailable, use a bounded, evidenced fallback that proves the
same record's ownership. A conflicting owner or account must block the mutation. Missing, invalid,
or stale IDs require an explicit recovery or clarification path, not silently selecting another
record. Clear retained customer context when the caller changes the customer or account.

## Reuse Browser state and wait for the needed condition

Reuse the authenticated Browser profile and relevant tab as described in
[computer-agent-configuration.md](computer-agent-configuration.md#reuse-browser-tabs-during-computer-tasks).
Choose a working page as a helper's start URL; recover authentication only when the session requires
it. Check the current page before navigating or reloading, and account for the helper runner's own
startup navigation. Reusing a page must still establish that the data needed for the action is fresh.

Prefer an evidenced API operation over UI work when it provides the required result with verified
authentication, scope, and semantics. Otherwise, query or navigate directly using known IDs instead
of loading a directory and filtering it. Read existing form values and update only those that differ.

Replace fixed pauses with bounded checks for the exact condition: the unique matching option,
accepted field value, selected technician, finished loading state, or persisted outcome. A generic
dropdown being present does not prove that the requested option is ready. Handle each required
wait's timeout explicitly. Use a fixed delay only when evidence shows it is needed, and document why.
Do not depend on an optional toast or transient banner when a direct saved-state read can verify
the result. Follow the existing reconciliation rules after uncertain writes; never save again merely
because verification timed out.

## Keep results small and delays diagnosable

Return a bounded set of relevant facts, exact IDs, outcome, and any verified status needed for the
next turn. Keep helper descriptions and routing instructions concise. Leave detailed implementation
in the owning helper and procedure instead of copying it into the Agent prompt or every task.

Build total, phase and nested subtask timings into helpers from the start, following
[helper-timing-and-tracing.md](helper-timing-and-tracing.md). Keep only declared compact diagnostics
in result.diagnostics, verify that they survive the voice result path, and retain bounded detailed
traces outside conversational context. Measure helper and broader response times separately;
missing model/orchestration spans remain unknown and overlapping spans are not additive.

Give a brief initial progress notice. Verify runtime support before promising an announcement while
a helper remains pending; prompt instructions alone cannot guarantee speech during a blocking call.
Do not invent progress settings or assume delegated async options change a direct helper's behavior.

## Example: appointment workflow

These helper names and fields are illustrative contracts, not built-in Vida functions.

| Step | Helper and handoff | Conversational boundary |
| --- | --- | --- |
| Identify | `find_customer(confirmed_phone)` returns `customer_id` and `service_address_id`. | Resolve ambiguity and confirm the customer and service address. |
| Offer times | `find_availability(date_range)` returns a small set of slots. | Gather missing preferences, then let the caller choose and confirm the action. |
| Book | `book_appointment(customer_id, service_address_id, chosen_slot, purpose)` checks live ownership/availability, submits once, verifies, and returns `appointment_id`. | Report the verified result. |
| Cancel later in the same call | `cancel_appointment(appointment_id, expected_customer_id)` checks live ownership, cancels once, and verifies. | Obtain the required cancellation confirmation before execution. |

Do not search for the customer again inside booking when the confirmed ID is available. Do not look
up appointments again to cancel the exact appointment just returned by booking. If a separate call
does not yet know the appointment, identify the customer and look up appointments by the returned
customer ID before requesting a confirmed change.

## Acceptance evidence

Extend the existing intended-entry-point test with these checks, within authorized test scope:

- The conversation returns to the caller for necessary choices or confirmations, without chaining
  unrelated work or forcing an extra conversational turn when no customer input is needed.
- Returned IDs reach downstream helpers unchanged. An already known customer/appointment does not
  trigger another discovery search; wrong ownership blocks, and unavailable ownership uses the
  declared fallback. A separate callback does not depend on the prior conversation's memory.
- A valid authenticated session and suitable page are reused. Required freshness checks still run.
- A timeout or uncertain write produces a diagnosable outcome and reconciliation path, without a
  repeated mutation or an unsupported success claim.
- Record response-time targets and observed results for representative operations, including an
  already authenticated session. Report helper time separately from the broader response cycle,
  explain relevant differences in test scope, and distinguish observations from averages or guarantees.

Compilation and schema checks alone do not establish conversational pacing or acceptable latency.
