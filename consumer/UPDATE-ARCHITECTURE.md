# Updating Architecture Guidance

Architecture changes are authored in this repository. There is no downstream `guides/` synchronization step.

## Client Updates

1. Change the correct canonical document under `client/core/` or `client/frameworks/`.
2. Run `python3 client/skill-maintenance/check-source-drift.py`.
3. Review and update every affected derived slice under `client/skill/references/`.
4. Refresh each reviewed fingerprint with `python3 client/skill-maintenance/check-source-drift.py --refresh <slice>`.
5. Run the drift checker again and validate the skill.
6. Commit and publish the repository revision; consumers reinstall or update the skill deliberately.

Do not refresh fingerprints without reviewing the derived guidance. Source hashes detect possible drift; they cannot determine semantic equivalence.

## Server Updates

1. Change the correct canonical document under `server/core/` or `server/runtime/`.
2. Run `python3 server/skill-maintenance/check-source-drift.py`.
3. Review and update every affected derived slice under `server/skill/references/`.
4. Refresh each reviewed fingerprint with `python3 server/skill-maintenance/check-source-drift.py refresh <slice>`.
5. Run the drift checker again and validate the skill.
6. Commit and publish the repository revision; consumers reinstall or update the skill deliberately.

Every canonical server Markdown guide must remain mapped in `server/skill-maintenance/source-map.json`.

## Legacy Copier

`copy-guides.sh` is intentionally disabled and exits without modifying the requested target. Do not restore copying as an undocumented compatibility path.
