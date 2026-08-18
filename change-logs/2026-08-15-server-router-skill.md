# 2026-08-15: Server Architecture Router Skill

## Summary

Added one installable `$server` architecture router derived from the canonical server guides. Together with `$client`, it replaces the former copied `guides/` bundle with progressive, concern-based skill loading.

## Skill

- Added `server/skill/SKILL.md` with eight composable slices: foundations, contracts, data flow, operations, security, telemetry, testing, and runtimes.
- Added UI metadata for the `Server Architecture` skill and the `$server` default prompt.
- Kept shared layer, DI, contract, transaction, error, and telemetry invariants in the router while moving detailed guidance into curated references.
- Preserved explanation, diagnosis, review, planning, implementation, and refactoring intent instead of treating every invocation as a mutation.

## Canonical Sources and Drift

- Kept the 49 existing Markdown guides under `server/` as the authoring source of truth.
- Added an explicit source map covering every canonical server guide, including runtime, provider, framework, and webhook material.
- Added a dependency-free checker that validates mappings, references, sources, aggregate SHA-256 fingerprints, and complete canonical coverage.
- Added targeted refresh for one reviewed slice; fingerprints cannot be refreshed implicitly during ordinary skill use.
- Updated contributor and architecture-update guidance with the server skill maintenance workflow.

## Distribution

- Updated installation guidance for GitHub source path `server/skill` and destination name `server`.
- Updated consumer integration guidance to use both `$client` and `$server` without loading every architecture document into project instructions.
- Updated the disabled `copy-guides.sh` entrypoint to provide migration instructions for both skills without modifying its target.
- Left standalone HTML companions and historical guides in the source repository; they are not bundled into the skills.

## Validation

- Initialized from the official skill scaffold and validated the finished skill with the official quick validator.
- Verified source drift, source coverage, internal links, UI metadata, temporary installation, and disabled-copy behavior.
- Forward-tested cross-cutting runtime, security, operations, telemetry, contracts, and testing requests in isolated skill invocations.
- Added a dedicated Skill tab to the standalone server architecture HTML with
  the portable package boundary, eight routed slices, Skills.sh/GitHub install
  and update commands, and links to the package and installation guide.
