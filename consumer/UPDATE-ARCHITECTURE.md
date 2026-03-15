# Updating the Architecture Docs

> This guide is for AI agents (and developers using AI agents) who need to update,
> extend, or tweak the architecture documentation in this repository and then push
> those changes to one or more consumer repos.

---

## Step 0 — Required Information (AI Agent Must Ask First)

Before making any changes, the AI agent MUST ask the user for:

1. **Absolute path to this architecture repo**
   > "What is the absolute path to the node-architecture repo on your machine?"
   > Example: `/Users/raphaelm/Documents/Coding/node-architecture`

2. **Absolute path(s) to each consumer repo to sync after the update**
   > "Which project repo(s) should receive the updated guides?
   > Please provide the absolute path for each."
   > Example: `/Users/raphaelm/Documents/Coding/boilerplates/next16bp`

Do NOT assume, guess, or hardcode any paths. Wait for explicit answers before proceeding.

---

## Step 1 — Identify the Change Type

Refer to `CONTRIBUTING.md` for full rules. The most common cases are:

| Change type | Scope | Key rule |
| --- | --- | --- |
| **Minor tweak** | Edit an existing doc (convention, wording, rule clarification) | Edit only the correct layer doc (`core/*` if agnostic, framework/* if specific) |
| **Add guidance to existing module** | New section or file in an existing folder | Follow the folder's existing naming and style |
| **New client framework** | New folder under `client/frameworks/<framework>/` | Must align with `client/core/*` contracts |
| **New server runtime or library** | New folder under `server/runtime/<runtime>/` | Must align with `server/core/*` contracts |

When unsure which layer a rule belongs to, apply CONTRIBUTING.md's rule of thumb:
- Works across frameworks/runtimes → `core/*`
- Depends on specific framework/runtime behavior → framework/runtime docs
- Both → define contract in `core/*`, add implementation details in framework/runtime docs

---

## Step 2 — Make the Changes

### Minor tweak / add guidance

1. Open the correct file in the architecture repo (absolute path from Step 0).
2. Edit following `CONTRIBUTING.md` style rules:
   - Prefer additive updates over broad rewrites.
   - Keep examples concrete but framework-neutral in `core/*`.
   - Do not duplicate core rules in framework docs; reference them instead.
3. If the change affects the PR Review Checklist or a conventions doc, update the checklist entries to match.
4. If non-trivial (behavioral change to a contract), add a changelog entry under `change-logs/` if that directory exists.

### If the change touches client/server error handling

When updating docs for API, transport, or toast/error-surface behavior, explicitly verify both sides of the contract:

- Client-side guidance should preserve user-safe messages for expected client-correctable `4xx` failures (for example conflict/business-rule errors), rather than collapsing them into generic fallback toasts.
- Server-side guidance should treat public error payloads as an explicit allowlist. Do not spread framework-provided error objects or `shape.data` into client responses.
- Public responses may include safe metadata such as `code`, `httpStatus`, `requestId`, `path`, and validation payloads when documented, but must never expose `stack` or other raw diagnostics.
- If the rule is transport-specific (for example tRPC formatter behavior), keep the canonical error policy in `core/*` and add the transport details in the relevant framework/runtime doc.

### Add a new client framework (example: Vue, Svelte)

Create the following structure:

```text
client/frameworks/<framework>/
  README.md       # index of docs in this folder
  overview.md     # what this framework covers and how it maps to client/core/*
```

Optional (add as needed):

```text
client/frameworks/<framework>/
  conventions.md
  error-handling.md
  state-<library>.md
  forms-<library>.md
  metaframeworks/
    <meta>/
      README.md
      overview.md
      folder-structure.md
```

Then update:
- `client/frameworks/README.md` — add the new framework entry
- `client/README.md` — add to the framework docs index
- `AGENTS-MD-ALIGNMENT.md` — add a new "If \<Framework\>" include block under Step 2

Must align with:
- `client/core/client-api-architecture.md` (`components -> query adapter -> featureApi -> clientApi -> network`)
- `client/core/error-handling.md` (normalize to `AppError`)
- `client/core/server-state-tanstack-query.md` (server-state ownership in query adapter)

### Add a new server runtime or library (example: Go, Express full impl)

Create the following structure:

```text
server/runtime/<runtime>/
  README.md
```

Optional (add as needed):

```text
server/runtime/<runtime>/
  libraries/
    <library>/
      README.md
      integration.md
  metaframeworks/
    <meta>/
      README.md
```

Then update:
- `server/runtime/README.md` — add the new runtime entry
- `server/README.md` — add to the runtime docs index
- `AGENTS-MD-ALIGNMENT.md` — add a new "If \<Runtime/Library\>" include block under Step 2

Must align with:
- `server/core/conventions.md` (layer boundaries)
- `server/core/error-handling.md` + `server/core/api-response.md` (error and envelope contracts)
- `server/core/transaction.md` + `server/core/logging.md` (transaction and logging expectations)

---

## Step 3 — Verify Consistency

Before syncing, confirm the following are still consistent across all changed docs:

- [ ] Client API chain (`components -> query adapter -> featureApi -> clientApi -> network`) unchanged in `client/core/*`
- [ ] Error normalization boundary (`unknown -> AppError`) unchanged
- [ ] Expected `4xx` business-rule/client-correctable failures still preserve user-safe messages end-to-end
- [ ] Logging and correlation ownership at transport boundaries unchanged
- [ ] Public error payloads are whitelist-based and do not leak `stack` or other raw diagnostics
- [ ] Query key strategy (direct tRPC generated keys, `buildTrpcQueryKey` wrapper interop, plain keys for non-tRPC adapters) unchanged
- [ ] Testing standard unchanged: `__tests__` mirror layout, AAA pattern, test doubles policy (`client/core/testing.md` + `server/core/testing-service-layer.md`)
- [ ] No canonical rule moved out of `core/*` into a framework/runtime doc
- [ ] No contradictory guidance between related docs (e.g., `conventions.md` vs a framework doc)
- [ ] New files/folders referenced in their parent `README.md`
- [ ] `AGENTS-MD-ALIGNMENT.md` updated if new guides need to be selectively included

---

## Step 4 — Sync to Consumer Repos

After changes are verified, run `copy-guides.sh` once for each consumer repo path collected in Step 0.

```bash
# From the architecture repo root (absolute path from Step 0):
./copy-guides.sh /absolute/path/to/consumer-repo-1
./copy-guides.sh /absolute/path/to/consumer-repo-2
```

The script replaces `guides/client/`, `guides/server/`, `guides/legacy/`, and the root guide docs wholesale in each consumer repo.
No manual merging is needed.

After syncing, confirm with the user that:
- The correct consumer repos were updated.
- The guides directory looks correct in each consumer repo.
- No `AGENTS.md` / `CLAUDE.md` changes are needed (framework blocks are unchanged unless a
  new framework was added, in which case guide the user through adding the new include block
  following `guides/AGENTS-MD-ALIGNMENT.md` Step 2).

---

## What NOT to Do

- Do not edit files inside a consumer repo's `guides/` directory. Those are generated.
  Always edit in the architecture repo, then re-run `copy-guides.sh`.
- Do not document or implement public error serialization by spreading framework error payloads wholesale.
  Explicitly whitelist safe fields instead.
- Do not move canonical rules out of `core/*` into framework docs.
- Do not couple `server/core/*` rules to a specific runtime or library.
- Do not skip the consumer repo sync step — the architecture repo and consumer repos will drift.
