# 2026-02-15: Client Docs Consistency Sweep

## Summary

Applied a focused consistency sweep across canonical client docs after the feature API/testability updates.

## Updated

- `client/core/query-keys.md`
  - Reworded Query Key Factory guidance to be explicit that it is canonical for non-tRPC adapters.
- `client/frameworks/reactjs/forms-react-hook-form.md`
  - Clarified `!isDirty` as an optional edit/update-only no-op prevention exception.
- `client/frameworks/reactjs/server-state-patterns-react.md`
  - Matched edit-form scenario wording to the same edit/update-only `!isDirty` exception.
- `client/diagrams.md`
  - Updated runtime layer diagram to show `I<Feature>Api` + class + factory boundary and query adapter dependency on the interface contract.
- `client/README.md`
  - Updated top architecture diagram wording so query adapter hooks own server-state/caching concerns, while feature components focus on orchestration.

## Notes

- Documentation-only changes.
- No runtime behavior changed.
