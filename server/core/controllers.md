# Framework-Neutral Controllers

> Canonical inbound application boundary between framework adapters and use cases/services.

## Purpose

Controllers keep framework and transport code replaceable without moving public-contract mapping into domain services.

```text
Next.js route | Express/Hono handler | tRPC procedure | other adapter
                         |
                         v
              framework-neutral controller
                         |
                         v
                 use case OR service
                         |
                         v
              repository/provider port
```

A controller is not a Next.js route, tRPC procedure, Express/Hono handler, or Nest controller decorator. Those are **framework adapters**. A canonical controller is a plain TypeScript module owned by a domain module.

Every externally exposed application-owned HTTP/RPC capability MUST enter application code through a framework-neutral controller. Internal workers may call a use case/service directly when they are not presenting the same public capability; reuse the controller when they intentionally reuse that public input/output boundary.

## Provider-Managed Endpoints

A selected authentication provider's native protocol and enabled plugin endpoints may be mounted through its documented handler. The provider owns their wire format, cookies, redirects, and lifecycle; do not recreate these endpoints as application controllers or rewrite them into the business API envelope. [Better Auth](../runtime/nodejs/libraries/better-auth/README.md) is a concrete mapping of this boundary.

This exception is limited to provider-managed behavior. Custom business operations, including those that call an auth provider, still use application controllers and protected services/use cases. Required application restrictions must also hold on directly reachable provider endpoints through supported configuration/hooks or an explicitly restricted exposure design; a stricter application wrapper does not secure an unrestricted native route. Provider hooks adapt to focused application operations without leaking provider types inward, and their transaction guarantees must be verified separately.

## Responsibilities

| Boundary | Owns |
| --- | --- |
| Framework adapter | Framework request/context types, body/header/cookie extraction, authentication, rate limiting, observability scope, shared input parsing, response envelope/status, central transport error mapping |
| Controller | Shared input to command mapping, plain actor/application metadata mapping, one use-case-or-service call, null-to-domain-error decisions, application result to shared response mapping |
| Use case | Multi-service workflow, transaction boundary, side-effect/outbox coordination |
| Service | Single-domain rules and self-contained read/write behavior |

Controllers MUST:

- use plain TypeScript inputs and outputs;
- accept types inferred from module-owned shared contracts;
- depend on interfaces for the use case or service they call;
- call exactly one use case or one service per operation;
- map internal entities/results to the shared public response shape;
- throw typed `AppError` subclasses for expected failures;
- remain reusable from every transport adapter.

Controllers MUST NOT:

- import Next.js, tRPC, Express, Hono, NestJS, OpenAPI adapter, or Node.js request/response types;
- read headers, cookies, environment variables, or framework context;
- choose HTTP status codes or construct transport envelopes;
- map errors to `TRPCError`, `NextResponse`, or another framework error;
- access repositories, databases, or vendor SDKs directly;
- orchestrate multiple services (create a use case instead);
- receive `requestId`, `traceId`, `spanId`, a transaction, or a service locator as a generic context object.

## Canonical Controller Shape

```typescript
// modules/user/controllers/create-user.controller.ts

import type {
  CreateUserInput,
  CreateUserResponse,
} from "../shared/contracts";
import type { Actor } from "@/shared/kernel/auth";
import type { ICreateUserUseCase } from "../use-cases/create-user.use-case";

export interface ICreateUserController {
  execute(input: CreateUserInput, actor: Actor): Promise<CreateUserResponse>;
}

export class CreateUserController implements ICreateUserController {
  constructor(
    private readonly createUser: ICreateUserUseCase,
  ) {}

  async execute(
    input: CreateUserInput,
    actor: Actor,
  ): Promise<CreateUserResponse> {
    const user = await this.createUser.execute({
      email: input.email,
      name: input.name,
      createdBy: actor.userId,
    });

    return {
      id: user.id,
      email: user.email,
      name: user.name,
      createdAt: user.createdAt.toISOString(),
    };
  }
}
```

For a simple read or single-service write, the controller depends directly on one service interface:

```typescript
export class GetUserController implements IGetUserController {
  constructor(private readonly users: IUserService) {}

  async execute(input: GetUserInput): Promise<GetUserResponse> {
    const user = await this.users.findById(input.id);
    if (!user) throw new UserNotFoundError(input.id);
    return toGetUserResponse(user);
  }
}
```

The controller is still useful on the simple path: it owns the public boundary mapping and null-to-domain-error decision while the service remains reusable internally.

## Framework Adapter Examples

Every adapter reuses the same controller. The examples below show two transports; Express and Hono follow the same boundary in their runtime guides.

```typescript
// Next.js adapter: app/api/users/route.ts
export async function POST(request: Request) {
  return withRequestObservability(request, async ({ requestId }) => {
    try {
      const body = await parseJsonRequestBody(request);
      const input = parseRequestInput(CreateUserInputSchema, body);
      const actor = await authenticateNextRequest(request);
      const result = await makeCreateUserController().execute(input, actor);
      const response = CreateUserResponseSchema.parse(result);
      return NextResponse.json({ data: response }, { status: 201 });
    } catch (error) {
      const { status, body } = handleError(error, requestId);
      return NextResponse.json(body, { status });
    }
  });
}
```

```typescript
// tRPC adapter: modules/user/user.router.ts
export const userRouter = router({
  create: protectedProcedure
    .input(CreateUserInputSchema)
    .mutation(async ({ input, ctx }) => {
      return makeCreateUserController().execute(
        input,
        toActor(ctx.session),
      );
    }),
});
```

The adapters may have different framework mechanics, but they do not duplicate command mapping, null handling, or public result mapping.

## Factory Pattern

Factories construct the controller and its complete inward dependency graph.

```typescript
// modules/user/factories/create-user.factory.ts
export function makeCreateUserController(): ICreateUserController {
  return new CreateUserController(
    makeCreateUserUseCase(),
  );
}

function makeCreateUserUseCase(): ICreateUserUseCase {
  return new CreateUserUseCase(
    makeUserService(),
    makeWorkspaceService(),
    getContainer().transactionManager,
    getContainer().appLogger,
    getContainer().productAnalytics,
  );
}
```

Framework adapters call controller factories only. They do not select or construct a service/use case themselves.

## Validation and Response Rules

- The framework adapter parses untrusted input with the canonical shared Zod schema.
- The controller accepts the inferred input type; it does not accept a framework request.
- The controller returns the shared response shape after mapping internal values such as `Date` to wire values such as ISO strings.
- The framework adapter parses the result with the canonical response schema before serialization. This is a runtime contract-drift guard.
- When two transports expose one capability, parity tests exercise both adapters against the same controller and contracts.
- When a capability requires a transport effect such as setting a session cookie, the controller may return a transport-neutral delivery intent alongside the shared response (for example `{ response, session: { token } }`). The adapter performs the actual cookie/header mutation; the controller never imports that framework API.

## Error Rules

- Services may return `null` where absence is an internal result.
- The controller converts capability-level absence into a domain-specific `NotFoundError` when the public capability requires it.
- Known application errors bubble unchanged to shared transport mapping.
- Framework adapters never repeat per-route domain-error translation.
- Unknown errors are logged and sanitized at the transport boundary.

## Observability and Transactions

Controllers receive neither observability nor transaction context by default.

- Request/trace correlation propagates through the active async observability scope.
- The injected `AppLogger` adapter reads that scope where logs are emitted.
- Transactions are owned by a service or use case and travel only through `TransactionOptions`.
- A controller may receive `AppLogger` only when it owns a meaningful operational boundary event; routine request lifecycle logging remains in the framework adapter.

## Testing

Test the boundaries independently:

| Test | Replace | Assert |
| --- | --- | --- |
| Framework adapter | Controller factory/controller port | Request extraction, shared input parsing, authentication/rate limit wiring, envelope/status, central error integration |
| Controller | Use-case or service interface | Input-to-command mapping, actor mapping, null-to-error behavior, exactly one downstream call, public response mapping |
| Use case | Service/provider ports | Orchestration, transaction ownership, side-effect timing |
| Service | Repository/provider ports | Domain rules and transaction participation |

Controller tests contain no framework request/context objects. Adapter tests contain no domain behavior assertions.

## Folder Structure

```text
src/lib/modules/<module>/
  controllers/
    <capability>.controller.ts
  factories/
    <capability>.factory.ts
  use-cases/                 # optional per capability
  services/
  repositories/
  shared/contracts/

src/app/api/<resource>/route.ts       # Next.js option
src/routes/<resource>.express.ts      # Express option
src/routes/<resource>.hono.ts         # Hono option
```

Use capability-based controller names such as `CreateUserController`, `GetUserController`, and `ListUsersController`. Avoid one large module controller whose dependencies grow with every endpoint.

## Checklist

- [ ] Framework adapter calls a controller factory, never a service/use-case factory
- [ ] Controller imports no framework or transport types
- [ ] Controller accepts shared input types and plain application types only
- [ ] Controller calls exactly one use case or service
- [ ] Controller maps internal result to shared response shape
- [ ] Controller turns capability-level null outcomes into typed domain errors
- [ ] Adapter validates the shared response schema before serialization
- [ ] Adapter and controller have separate tests
- [ ] Dual transports have parity tests
