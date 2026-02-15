# Endpoint Naming (tRPC + OpenAPI)

> Naming rules for procedure/endpoint clarity and migration-safe mapping.

## Goal

Keep naming predictable across transports so migrations do not rename business capabilities.

## Naming Policy

- Business capability name is canonical (for example `profile.create`, `profile.update`)
- tRPC and OpenAPI names map to the same capability
- Favor explicit action names over vague verbs

## tRPC Naming

Use namespaced procedure names by module.

- Router namespace: `<module>`
- Procedure: `<action>`
- Combined capability identity: `<module>.<action>`

Examples:

- `profile.getById`
- `profile.list`
- `profile.create`
- `profile.update`

## OpenAPI Naming

Use resource-oriented paths and standard HTTP methods.

- Collection create: `POST /profiles`
- Single get: `GET /profiles/{profileId}`
- Update: `PATCH /profiles/{profileId}`
- List/filter: `GET /profiles`

Operation IDs should map cleanly to capability names.

Examples:

- `operationId: profileCreate`
- `operationId: profileGetById`
- `operationId: profileUpdate`

## Capability Mapping Table

| Capability | tRPC | OpenAPI |
| --- | --- | --- |
| Create profile | `profile.create` | `POST /profiles` (`profileCreate`) |
| Get profile | `profile.getById` | `GET /profiles/{profileId}` (`profileGetById`) |
| Update profile | `profile.update` | `PATCH /profiles/{profileId}` (`profileUpdate`) |

## Orchestration Rule Example (Profile)

Create profile requires user identity enrichment via another service, so it uses a use case.

```text
Create Profile (complex orchestration)

transport adapter (tRPC or OpenAPI)
  -> CreateProfileUseCase
      -> UserService (resolve/validate user.userId)
      -> ProfileService
          -> ProfileRepository
```

Update profile is a single-service write, so it can call service directly.

```text
Update Profile (single-service write)

transport adapter (tRPC or OpenAPI)
  -> ProfileService
      -> ProfileRepository
```

## References

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- Operation Object: https://spec.openapis.org/oas/latest.html#operation-object
- Paths Object: https://spec.openapis.org/oas/latest.html#paths-object
