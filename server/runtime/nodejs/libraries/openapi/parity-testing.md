# OpenAPI Parity Testing (with Existing tRPC)

> Guardrails to prevent transport drift while both tRPC and OpenAPI are active.

## Goal

If one business capability is exposed through both transports, behavior must stay equivalent.

## What to Test

For each dual-exposed capability:

- Input validation parity (same accepted/rejected cases)
- Success contract parity (same business payload semantics)
- Error contract parity (same domain code/category semantics)
- Authorization/rate-limit boundary parity

## Test Shape

```text
fixtures (input)
  -> call tRPC procedure
  -> call OpenAPI endpoint
  -> normalize transport envelope
  -> assert business-level parity
```

## Fixture Sets (Required)

- `golden`: representative valid request
- `minimal`: smallest valid request
- `invalid-*`: explicit invalid contract cases
- `forbidden/unauthorized` where auth is required

## Recommended Assertion Levels

1. Domain outcome parity (primary)
2. Contract/error parity (secondary)
3. Transport-specific metadata parity only where required

## Example: Profile Create vs Update

```text
create profile parity
  fixture -> trpc.profile.create
          -> POST /profiles
          -> both must create equivalent profile record

update profile parity
  fixture -> trpc.profile.update
          -> PATCH /profiles/{profileId}
          -> both must update equivalent fields
```

## Rollout Gate

Before switching client traffic from tRPC to OpenAPI for a capability:

- parity tests pass in CI
- observability confirms equivalent failure/success rates
- fallback path to previous transport is documented
