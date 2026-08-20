# Reusable Helper Authoring

Read this reference when an Agent needs to manually create or change a reusable Computer helper.
Use the Browser workflow recording and generation APIs instead when the operation must be learned
from a website.

## Choose the helper type

- Use `@computer_function(...)` for a stable API, file, or data operation that does not open or
  consult the Computer Agent's Browser.
- Use `@browser_function(...)` only when execution needs the live Browser session, cookies, storage,
  or page state.
- Keep reusable source with its owning skill under `skills/{skillSlug}/helpers/`. Do not edit the
  generated helper registry.

## Browser-independent API example

Write an owning `skills/customer-records/SKILL.md`, then save this source as
`skills/customer-records/helpers/lookup_customer.py`:

```python
import json
from urllib import error, parse, request

from vida_helper_runtime import computer_function, managed_secret


API_ROOT = "https://api.example.com/v1"


@computer_function(
    domain="api.example.com",
    description="Look up one customer by its external ID.",
    args={
        "type": "object",
        "required": ["customer_id"],
        "properties": {
            "customer_id": {"type": "string", "description": "Exact source-system ID."},
        },
    },
    result={
        "type": "object",
        "required": ["status", "summary"],
        "properties": {
            "status": {"type": "string", "enum": ["done", "blocked", "need_user"]},
            "summary": {"type": "string"},
            "reason": {"type": "string"},
            "httpStatus": {"type": "integer"},
            "result": {
                "type": "object",
                "properties": {
                    "customerId": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
        },
    },
    required_secrets=["example_api_token"],
)
def lookup_customer(customer_id):
    customer_id = str(customer_id or "").strip()
    if not customer_id:
        return {
            "status": "blocked",
            "summary": "A customer ID is required.",
            "reason": "invalid_customer_id",
        }

    token = managed_secret("example_api_token")
    url = f"{API_ROOT}/customers/{parse.quote(customer_id, safe='')}"
    api_request = request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

    try:
        with request.urlopen(api_request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        if exc.code in (401, 403):
            return {
                "status": "need_user",
                "summary": "The API connection must be updated.",
                "reason": "authentication_required",
                "httpStatus": exc.code,
            }
        return {
            "status": "blocked",
            "summary": "The customer API rejected the lookup.",
            "reason": "api_error",
            "httpStatus": exc.code,
        }
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return {
            "status": "blocked",
            "summary": "The customer API could not return a usable response.",
            "reason": "api_unavailable",
        }

    return {
        "status": "done",
        "summary": "Customer found.",
        "result": {
            "customerId": str(payload.get("id", customer_id)),
            "name": str(payload.get("name", "")),
        },
    }
```

The decorator metadata is the callable contract. It must be made only of literal values and must
describe every input and result field callers depend on. Import `computer_function` and
`managed_secret` from `vida_helper_runtime`. Do not inline credentials, accept them as arguments, or
return them.

## Build and acceptance workflow

1. Read the existing owning skill and helper path before writing. Use `POST /workspace/write` with
   complete text for the `SKILL.md` and `.py` source, then read both back.
2. Save every ID in `required_secrets` through `POST /secrets` with `{secretId, value}` for the
   selected Computer Agent. Do not put secret values in a Task, Agent configuration, setup state, or
   workspace file.
3. Call `POST /helpers/refresh`. Require `ok: true`; inspect every compile and registry finding and
   verify the expected callable contract in `functions`.
4. Read `GET /helpers` and preserve the returned name and argument schema exactly.
5. Execute safe representative input through `POST /helpers/execute` with
   `{name: "lookup_customer", arguments: {customer_id: "..."}}`. Require a structured `done`,
   `blocked`, or `need_user` result and verify every result field against the declared metadata.
6. For mutating helpers, use an idempotency key when the destination API supports one. After a
   timeout or uncertain response, read the destination state before retrying.
7. Discover the conversational Agent's available functions. Stage the exact `computer` action and
   map conversation values to the registered argument names. Set `computerDelegateAccountId` only
   when the helper belongs to another Agent's Computer.
8. Run a staged conversational test and inspect its linked conversation. Publish only when helper
   registration, direct execution, and conversational selection all succeed.

Refresh, list, and execute representative input after every helper-source change. The public guide
is `https://vida.io/docs/api-reference/agent-guides/computer-agent-workspaces-and-helpers`.
