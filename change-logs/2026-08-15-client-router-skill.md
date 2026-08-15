# Client Architecture Router Skill

Date: 2026-08-15

## Summary

Added an installable `$client` architecture router with eight composable concern slices while preserving the existing client documentation as the authoring source of truth.

## Changes

- Added `client/skill/SKILL.md` with routing for foundations, contracts, data flow, state/realtime, telemetry, testing, React, and Next.js.
- Added portable derived references and OpenAI skill metadata.
- Added repository-only source mapping and deterministic drift checking under `client/skill-maintenance/` so derived slices cannot silently fall behind mapped client docs without shipping maintainer tooling to consumers.
- Added Codex and repository-local installation guidance.
- Disabled `copy-guides.sh`; it now exits without changing a consumer repository and explains the skill migration.
- Replaced active consumer-copy instructions with skill installation, maintenance, AGENTS alignment, and OpenCode migration guidance.

## Compatibility

- Existing files under `client/core/` and `client/frameworks/` remain canonical and retain their current structure.
- The source skill lives at `client/skill/` and must be installed with destination name `client`.
- Drift tooling and provenance metadata live outside the installable skill under `client/skill-maintenance/`.
- Server documentation currently has no installable skill or automated distribution replacement.
