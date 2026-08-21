# Voice Agent Configuration

Read this reference when creating, editing, publishing, versioning, or experimenting with a Vida Agent configuration. The live OpenAPI at `https://vida.io/docs/apiv2.json` remains authoritative for exact request and response schemas.

## Identity and scope

- `targetAccountId` is the stable Vida account that owns the agent. Use it to scope requests.
- `agentConfigId` is the ID of a staging, live, or saved agent configuration record. Staging and live normally have different IDs.
- `versionId` identifies a saved snapshot.

Never use an `agentConfigId` as `targetAccountId`. Public requests and explanations must use `agentConfigId`; do not introduce alternate configuration-ID terminology.

## Read, change, verify, publish

1. Read `GET /api/v2/agentEventRules/staging?targetAccountId=...`.
2. If staging is empty, read `GET /api/v2/agentEventRules/default?targetAccountId=...` for the live configuration.
3. Save the original response before editing.
4. Discover dynamic values and account eligibility:
   - `GET /api/v2/models/supported?targetAccountId=...`
   - `GET /api/v2/agent/voices?targetAccountId=...`
   - `GET /api/v2/agent/functions?targetAccountId=...`
   - `GET /api/v2/apps?targetAccountId=...`
5. Send only intended writable settings to `POST /api/v2/agent?targetAccountId=...`. Omitted settings retain their staging values.
6. Re-read staging and compare every intended field.
7. Test staging when the change affects conversations or tool behavior.
8. Publish only with explicit intent using `POST /api/v2/agent/publish?targetAccountId=...`.
9. Re-read `/agentEventRules/default` and verify the live values.

Arrays such as `actions`, `apps`, `skills`, and `reportingFields` are complete authored arrays when supplied. Read and preserve members the user did not ask to remove. Do not write calculated response fields such as function `allowed`, `reason`, or `missingRequirement`, `activeEventRules`, or `effectiveReportingFields`.

## Intelligence

- `agentModel` is the primary model for voice, messaging, and Computer Agent work.
- `agentThinking` configures supported reasoning on the primary model.
- `agentThinkingModel` selects the model used by Pause & Think and optional post-conversation reasoning.
- `postConvoForceThinking` uses that thinking model for post-conversation work when appropriate.

Always select exact model IDs from the account-aware supported-model response. Do not rely on a copied model list.

## Voice and language

Select the exact `agentVoice` from `/agent/voices`. Check `accountAvailability.available`, `languages`, `compatibleS2SEngines`, and `supportsStandardTts` before saving it.

- `agentS2SEngine: null` uses separate speech recognition and synthesis. Configure `agentSttEngine`, `agentTtsEngine`, and `agentVoice` for this mode.
- `agentS2SEngine: "openai"` or `"gemini"` enables the corresponding speech-to-speech mode. Use only a compatible voice and language returned by discovery.
- `agentLang` is the Vida language mode. Follow the OpenAPI enum and the selected voice's advertised languages.

Do not migrate the frontend's hard-coded catalog or invent voice IDs. The API catalog is the integration source of truth.

## Phone and SIP setup

An Agent configuration defines conversation behavior; phone-number or SIP setup connects that agent to telephony. Complete only the path the user needs, and verify account eligibility in OpenAPI before changing anything because provider and number-management operations may require reseller, partner, or developer access.

For a Vida-managed phone number:

1. Read `GET /api/v2/numberingProviders` and confirm the organization has an appropriate provider. Reseller or partner administrators can add or update one with `POST` or `PUT /api/v2/numberingProvider?targetOrganizationId=...` using the provider's documented configuration fields.
2. Search available numbers with one of `/api/v2/phoneNumber/search/local/locality`, `/phrase`, or `/prefix`, including `targetAccountId` for the agent account.
3. Present the exact number and any expected purchase or recurring impact to the user. Assign it only with explicit approval using `POST /api/v2/phoneNumber/assign?targetAccountId=...`.
4. For an already-owned number, use `POST /api/v2/phoneNumber/byo/assign?targetAccountId=...` instead of purchasing another number.
5. Verify assignment with `GET /api/v2/phoneNumbers?targetAccountId=...` and run an authorized inbound or outbound test. Returning a number with `POST /api/v2/phoneNumber/return` disconnects it and requires explicit confirmation.

For high-volume outbound Task workflows, Vida can optionally configure a managed pool of assigned
numbers for the organization. This requires contacting Vida; there is no public self-service pool
management API. After enablement, verify the Agent's assigned inventory with
`GET /api/v2/phoneNumbers?targetAccountId=...` and test representative call or text Tasks before
increasing volume.

For SIP connectivity:

Choose the topology first; these resources are not interchangeable:

- **Agent registration to an external PBX:** check the address with
  `POST /api/v2/sip/registration/available?targetAccountId=...`, create or update it with
  `POST /api/v2/sip/registration?targetAccountId=...`, then verify it with
  `GET /api/v2/sip/registration?targetAccountId=...` and representative inbound/outbound calls.
- **Direct inbound SIP to Vida:** read `GET /api/v2/sip/ipWhitelist?targetAccountId=...`, then add
  each approved source signaling IP with `POST /api/v2/sip/ipWhitelist?targetAccountId=...`.
  Re-read the list and test the Agent's SIP URI from an allowed source.
- **Direct outbound SIP from Vida:** read `GET /api/v2/sip/outboundRoutes?targetAccountId=...`, add
  the exact approved destination with `POST /api/v2/sip/outboundRoutes?targetAccountId=...`, then
  re-read and place a representative outbound call.

Follow OpenAPI for registration address, authentication, proxy, port, transport, and subscription
fields, and for the exact whitelist/route payloads. IP allowlist and outbound-route operations require
developer API access. Do not configure both a registration and a direct route unless the intended
PBX topology needs both. Deleting a registration, whitelist entry, or outbound route can interrupt
calls; require explicit confirmation and verify the resulting state.

## Functions

Read `/agent/functions` before editing `actions`.

- Store the returned `name` exactly in `actions[].name`.
- Check `allowed` and resolve `missingRequirement` before publishing.
- Use `placeholder` and the function's `docsPage` to write focused `instructions`.
- `limit` is the maximum supported instances when present.
- `hasSettings` means the function also uses related root-level configuration.

For a stable operation that is not already a built-in function, create and verify an exact helper
on a provisioned Computer Agent. Use `@computer_function(...)` for API, file, or data work that does
not need Browser access, and `@browser_function(...)` only when the helper requires the live Browser.
Configure the exact `computer` action returned by the catalog and map conversation values to the
registered helper's exact argument names. A Computer Agent uses its own Computer automatically; set
`computerDelegateAccountId` only when it must use another Agent's Computer. The `browser` action is
for ad hoc live-Browser work, not registered helpers. Use ordinary Computer delegation for novel or
multi-step work rather than forcing it into one helper.

The API intentionally does not add function-specific validation beyond the current Agent update behavior. Use the function guide and current configuration shape; do not infer unsupported fields.

Root-level relationships include transfer confirmation/monitoring/attended-transfer controls, recording notice settings, speech timing, the thinking model for Pause & Think, and typed reporting fields. Read the OpenAPI `AgentConfigurationWrite` schema for the complete approved writable set.

## Apps

Use the app lifecycle API to discover and prepare an app before assigning it to an agent:

- `GET /api/v2/apps?targetAccountId=...`
- `GET /api/v2/apps/{appId}/{appVersion}?targetAccountId=...`
- `POST /api/v2/apps/{appId}/{appVersion}?targetAccountId=...`
- `PUT /api/v2/apps/{appId}/{appVersion}?targetAccountId=...`
- `DELETE /api/v2/apps/{appId}/{appVersion}?targetAccountId=...`

Read dependency/setup state first, make the smallest change, and re-read it. Then assign the app in staging with `apps[]` using its exact `appId`, `version`, instructions, and enabled state. Test before publishing. Do not use internal app execution routes as a setup API.

## Reporting fields

`reportingFields` contains agent-authored typed fields. Each field has a stable `key`, display `label`, precise `instructions`, and `values.kind` of `boolean`, `choices`, `number`, or `text`. A choices field also supplies `values.choices`.

Define when a result is `null`; do not turn unknown or inconclusive outcomes into `false`. Reads may include `effectiveReportingFields`, the final reseller → organization → agent merge. Each effective field reports its winning `source`. Treat that list as read-only; write only the agent's own `reportingFields`.

## Saved versions

Use the live `agentConfigId` in saved-version paths:

- `GET /api/v2/agent/{agentConfigId}/versions`
- `POST /api/v2/agent/{agentConfigId}/versions`
- `POST /api/v2/agent/{agentConfigId}/versions/{versionId}`
- `DELETE /api/v2/agent/{agentConfigId}/versions/{versionId}`
- `POST /api/v2/agent/{agentConfigId}/versions/{versionId}/restore`
- `PUT /api/v2/agent/{agentConfigId}/versions/{versionId}/title`

A new version snapshots staging by default; use the documented `source` value when saving live instead. Replacing changes the named snapshot, not staging or live. Restore targets staging by default; publish afterward if the restored configuration should become live. A version referenced by an active experiment or Task may not be deletable.

## Experiments

Experiments distribute new work deterministically across saved versions of one live agent configuration. Use `agentConfigId` consistently:

- `GET /api/v2/experiments?targetAccountId=...&agentConfigId=...`
- `POST /api/v2/experiments?targetAccountId=...`
- `GET /api/v2/experiments/{experimentId}?targetAccountId=...`
- `PUT /api/v2/experiments/{experimentId}?targetAccountId=...`
- `POST /api/v2/experiments/{experimentId}/status?targetAccountId=...`
- `DELETE /api/v2/experiments/{experimentId}?targetAccountId=...`

Create candidate saved versions first. Each variant uses a numeric `versionId` and positive `weight`, with at least two distinct versions. Variants can change only while draft. Only one experiment may be active for the agent configuration. Pause or end it before deletion. Preserve the same reporting-field definitions across variants and report sample size and denominator with every comparison.

Define the experiment's hypothesis, primary metric, denominator, and guardrails before activation.
Where practical, change one behavior at a time between candidate versions. Establish a baseline and
verify that every variant emits the same measurement fields before routing live work. Compare only
like-for-like populations and time ranges, use event counts with metric values, and avoid declaring a
winner from small or operationally different samples. Conversation and Task-attempt logs retain
`experiments.id`, `experiments.variant`, and `experiments.versionId`; use those fields to inspect and
filter variant results through the Logs and time-series APIs.

## Completion evidence

For a configuration change, record:

- `targetAccountId`
- staging and live `agentConfigId` values used
- exact fields changed
- staging re-read evidence
- publish response, if published
- live re-read evidence
- any saved `versionId` or `experimentId`

An accepted write is not verification. Do not claim the live agent changed until the live read proves it.

For a complete account-through-production sequence, use
`https://vida.io/docs/api-reference/cookbooks/launch-an-agent` with this reference and current
OpenAPI schemas.
