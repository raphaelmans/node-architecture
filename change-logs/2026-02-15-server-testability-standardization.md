# 2026-02-15: Server Testability Standardization (MUST)

## Summary

Standardized server-layer testability as a MUST-level rule across modules.

Canonical architecture flow is now explicitly documented as:

`controller -> usecase (optional) -> service -> repository`

## Added

- `server/core/testing-service-layer.md`
  - global testing standard for controller/usecase/service/repository
  - interface-first dependency rules
  - fixtures + doubles + contract/regression guidance

## Updated

- `server/core/conventions.md`
  - explicit canonical layer chain
  - MUST interface dependency rules for usecase/service/repository boundaries
  - factory wiring rule for testability
  - testability MUST checklist + final verification additions
- `server/core/overview.md`
  - testability stated as a first-class quality gate
  - testing doc linked in documentation index
- `server/README.md`
  - core table includes testing standard
  - quick-start testing baseline section added
- `server/core/webhook/testing-overview.md`
  - linked to core testing standard; positioned as specialized extension
- `server/core/webhook/testing-test-doubles.md`
  - linked to global doubles policy

## Notes

- This change is documentation-only.
- Webhook testing docs remain specialized; global testability contract now lives in core.

