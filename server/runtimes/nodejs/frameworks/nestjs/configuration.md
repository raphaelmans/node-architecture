# NestJS Configuration

> Retain NestJS configuration and dependency-injection facilities at the application boundary while keeping inward application code independent of Nest and external variable names.

Apply the [server configuration contract](../../../../core/configuration.md). In a workspace, the deployable NestJS application owns the schemas and composition; reusable packages receive normalized options or ports.

## Framework Boundary

Nest's configuration module is the outer adapter for host-injected environment values:

```text
host/process environment
  -> app-owned executable ServerRuntimeConfig schema
  -> Nest configuration/bootstrap boundary
  -> focused namespace or provider options
  -> Nest provider / plain application dependency
```

Use the installed Nest version's native module initialization, validation, namespaced configuration, typed injection, lifecycle, and testing support. Retrieve current official documentation before choosing exact APIs or module options.

The environment adapter validates only fields declared by the deployable application. Unrelated ambient variables remain available to Nest, Node.js, the host, or tooling and do not enter the validated application result.

## Validate and Materialize

Validate required `ServerRuntimeConfig` before the Nest application accepts dependent traffic or starts dependent work. Normalize external strings and names into application-facing values once at this boundary.

Optional integrations use explicit configuration modes. Enabling a provider requires its complete configuration; unrelated missing variables do not silently enable or disable it.

Validation errors name the missing/invalid field and expected shape without printing the supplied value. Do not log the full Nest configuration store.

## Dependency Injection

Use framework-native DI at the outer layer without leaking generic configuration lookup inward:

```text
ServerRuntimeConfig.databaseUrl
  -> DatabaseConfig { connectionString }
  -> database provider factory
  -> repository adapter
  -> application port
```

Framework adapters, infrastructure modules, and application composition modules may inject typed, focused configuration namespaces or provider options. Framework-neutral controllers, services/use cases intended to remain portable, domain objects, contracts, and package-owned ports receive constructor/factory arguments with normalized values; they do not import Nest configuration types or call a string-keyed configuration service.

When a reusable Nest integration is packaged as a dynamic module, the consuming deployable supplies normalized options. The reusable module does not read `process.env` or own the application's external variable names.

## NestJS with a React Application

Treat NestJS and a standalone React client as separate deployables:

```text
React deployable
  -> BrowserBuildConfig
  -> optional BrowserRuntimeConfig

NestJS deployable
  -> ServerRuntimeConfig
```

The React application never imports or receives the Nest server environment. If the browser requires runtime-delivered public configuration, an explicit public resource projects only approved values and follows the client runtime-config contract.

## Schema and Example Contract

- The executable server schema is authoritative.
- The Nest deployable's `.env.example` is a checked, human- or agent-authored projection with safe placeholders.
- Unknown ambient variables are permitted and excluded from normalized configuration.
- Reusable packages do not contribute environment files or a shared root schema.

## Tests

- Unit-test schema valid, missing, malformed, optional, and conditional cases.
- Test focused provider factories with normalized configuration values.
- Use Nest's testing facilities for module/composition integration.
- Verify bootstrap rejects invalid required configuration before dependent traffic/work.
- Verify portable application services with plain constructor/factory inputs rather than a Nest configuration container.

## Official References

- [NestJS Configuration](https://docs.nestjs.com/techniques/configuration)
- [NestJS Custom Providers](https://docs.nestjs.com/fundamentals/custom-providers)
- [NestJS Dynamic Modules](https://docs.nestjs.com/fundamentals/dynamic-modules)
- [NestJS Testing](https://docs.nestjs.com/fundamentals/testing)

These references define the selected framework mechanism. Derive exact APIs and module options from the installed NestJS version.
