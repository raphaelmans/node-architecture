# 2026-02-15: Client Edit/Update Form Re-Sync Standard

## Summary

Documented a canonical edit/update form success flow for forms that read external query data.

## Updated

- `client/frameworks/reactjs/forms-react-hook-form.md`
  - Added feature-specific sync-hook pattern (`query.data` -> `reset(...)`) for edit/update forms.
  - Added explicit `onSubmitRefetch` (`query.refetch()`) in submit sequence.
  - Clarified that edit/update forms should not reset to empty defaults on success.
  - Added checklist items for refetch + re-sync hook requirements.
  - Added RHF note that this architecture favors explicit `reset(...)` sequencing for external-data forms.
- `client/frameworks/reactjs/server-state-patterns-react.md`
  - Extended decision matrix with edit/update external-data refresh case.
  - Updated component-coordinator example to include explicit refetch.
  - Added guardrail that query-data -> form reset logic should live in a dedicated sync hook.
- `client/frameworks/reactjs/error-handling.md`
  - Updated `useCatchErrorToast` submit example to include `onSubmitRefetch`.
  - Clarified success toast sequencing (fires after wrapped async pipeline resolves).
- `client/diagrams.md`
  - Added dedicated ASCII flow for edit/update submit:
    - mutate -> invalidate -> refetch -> reset from refreshed query data.

## Notes

- Documentation-only update.
- No runtime code changes.
