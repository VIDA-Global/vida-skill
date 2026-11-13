# One workflow, two execution paths

These examples illustrate argument mapping, not a maintained operation catalog. Read the selected
transport reference and current schema before executing. Account IDs below are placeholders;
replace them only after resolving the user's intended authorized target. Credentials are supplied
privately by the selected transport, never pasted into the example.

## Requester preflight

Goal: establish who is authenticated and their hierarchy privileges before scoped work.

- MCP: discover `GET /api/v2/account`, then call the returned account-read tool with `{}`.
- HTTP: call `GET /api/v2/account` with the private runtime API credential and no target parameter.

Apply the main skill's classification to the returned account, including `superAdmin` and
`permittedAccountIds`. Do not replace this identity with `get_profile` or a targeted account read.

## Read a selected downstream account

Goal: confirm the target's identity and parent relationships without changing anything.

- MCP: discover `GET /api/v2/account`; with the current schema, arguments are
  `{"targetAccountId": 12345}`.
- HTTP: call `GET /api/v2/account?targetAccountId=12345`, adding the private credential in-process.

The selected account describes the target, not the privileges of the requester. Confirm the target
matches the user's intended organization or Agent; do not assume an organization ID is an Agent ID.

## Inspect a bounded page of finished Tasks

Goal: read recent finished Tasks for an already-resolved Agent, without creating or rerunning work.
Read `tasks-contacts-and-communications.md` for Task semantics.

First discover `GET /api/v2/tasks` and verify its filters and pagination in the current contract.
Check documented ordering and timestamp semantics before calling the page recent; do not assume
creation order means completion order. Clarify the time basis if it matters to the user's request.
For the current schema, equivalent business arguments are:

- MCP: call the discovered Task-list tool with
  `{"targetAccountId": 12345, "state": "finished", "limit": 5, "offset": 0}`.
- HTTP: call `GET /api/v2/tasks?targetAccountId=12345&state=finished&limit=5&offset=0`,
  adding the private credential in-process.

Report the selected account, returned Task IDs and states, and pagination evidence. A finished
state is not by itself proof that the Task achieved its goal. Do not present one page as the complete
history, and do not include unnecessary contact or conversation content in the report.

## Switching transports after a timeout

If a create request times out, both paths have the same rule: query the relevant resource using
known IDs or caller-owned correlations before resubmitting. Switching from MCP to HTTP does not
make a duplicate create safe. An empty read alone may not establish absence when visibility is
delayed or correlation is missing; preserve uncertainty and do not resubmit in that case.
If HTTP lacks a securely available authorized API credential, stop
at that boundary rather than exporting the MCP token or creating a new API key automatically.
