# Shadcn Component Convention Leaf

Load with `react` when creating, updating or reviewing UI components, shared compositions, themes, variants or feature styling. Do not load for unrelated React data, configuration or lifecycle work.

## Adoption and Preflight

Shadcn/ui is mandatory for new and modified React UI under this convention. Do not treat another component library as an equivalent specialization. An existing alternative system requires an explicit affected migration boundary; the convention does not expand a local task into a whole-application rewrite. Reviews report violations without mutation. Apply existing scaffolding and dependency authorization rules when setup is required.

Inspect the owning workspace, installed versions, component configuration, aliases, resolved source and theme locations, primitive base, existing compositions and affected consumers. Use the installed `shadcn` skill when available. Retrieve current official documentation for the actual CLI and component APIs; do not assume a primitive base, import alias or package runner.

## Three Ownership Tiers

| Tier | Default placement | Owns |
| --- | --- | --- |
| UI foundation | `components/ui/` | Shadcn components, shared base styles and variants |
| Shared composition | `components/composed-ui/` | Feature-independent arrangements and interactions built from shared components |
| Feature component | `features/<feature>/components/` | Feature business coordination and feature-specific presentation |

An installed shadcn component remains foundation UI even if it internally composes multiple controls. “Primitive” denotes its foundation role, not its element count. Existing StandardForm components in `components/form/` are a specialized shared composition namespace, not another tier.

Use `composed-ui/` for new namespaces. Preserve a cohesive existing `custom-ui/` namespace during incremental work unless migration is requested; do not split shared ownership across duplicate directories. Resolve actual paths from repository configuration and package ownership.

Features may import either shared tier. Compositions may import foundation components and other shared compositions without cycles. Foundation components never import compositions or features. Shared UI never imports feature contracts, business APIs, query adapters, route policies or infrastructure containers. Feature-specific presentation remains feature-owned even when it has no side effects or is reused by multiple screens.

## Create or Reuse

Reuse the existing component that owns the required behavior first. Then use installed shadcn components and their variants, add the appropriate missing shadcn component, or compose those components. Do not hand-build equivalent controls when shadcn covers the requirement.

When no suitable shadcn component exists, inspect registry and composition options before introducing a custom foundation component. Explain the coverage gap and preserve accessibility and API conventions. Ordinary semantic markup and layout containers remain appropriate.

A new shared composition needs a coherent feature-independent contract; component length alone is insufficient. Keep domain vocabulary and orchestration in features. For example, a feature-owned DeleteCustomerDialog provides copy and an action callback to a generic ConfirmDialog, which uses the foundation Button's destructive variant.

## Styling Ownership

- Themes change semantic tokens in the established theme source. Do not duplicate components or create a variant per brand or light/dark theme.
- Shared default appearance belongs in the owning component's base styles. Reusable opt-in visual choices belong in that component's variant definition.
- Reuse existing variants before adding meaningful semantic variants with the established variant mechanism. Do not copy or wrap a primitive solely for styling.
- Shared compositions may own variants for their own arrangement or behavior; they use primitive variants for underlying controls.
- Features select props, variants and slots. Consumer class overrides are for placement/layout, not colors, typography, internal spacing or interaction-state styling. Keep feature names out of foundation variants and avoid selectors targeting shared internals.

## Update and Verify

Compare upstream source with local customizations before updating. Merge deliberately; preserve local variants, tokens, accessibility and consumer contracts instead of blindly overwriting owned code. Review generated files and dependency changes using the owning project's tooling.

Identify affected consumers before changing shared defaults, tokens or public props. Use an opt-in variant when only some consumers need the change. Check affected types and existing tests, then render representative consumers in supported themes and required viewports. Verify relevant keyboard, focus, accessible naming and interaction states. Add focused behavior tests for changed interactions or contracts, not tests that merely restate classes.

## Official Implementation References

- [shadcn/ui](https://ui.shadcn.com/docs)
- [Theming](https://ui.shadcn.com/docs/theming)
- [Component configuration](https://ui.shadcn.com/docs/components-json)
- [CLI](https://ui.shadcn.com/docs/cli)

This leaf owns architectural placement and customization policy. Derive current vendor syntax from the target setup and official sources.

## Derivation Sources

Derived from the source repository's React UI component convention. Source paths are provenance only in an installed skill.
