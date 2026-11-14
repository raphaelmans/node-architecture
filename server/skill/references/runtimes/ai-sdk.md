# AI SDK Integration Convention

Load only when the Vercel AI SDK is present or selected. Read [runtimes](../runtimes.md) and the [AI boundaries leaf](../operations/ai-boundaries.md). It is independent of [Mastra](mastra.md); direct model calls follow this leaf even when Mastra is also used.

## Apply

- Implement the deployable's shared model gateway port with the AI SDK; modules pass it their own prompts, schemas, and model choice. That adapter and the composition root are the only modules that import the SDK or a provider package.
- Create the provider from an injected credential; a missing credential fails at composition with a typed error. Accept an injectable transport for tests and request hooks.
- Expose only the call shapes the application uses. For structured generation, pass the caller's schema to the SDK's structured-output mechanism and return the validated value.
- Keep Zod contracts application-owned and independent of ORM/provider types. Native validation can fulfill the boundary; distinguish fallback, partial and rejected values and derive provider schema projections from the canonical contract rather than maintaining copies.
- When the SDK reports that no valid object was produced, return the raw text, usage, and provider request identity as a rejected result. Rethrow other failures for translation.
- Return token counts, whether usage was actually reported, and any provider metadata the application records. Do not leak SDK result types.
- Keep provider-specific options inside the adapter. Bound retries and parallel embedding calls explicitly.
- Keep each module's model identifiers in one configuration module it owns; the adapter accepts the identifier and does not decide it.
- When an agent framework accepts an AI SDK model object, create it at composition and inject it; agent and tool definitions never construct a provider.
- Native framework model routing is also allowed at composition when supported. Preserve native agent loops, memory and streaming; the application model gateway remains the port for direct service calls. Apply contracts and usage accounting to both paths.
- A route streaming in the AI SDK's UI stream protocol is a framework-owned transport. Keep its wire format, pin the protocol version the client expects, and change server and client together. Client conversation state is not a second source of truth for application records.

## Verify and Sources

Test the adapter with an injected transport or mock model for a valid object, a rejected object, missing usage, provider outage, and retry bounds. Check that nothing else imports the SDK.

- [AI SDK documentation](https://ai-sdk.dev/docs/introduction)
- [Structured data](https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data)
- [Embeddings](https://ai-sdk.dev/docs/ai-sdk-core/embeddings)
- [Testing](https://ai-sdk.dev/docs/ai-sdk-core/testing)
- [Stream protocols](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)

Detect installed `ai` and provider versions. Major versions change function names, result shapes, structured-output APIs, and the stream protocol; resolve exact imports, options, and error types from matching official documentation.
