# AI SDK Integration Convention

Use when the Vercel AI SDK (`ai` and its `@ai-sdk/*` provider packages) is installed or explicitly selected. Apply [AI model, agent, and workflow boundaries](../../../../core/ai-boundaries.md) first. The AI SDK does not require Mastra, and Mastra does not replace this convention for direct model calls.

## Ownership

| Concern | Owner |
| --- | --- |
| Provider client, credentials, retries | Deployable composition, from validated application configuration |
| Model request and response handling | One model gateway adapter per provider |
| Prompt content, schemas, model choice, budgets, persistence of results | The owning module's service or use case |
| UI stream protocol | The framework-owned chat transport and the client's AI SDK UI integration |

## Model Gateway Adapter

Implement the deployable's shared model gateway port with the AI SDK. This adapter is the only module that imports the SDK or a provider package. Modules pass it their own prompts, schemas, and model choice.

- Create the provider from an injected credential. A missing credential fails at composition with a typed error rather than on the first call. Accept an injectable transport so tests and request hooks need no global patching.
- Expose only the call shapes the application uses. For structured generation, pass the caller's schema to the SDK's structured-output mechanism and return the validated value.
- The application module owns the Zod schema independently of provider or ORM types. Native validation can fulfill the contract when it applies that schema; distinguish rejected, fallback, and partial values rather than blindly parsing the same accepted object twice. Derive provider-compatible representations from the canonical schema and enforce checks the provider cannot represent.
- When the SDK reports that no valid object was produced, return the raw text, usage, and provider request identity as a rejected result so the caller can record it. Rethrow every other failure for translation.
- Return input and output token counts, whether they were actually reported, and provider metadata the application records, such as a request id or service tier. Do not leak SDK result types.
- Keep provider-specific options, such as reasoning effort or service tier, inside the adapter. They are provider configuration, not application vocabulary.
- Bound retries and parallel embedding calls explicitly; the SDK's defaults are not an application policy.

Keep each module's model identifiers in one configuration module that it owns, so a model change is one edit and is visible in review. The gateway adapter accepts the identifier; it does not decide it.

## Injecting a Model Into an Agent Framework

When an agent framework accepts an AI SDK model object, the composition root creates the provider and model and injects it. Agent and tool definitions receive the model as a parameter and never construct a provider. Tests inject a mock model.

A framework may instead offer native model routing configured at composition. Use the supported integration for the installed version; do not require an AI SDK model object solely to preserve a facade. Framework-owned agent loops, streaming, and memory remain native. The model gateway still owns direct model calls made by application services, and both paths must preserve output contracts and usage accounting.

## Streaming to a Client

When the server streams an agent or model response in the AI SDK's UI stream protocol, treat the route as a framework-owned transport: it keeps the protocol's wire format and is not wrapped in the business envelope. Pin the protocol version the client expects and change server and client together. On the client, the AI SDK UI integration is an auth-aware transport behind the feature boundary; conversation state it holds is not a second source of truth for application records.

## Verification and Sources

Test the adapter with an injected transport or mock model for a valid object, a rejected object, missing usage, a provider outage, and retry bounds. Test that no module outside the adapter and the composition root imports the SDK.

- [AI SDK documentation](https://ai-sdk.dev/docs/introduction)
- [Generating structured data](https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data)
- [Embeddings](https://ai-sdk.dev/docs/ai-sdk-core/embeddings)
- [Testing](https://ai-sdk.dev/docs/ai-sdk-core/testing)
- [Stream protocols](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)

Detect the installed `ai` and provider package versions. Major versions change function names, result shapes, structured-output APIs, and the stream protocol, so retrieve matching official documentation for imports, options, and error types. This guide records our approach, not frozen SDK syntax.
