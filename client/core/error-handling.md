# Error Handling (Agnostic)

Conventions for handling errors across the client architecture.

## Error Types

| Error Type        | Source                 | Handling                        |
| ----------------- | ---------------------- | ------------------------------- |
| Validation errors | Schema boundary        | Field-level messages            |
| API errors        | `clientApi` / `featureApi` | Toast or root-level error    |
| Query errors      | Query adapter layer    | Error UI or retry               |
| Unexpected errors | Runtime exceptions     | Framework error boundary        |

## Rules

- Prefer typed, inspectable errors emitted from `clientApi`.
- Validation errors should be mapped close to the user’s input.
- Query adapter owns retry and invalidation policies; components only render states.

Framework-specific wiring:

- React forms: `client/frameworks/reactjs/forms-react-hook-form.md`

