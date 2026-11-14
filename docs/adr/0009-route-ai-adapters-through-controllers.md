---
status: accepted
---

# Route AI adapters through controllers

Internal workers may call a use case or service directly, yet agent tools and workflow business steps must enter application code through a framework-neutral controller, even for an operation with no public endpoint. An AI adapter is a caller we trust less than our own worker: a model chooses a tool's arguments, and a workflow step replays serialized input in another process, possibly days later. We accept a thin, sometimes pass-through controller per internal operation in exchange for one entry shape for every AI-driven call: a declared contract, an explicit actor, one use case or service, and translated errors. It also keeps the agent framework replaceable, because nothing behind the controller knows which engine called it.

## Consequences

- A tool or step never selects services, receives a container, or reaches a repository. It receives a narrow controller factory.
- An operation that already has a public controller is reused, so HTTP, tool, and step callers cannot drift apart. An internal controller uses a server-only contract and implies no route.
- Pure engine work such as mapping, branching, and suspension performs no business operation and needs no controller.
- Non-AI workers keep the direct-call allowance. A worker that only hands committed intent to the engine, such as outbox dispatch, is not an AI adapter.
- The step's actor is an execution identity rebuilt from the run's persisted scope, and the operation re-authorizes it on every business step.
