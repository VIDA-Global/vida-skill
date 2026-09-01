# Computer Agent Cloning

Read this reference when the user wants another Vida Agent or organization to have the same
Computer Agent functionality as an existing source. The public API does not expose one atomic
Computer clone operation. Build the outcome by reading, classifying, recreating, and verifying the
required resources.

Do not use backup restore as cloning. Backups contain saved Computer state and are for recovery of
the owning Computer, not for creating a portable customer template.

## Choose the mode from resolved account scope

Read both Agent accounts and compare their `organizationId` values before planning:

- **Same organization:** one organization Computer can serve several assigned Agents. The normal
  replication topology reuses the approved organization Computer deployment while each Agent has
  its own configuration, Browser profile, and workspace. Sharing the Computer does not make one
  Agent's customer-authored workspace skill or helper source visible to another Agent. Review and
  recreate approved source in the target Agent workspace unless current API and runtime evidence
  proves another supported topology. Confirm that shared Computer code and any approved
  organization-level secret fallback are intended.
- **Different organizations:** create an independent sanitized capability on the target
  organization's Computer. Never point the target Agent's `computerDelegateAccountId` to the source
  organization or reuse the source Computer, Browser profile, inherited secrets, or runtime state.

If the organizations match but the user requires isolation equivalent to a separate customer,
require a supported independent target organization or another topology proven by the current API.
Do not promise a second isolated Computer inside one organization unless current account reads and
OpenAPI operations prove it is supported.

## Resolve the real Computer owner

Keep these identifiers separate:

- source and target Agent account IDs;
- source and target organization IDs;
- staging and live `agentConfigId` values;
- each Agent configuration's `computerDelegateAccountId`;
- the organization Computer that status and Browser-profile reads show is serving each Agent.

Read source and target live/staging Agent configuration, then read
`GET /api/v2/computer/accounts/{targetAccountId}/status`. An Agent path may resolve to an
organization-owned deployment and an Agent-specific Browser profile. Treat that ownership and
profile evidence as part of the clone plan rather than assuming the Agent account owns a separate
machine.

## Classify resources before copying

| Resource | Same organization | Different organizations |
| --- | --- | --- |
| Agent model | Re-select from target supported models | Re-select from target supported models |
| Agent and skill instructions | Reuse only after client review | Semantically sanitize into neutral instructions and target bindings |
| Generic catalog skill | Reuse target-discovered catalog item | Install target-discovered catalog item |
| Customer-authored skill/helper source | Review, recreate in the target Agent workspace, and test | Sanitize, place under a neutral target slug in the target Agent workspace, and test |
| Generated or legacy `domain_helpers/` helper | Reuse only on the shared Computer | Rebuild under `skills/{neutralSlug}/helpers/` or generate from target-local evidence |
| `computerDelegateAccountId` | May identify the approved organization Computer | Must resolve inside target scope |
| Browser profile and login | Rebuild in the target Agent profile | Rebuild in the target Agent profile |
| Secret values | Do not duplicate by default; approved inherited fallback may already apply | Never copy; collect or authorize target values through managed-secret flows |
| Channel, App, OAuth, or device setup | Rebuild or explicitly reuse a supported organization connection | Rebuild through target catalogs and authorization flows |
| Links, tenant URLs, reporting rules, webhooks, phone, SIP | Separate review and approval | Replace with target-owned values under separate approval |
| Memory, sessions, messages, Tasks, schedules, contacts, communications, logs | Exclude by default | Exclude |
| Backups, workflow recordings, screenshots, DOM evidence | Exclude | Exclude; create target-local evidence when needed |
| Workspace customer data | Exclude | Exclude |

Read `/skills/state`, `/skills/catalog`, `/helpers`, and only the specific authored workspace files
needed for the requested functionality. Read `/secrets` only for declared secret metadata. Do not
read excluded runtime categories merely to prove that they will not be copied.

## Make a metadata-only clone plan

Before mutation, record:

- mode and intended topology;
- exact source and target Agent, organization, and Computer-owner IDs;
- a fingerprint of the source configuration and authored artifacts in scope;
- every component classified as `reuse`, `sanitize`, `rebuild`, or `exclude`;
- named target bindings and whether each is resolved or needs user action;
- all excluded categories;
- provisioning, billing, login, publish, and destructive impact;
- the representative acceptance test;
- separate semantic-review and mutation approvals.

Keep the plan metadata-only. Do not include raw instructions, source files, request payloads,
credentials, customer values, access URLs, recordings, or runtime data. Re-read and recompute the
fingerprint immediately before apply. Drift in an in-scope artifact invalidates approvals.

## Cross-organization sanitization gate

Cross-organization authored artifacts must not retain or depend on source-specific:

- customer, tenant, property, contact, user, Agent, account, or configuration identifiers;
- email addresses, phone numbers, domains, URLs, webhooks, external record IDs, or storage paths;
- policies, hours, transfer destinations, escalation rules, reporting labels, or examples;
- credentials, tokens, cookies, login hints, OAuth state, secret values, or access links;
- customer records, Task context, conversations, memory, logs, screenshots, recordings, or DOM
  evidence.

Do not treat simple name replacement as sanitization. Rewrite the artifact into application-level
behavior with named target bindings, for example `TENANT_URL`, `PROPERTY_SCOPE`,
`ESCALATION_POLICY`, and declared managed-secret IDs. Keep binding values out of retained plans and
logs.

## Apply and verify

1. Re-read source and target, verify scope, compare the source fingerprint, and read the current
   OpenAPI operations.
2. Discover target models, Agent functions, Apps, Computer skills, channels, and entitlements.
3. Establish the approved topology. Provision or reconcile only when required and explicitly
   approved, then poll to terminal lifecycle state and verify health.
4. Write intended Agent fields to staging with `POST /api/v2/agent?targetAccountId=...`. Preserve
   unrelated replacement-style arrays, re-read staging, and test it before publish.
5. Install target catalog skills or write reviewed or sanitized authored skill/helper files through
   the target Agent's `/workspace`. For every authored skill, require the exact
   `skills/{skillSlug}/SKILL.md` path, first-byte YAML frontmatter with `name` and `description`, and
   equality between the directory, frontmatter name, and staged skill slug. Read the files back, then
   call `/skills/state` and require an exact `runtimeStatus.skills` entry with the expected
   `skillKey`, `source: openclaw-workspace`, workspace `filePath`, and `eligible: true`. Separately
   call `/helpers/refresh`, require clean compile and registry findings, and list the registered
   contracts. Helper compilation alone does not prove that the owning skill loaded.
6. Configure target-local secret values through `/secrets` and complete target Browser, channel,
   OAuth, or device login. Never transfer authentication state.
7. Execute each helper with safe representative target input and verify its structured result and
   destination effect.
8. Read target `/agent/functions`, stage the exact allowed Computer action, and run a staged
   conversation that actually selects and uses the helper.
9. Publish only with explicit approval, re-read live configuration, repeat `/skills/state`, and
   repeat the representative capability test.

Do not claim completion from an accepted write, provision request, helper refresh, login start, or
publish response.

## Acceptance scenarios

### Same-organization replication

Agent A and Agent B belong to one organization. Agent A uses an organization Computer with a custom
property-system skill. The accepted result proves Agent B is assigned to the intended organization
Computer, the reviewed skill and helpers exist in Agent B's workspace, and Agent B's runtime skill
state reports the expected workspace skill as eligible. Agent B uses its own Browser profile,
discovers the approved helper contracts, completes any required login in that profile, and succeeds
on representative target input. No memory, sessions, Tasks, or customer records are copied.

### Cross-organization sanitized clone

A source organization has a Browser-based property-system integration. The accepted result creates
a neutral target-owned skill and helpers in the target Agent workspace, proves the skill is eligible
in target runtime state and its helpers are registered, obtains the target tenant and login through
target-local bindings and authorization, contains none of the source tenant's names, URLs, IDs,
policies, data, or evidence, and passes representative read and write workflows in the target
environment.

## Completion evidence

Report the clone mode and topology, source and target Agent and Computer-owner IDs, plan fingerprint,
components reused/sanitized/rebuilt/excluded, staging and live `agentConfigId` values, helper
contracts, target runtime skill state, target-local setup state, terminal Computer health,
representative capability evidence, and any unresolved user action.
