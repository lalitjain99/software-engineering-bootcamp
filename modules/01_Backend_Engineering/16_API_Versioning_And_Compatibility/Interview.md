# Topic 16 — API Versioning and Compatibility Interview Guide

## 1. When does an API need a new version?

A new version is justified when the existing external contract must change incompatibly. Examples include:

- removing or renaming an existing field;
- changing a field's type or meaning;
- making an optional request field required;
- removing an endpoint or accepted enum value;
- changing authentication requirements;
- changing pagination or operation semantics in a way that existing clients cannot handle.

Internal refactoring, query optimization, or performance improvements do not require a new API version when the observable contract remains unchanged.

Do not create a new version for every small change. Versioning creates additional routing, documentation, testing, monitoring, support, and migration costs.

## 2. Is adding an optional response field breaking?

Usually, adding an optional response field is backward-compatible. Existing clients can continue reading the fields they already use, while new clients can use the additional field.

However, verify that clients tolerate unknown fields. Strict mobile models, generated SDKs, or rigid contract tests may reject unexpected response properties. An additive change can still be breaking for those clients.

Use the existing version when:

- existing fields retain their meaning;
- the new field is optional or additive;
- clients tolerate unknown fields;
- the change does not alter status codes or operation semantics.

## 3. How should a response field rename be handled?

A direct rename is breaking. A client that reads price will fail or receive no value if the server suddenly returns only unit_price.

Preferred migration:

1. Return both price and unit_price with the same value.
2. Update clients to read unit_price, with a temporary fallback to price if needed.
3. Announce the deprecation of price and provide a migration timeline.
4. Monitor remaining usage of price.
5. Remove price only after client migration is complete.

This is an expand-migrate-observe-contract sequence.

Create a new API version when:

- the old and new fields have different semantics;
- both fields cannot safely coexist;
- the rename is part of several breaking changes;
- a clean long-term contract is more valuable than a temporary compatibility period.

## 4. Which versioning strategy would you choose for public APIs?

For mobile clients, partner integrations, and internal services, URL-path versioning is usually the most practical major-version mechanism:

    /v1/products/{id}
    /v2/products/{id}

Advantages:

- visible in logs, traces, dashboards, and browser requests;
- simple gateway and router rules;
- easy documentation and manual testing;
- clear client choice of supported version;
- straightforward traffic and error metrics by version.

Header versioning keeps URLs stable and treats the version as representation metadata, but it is less visible and can be harder for partners to configure correctly.

Query-parameter versioning is simple, but clients may apply it inconsistently and it can be less clear in routing and documentation.

A useful rule is to make major versions rare and prefer additive changes within an existing major version.

## 5. How would you deprecate an old API version?

Do not remove an old version immediately. Use a controlled deprecation process.

### Communication

- announce the replacement version and migration guide;
- state the deprecation and final shutdown dates;
- explain field, authentication, and behavior differences;
- contact important partners directly rather than relying only on documentation.

### Identification and monitoring

Track the remaining v1 usage by:

- API key, OAuth client ID, or partner ID;
- endpoint and operation;
- request volume and unique active clients;
- last-seen timestamp;
- status codes and errors;
- SDK or User-Agent information.

API keys and OAuth client IDs are better client identifiers than source IPs because NAT, proxies, and shared infrastructure can obscure the real caller.

### Migration support

- provide a migration guide and field mapping;
- provide a sandbox or staging environment;
- offer migration assistance for blocked partners;
- use a compatibility shim when a temporary translation layer is practical.

### Final shutdown

Before shutdown, verify that usage is zero or that all remaining clients have an approved migration exception. For a removed endpoint, return HTTP 410 Gone with a useful migration message rather than silently returning 404.

After shutdown, remove legacy routes, schemas, adapters, tests, and documentation so the old contract does not remain as permanent technical debt.

## 6. What if an important partner still generates 20% of v1 traffic?

Do not shut down v1 blindly. Treat this as a risk-managed exception.

1. Confirm the traffic using authenticated client IDs.
2. Identify the partner's business dependency and migration blocker.
3. Involve product, account, customer-success, and engineering stakeholders.
4. Provide technical migration support.
5. Grant only a time-bounded extension with a hard final date.
6. Monitor that partner's v1 traffic daily.

Possible mitigations include:

- a scoped API-key exception;
- a temporary gateway compatibility shim that translates v1 to v2;
- white-glove engineering support;
- a short extension while the partner completes migration.

Do not use an indefinite extension. The exception should have an owner, deadline, monitoring, and a documented removal plan.

## 7. How should shared business rules work across API versions?

If discontinued products must not be returned by either v1 or v2, the rule belongs in the shared service layer because it is business behavior, not presentation behavior.

The service can raise a domain exception such as ProductDiscontinuedError. Each router translates that exception into the agreed HTTP response for its version.

Test at two levels:

- a service test verifies the business rule once;
- v1 and v2 router tests verify that each public contract exposes the rule correctly.

This avoids duplicating business logic while preserving version-specific response schemas.

## 8. How should API and database changes coexist during rolling deployment?

Use expand and contract so old and new application instances can run simultaneously.

### Expand

- add the new column as nullable or with a safe default;
- ensure old application instances can continue writing and reading;
- deploy new code that handles null or old data safely.

### Migrate and backfill

- populate existing records in controlled batches when required;
- allow new code to read both old and new representations during transition;
- monitor errors, locks, latency, and backfill progress.

### Contract

After all old instances are gone and data is ready:

- enforce stricter constraints such as NOT NULL;
- remove fallback code;
- remove old columns or adapters in a later migration.

Never immediately drop or rename a column while old instances may still reference it.

## 9. How do you decide whether an additive change is truly safe?

Check more than the schema diff:

- do clients reject unknown response fields?
- do generated SDKs need regeneration?
- do contract tests expect an exact response shape?
- does the field change payload size or latency materially?
- does caching vary by version or representation?
- does the new field expose sensitive information?
- do clients depend on field ordering or undocumented behavior?

Backward compatibility is an observed client property, not merely an assumption based on the server schema.

## 10. What should be monitored during a version migration?

Track each version separately:

- request rate and unique clients;
- p50, p95, and p99 latency;
- 4xx and 5xx rates;
- validation and authentication failures;
- downstream dependency failures;
- response size and timeout rate;
- migration adoption by client;
- remaining v1 traffic and last-seen clients.

Metrics should be segmented by authenticated client identity where possible. Logs and traces should include the API version, route, client identifier, and correlation ID while redacting credentials and sensitive data.

## Common mistakes

- creating a new version for every optional field;
- renaming fields directly in an existing version;
- removing v1 based only on total traffic falling;
- identifying clients only by source IP;
- relying only on email communication for deprecation;
- using an indefinite partner exception;
- putting version-specific business rules in routers;
- dropping database columns during a rolling deployment;
- assuming additive response fields are safe without checking clients;
- keeping legacy code forever after migration is complete.

## Interview summary

When explaining API evolution, use this sequence:

    classify the change
        ↓
    assess client compatibility
        ↓
    choose additive evolution or a new version
        ↓
    communicate and support migration
        ↓
    monitor adoption and failures
        ↓
    deprecate and remove safely