# ReactJS Architecture Overview

This section documents React-specific implementation details for the client architecture.

ReactJS concerns include:

- Component boundaries in TSX (business vs presentation)
- Server-state ownership patterns (hook-owned effects, coordinator sequencing, hybrid)
- Form state patterns (`react-hook-form` + StandardForm)
- UI primitives and composition (`shadcn/ui`, Radix/Base UI)
- Client coordination state patterns (Zustand)
- Mutation/workflow telemetry ownership through core `AppLogger` and `ProductAnalytics` ports
- Browser dependency composition and provider lifetimes
- Realtime subscription lifecycle over provider-neutral feature APIs

See `client/frameworks/reactjs/server-state-patterns-react.md` for the server-state cookbook.

See `client/core/` for the framework-agnostic architecture and rules.
