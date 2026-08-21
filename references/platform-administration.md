# Platform Administration

Read this reference when onboarding customer accounts, managing optional reseller or partner
capabilities, applying Agent templates, configuring member access, connecting inbound email or
webhooks, or managing white-label domains. The live OpenAPI at
`https://vida.io/docs/apiv2.json` remains authoritative for exact request and response schemas.

## Start from the actual account type

Not every customer has every hierarchy level.

- Most customers have an organization with child Agent accounts.
- A reseller is optional and manages downstream customer organizations.
- A partner is optional and manages downstream resellers.
- An Agent account owns one Agent's configuration, Tasks, communications, and optional Computer
  Agent resources.

Read `GET /api/v2/account` first. Never invent a reseller or partner layer for an ordinary
organization. Use reseller templates, white-label domains, downstream feature assignment, or
partner reseller settings only when the authenticated account is eligible for that operation.

## Identity and scope

- `targetAccountId` selects an authorized account for a request.
- `targetOrganizationId`, `targetResellerId`, and `targetPartnerId` are used only where the endpoint
  explicitly selects that hierarchy level.
- `accountId` owns a Task and normally identifies an Agent account.
- `agentConfigId` identifies staging, live, or saved Agent configuration. It is not an account ID.
- `externalAccountId` and `externalBillingId` are caller-owned correlations; preserve returned Vida
  IDs as the authoritative resource identifiers.

After account creation, read the resource and its parent relationship before continuing. Do not
claim success from a create response when the account may have been selected under the wrong parent.

## Customer onboarding

For a normal organization:

1. Read the organization and current product access.
2. List current Agent accounts with `GET /api/v2/listAccounts?targetOrganizationId=...`.
3. Create only approved Agent accounts with `POST /api/v2/createAccount`.
4. Discover the selected account's models, voices, functions, Apps, and entitlements.
5. Configure staging, verify it, test it, publish with explicit intent, and verify live state.
6. Connect only the required telephony, messaging, email, or Computer resources.
7. Verify a representative end-to-end interaction.

For an eligible reseller, create or resolve the downstream organization first, then run the same
Agent-account flow inside it. For an eligible partner, create or resolve the reseller first. Account,
plan, number, and Computer creation can affect billing; present impact before an unapproved write.

Read `GET /api/v2/features` before promising a capability. Partner and reseller administrators may
assign only features already granted to their own scope through `POST /api/v2/features/assign`.
Feature creation and internal enablement are not public APIs; contact Vida when required access is
not available.

## Reporting defaults

`POST /api/v2/account` supports these documented account settings:

- `settings.reportingFields` at reseller or organization level;
- `settings.metrics` for an organization dashboard;
- `settings.defaultOrgSettings.metrics` for reseller defaults on new organizations.

These arrays replace the current array at the supplied path. Read, preserve unrelated entries,
write the complete intended array, and re-read. Agent-level reporting fields remain part of Agent
staging and publish.

## Stripe and Chargebee billing providers

Billing-provider configuration is optional and applies only to eligible reseller or partner
accounts that bill downstream customers. Do not configure it for an ordinary organization.

1. Read `GET /api/v2/account?targetAccountId=...` and confirm the exact reseller or partner account
   that should own the connection.
2. Read `GET /api/v2/billing/billingSystemConfig?targetAccountId=...`. A `404` means no provider is
   configured. Returned credential values are redacted presence indicators and cannot be reused.
3. Complete the provider-side setup in the Stripe or Chargebee guide, including the account-scoped
   webhook URL and customer-facing plan mappings.
4. Write the complete provider configuration with
   `POST /api/v2/billing/billingSystemConfig?targetAccountId=...`.
5. Re-read the configuration, then verify a representative checkout and subscription in both the
   provider and Vida.

Stripe writes require `billingSystemType`, `apiKey`, `publishableKey`, and `webhookSigningKey`.
Chargebee writes require `billingSystemType`, `apiKey`, `publishableKey`, `site`,
`webhookUsername`, and `webhookPassword`. A POST replaces the complete stored configuration; never
combine new values with redacted values returned by GET. Use only fields declared by the current
OpenAPI operation.

Provider setup guides:

- Stripe: `https://vida.io/docs/billing/stripe`
- Chargebee: `https://vida.io/docs/billing/chargebee`
- API workflow: `https://vida.io/docs/api-reference/platform-guides/billing-providers`

## Reseller Agent templates

Templates are optional reseller resources. Ordinary organizations configure Agents directly.

1. Create a disabled draft with `POST /api/v2/templates/createTemplate`.
2. Read and update it through `/api/v2/templates/{templateId}`.
3. Test its Agent configuration, fields, and integrations before enabling it.
4. Apply it with `POST /api/v2/createAgentFromTemplate` to the exact Agent account.
5. Re-read staging and live configuration and test the resulting Agent.

Template fleet migrations must start with `dryRun:true`. Inspect queued migration status, limit
`sectionsToMigrate`, and do not overwrite customer overrides without explicit approval. Detaching
an Agent preserves its current authored configuration but removes template ownership restrictions.

## Members and credentials

- Read members before inviting, changing, or deleting access.
- Use `permittedAccountIds` for constrained child-account access.
- Do not remove the current administrator's last viable access.
- Rotate API tokens by creating and verifying the replacement before revoking the current token.
- Generate one-time authentication tokens only from a trusted backend after verifying the signed-in
  user's customer membership.

## Inbound email

Inbound email belongs to the selected Agent account:

1. Read `GET /api/v2/email/inboundPolicy` and the current allowlist.
2. Add approved senders before selecting `allowlist` mode.
3. Use `open` only when any sender should be accepted.
4. Re-read policy and allowlist, then send a representative authorized test email.

Removing a sender affects delivery only while the policy uses `allowlist`.

## Webhooks and relays

Event webhooks send Vida events to your system. Webhook relays forward supported inbound provider
events through your application before Vida processes them. Do not substitute one for the other.

Event webhook types are `conversation`, `incoming`, `contact`, `agent`, and `onboarding`. Vida sends
JSON plus `X-Vida-Event`, `X-Vida-Timestamp`, `X-Vida-Signature-Version`, and `X-Vida-Signature`.
Return success quickly and process longer work asynchronously. HTTP 410 may permanently remove a
destination, so use it only for a retired endpoint.

For relays, list supported types, read the current type configuration, update one HTTPS destination,
re-read it, and send a safe provider test. Confirm a replacement path before deletion.

## White-label domains and embed

White-label domains and embedded application access are optional reseller capabilities.

1. Read `GET /api/v2/domains`.
2. Register with `POST /api/v2/domain` only after completing the supplied domain setup.
3. Re-read, set the default with `POST /api/v2/domain/default`, and verify it.
4. The current default cannot be removed. Select another default first, then call
   `DELETE /api/v2/domain` with the exact registered domain in the `domain` query parameter.
5. Verify DNS, HTTPS, login, and customer navigation in the actual domain.

For embed access, resolve the customer organization, verify the signed-in user in the caller's own
system, generate a one-time auth token from a trusted backend, and load
`https://<vida-domain>/app/embed` with URL-encoded `authToken` and `email`. Never expose the
long-lived Vida API token in browser code. Treat onboarding prefill query values as draft inputs and
verify the resulting account and Agent.

## Outbound number pools

A managed outbound number pool is an optional organization capability for approved call or text
Task workflows. Vida must enable and configure it. Do not use internal pool-management routes or
claim it is self-service. After Vida enables it, verify assigned number inventory with
`GET /api/v2/phoneNumbers?targetAccountId=...` and run a representative Task before scaling volume.

## Completion evidence

Record the authenticated account type, selected parent and target IDs, created or changed resource
IDs, post-write reads, and one representative capability test. Accepted writes and queued operations
are not completion evidence.
