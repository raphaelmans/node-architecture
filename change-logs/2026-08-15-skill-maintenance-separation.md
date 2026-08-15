# 2026-08-15: Separate Skill Maintenance Artifacts

## Summary

Moved source-drift manifests and checkers out of the portable `$client` and `$server` packages. Installed skills now contain only runtime instructions, UI metadata, and curated references.

## Structure

```text
client/skill/                 portable $client package
client/skill-maintenance/     client source map and drift checker
server/skill/                 portable $server package
server/skill-maintenance/     server source map and drift checker
```

## Changes

- Moved each `source-map.json` beside its canonical documentation rather than shipping it to consumers.
- Moved each `check-source-drift.py` into the matching `skill-maintenance/` directory.
- Updated repository contribution and architecture-update commands to use the new paths.
- Removed maintainer-tool references and `scripts/` from installed package guidance.
- Preserved source fingerprints, explicit slice mappings, and targeted refresh behavior.

## Validation

- Validated both portable skill packages with the official skill validator.
- Ran both drift checkers from their new locations.
- Tested stale-source detection, targeted refresh, missing mappings/references, and installed-package contents.
