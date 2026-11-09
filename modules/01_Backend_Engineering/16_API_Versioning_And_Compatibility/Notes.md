# Topic 16 — API Versioning and Compatibility

## 1. Why API versioning exists

An API is a contract between a provider and its clients.

Clients may include:

- web frontends;
- mobile applications;
- partner systems;
- internal services;
- CLI tools;
- third-party integrations.

The provider may need to change the API, but existing clients may still depend on the old behavior. Versioning provides a controlled way to evolve the contract without unexpectedly breaking those clients.

~~~text
Existing clients → continue using a compatible contract
New clients     → adopt the improved contract
~~~

## 2. What is a breaking API change?

A breaking change can cause an existing valid client request to fail or change meaning.

Examples:

- removing an endpoint;
- renaming a response field;
- changing a field from a number to a string;
- making an optional request field required;
- changing the meaning of an existing status code;
- removing an accepted enum value;
- changing pagination behavior;
- changing authentication requirements;
- changing the meaning of an existing operation.

A change is not breaking merely because the implementation changed. The question is whether the documented external behavior changed for existing clients.

## 3. What is usually backward-compatible?

Commonly compatible changes include:

- adding a new optional request field;
- adding a new response field when clients ignore unknown fields;
- adding a new endpoint;
- adding a new optional query parameter;
- improving internal performance without changing the contract;
- adding a new response type only for a new endpoint.

Compatibility still depends on client behavior. Some fragile clients fail when unexpected response fields appear, so compatibility assumptions should be tested.

## 4. Common versioning strategies

### URL versioning

~~~text
/api/v1/products
/api/v2/products
~~~

Advantages:

- easy to understand;
- visible in logs and metrics;
- easy to route at a gateway;
- simple for clients to select.

Trade-off: URLs and route definitions multiply over time.

### Header versioning

~~~http
Accept: application/vnd.example.products.v2+json
~~~

Advantages:

- resource URLs remain stable;
- version is treated as representation metadata.

Trade-off: less visible during manual testing and more difficult to discover.

### Query-parameter versioning

~~~text
/products?version=2
~~~

Advantages:

- simple to implement and test.

Trade-off: version selection becomes part of the request parameters and can be inconsistently applied.

## 5. Versioning is different from deployment

Deploying new code does not automatically mean creating a new API version.

A new version is justified when the external contract must change incompatibly. Internal refactoring, query optimization, or moving code between layers does not require a new API version if observable behavior remains compatible.

## 6. Safe evolution without a new version

For a compatible change:

1. Add the new optional field or behavior.
2. Deploy code that supports both old and new clients.
3. Update documentation and client guidance.
4. Measure adoption and errors.
5. Deprecate the old behavior with a clear timeline.
6. Remove it only after the support period ends.

## 7. Safe evolution with a new version

For a breaking change:

1. Define the new contract.
2. Add a new version while keeping the old version available.
3. Implement and test both versions.
4. Migrate clients gradually.
5. Monitor traffic, errors, and latency by version.
6. Announce a deprecation date for the old version.
7. Remove the old version only after the agreed support period.

## 8. Database compatibility during API evolution

The API and database may be deployed at different times. During rolling deployments, old and new application instances can run simultaneously.

Use an expand-and-contract approach:

### Expand

- add new nullable schema;
- deploy code that can read old and new fields;
- dual-write if necessary;
- backfill existing data.

### Contract

- stop using the old field;
- verify that old application versions are gone;
- remove the old schema later.

The database must support both application versions during the transition.

## 9. Deprecation

Deprecation means an API remains available but clients are warned that it will be removed or replaced.

A useful deprecation plan includes:

- affected endpoint or field;
- replacement contract;
- migration instructions;
- deprecation date;
- removal date;
- traffic and client adoption monitoring;
- support contact or escalation path.

Deprecation should be observable through documentation, communication, and, where appropriate, response headers.

## 10. Compatibility testing

Compatibility tests should verify:

- old clients can still call the old contract;
- new clients can call the new contract;
- request validation remains correct;
- response schemas are stable;
- status codes and error formats remain compatible;
- authentication and authorization behavior is preserved;
- both old and new application versions work with the database during rollout.

## 11. Key mental model

Before changing an API, ask:

1. Is the change internal or externally observable?
2. Is it backward-compatible?
3. Can the contract evolve additively?
4. Do we need a new version?
5. How will old clients migrate?
6. How long will both versions be supported?
7. Can old and new application versions coexist during deployment?
8. How will we measure adoption and failures?

API versioning is a compatibility and migration strategy, not merely a number added to a URL.
