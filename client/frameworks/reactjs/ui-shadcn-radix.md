# UI Component Convention (shadcn/ui)

Shadcn/ui is mandatory for new and modified React UI under this convention. Use its components as the owned foundation of the application design system. Framework-agnostic component-system guidance is deferred.

This requirement selects the component system; it does not authorize an unrelated application-wide migration. For an existing alternative system, identify the affected migration boundary and dependencies before implementation. Apply the requested scope and existing scaffolding/dependency rules. Reviews report noncompliance without changing code.

## Component Ownership

```text
src/components/
├── ui/                    # Owned shadcn foundation components and variants
├── composed-ui/           # Shared compositions without feature knowledge
└── form/                  # Existing StandardForm composition namespace

src/features/<feature>/components/
└── ...                    # Feature business and presentation components
```

These are three ownership tiers. `form/` is a specialized namespace within the shared composition tier, not a fourth tier. See [Forms](./forms-react-hook-form.md).

| Tier | Responsibility | Examples |
| --- | --- | --- |
| UI foundation | Shadcn components, their anatomy, shared styling and variants | Button, Input, Dialog, Card |
| Shared composition | A reusable arrangement or interaction built from the foundation, with props, slots and callbacks | ConfirmDialog, SearchToolbar, a generic DataTable |
| Feature component | Feature vocabulary, business coordination or feature-specific presentation | DeleteCustomerDialog, CustomerTable, ProfileForm |

“Primitive” means an application foundation component here, not necessarily a single element or a headless library primitive. Installed shadcn components can be internally composed and still belong in `ui/`. Complexity or child count does not decide placement.

Use `composed-ui/` for new shared compositions. Existing `custom-ui/` may remain during incremental migration; extend its cohesive namespace instead of creating competing directories unless the task includes renaming it. Resolve actual paths and aliases from the target application. In a monorepo, keep the same ownership rules in the resolved application or shared UI package; folder names alone do not justify package extraction.

Dependencies point toward shared UI: features may consume shared compositions and foundation components directly; compositions may consume other shared compositions and foundation components; the foundation must not import compositions or features. Keep composition dependencies acyclic. Shared UI must not import feature schemas, business APIs, query adapters, route policies or application infrastructure containers.

Feature-specific presentation stays with its feature even if it has no fetching. A reusable customer card still belongs to its domain owner; reuse alone does not make it generic UI. Extract a shared composition when it has a coherent feature-independent contract, not merely because markup is long.

## Choose Before Creating

1. Reuse an existing component that owns the needed behavior and satisfies the requirement.
2. Use the appropriate installed shadcn component and its existing variants.
3. Add the matching shadcn component when missing, using the target setup and current official documentation.
4. Extend a foundation component for a shared visual variant, or compose components for a reusable arrangement or interaction.
5. Keep feature behavior in the feature component.

Do not hand-build a replacement button, dialog, input or other control when shadcn supplies the needed component. When no suitable component exists, inspect the available registry and composition options, then document why a custom foundation component is necessary. Preserve accessible semantics and the established component API conventions. This exception addresses missing coverage; it does not make shadcn optional.

Normal semantic markup and layout containers are allowed. Do not introduce a component wrapper for every element.

## Themes, Variants and Overrides

| Change | Owner | Example |
| --- | --- | --- |
| Shared palette or theme | Semantic design tokens in the established theme source | Brand color, light/dark surface values |
| Reusable visual choice of one component | That component's variant definition | Button intent or size; Badge tone |
| Shared arrangement or interaction | Shared composition | Confirmation title, message and actions |
| Feature behavior or content | Feature component | Customer deletion mutation and wording |
| Placement within a parent | Consumer layout | Width, grid placement, alignment |

Use semantic tokens rather than hardcoded theme colors. A new theme changes token values; it does not require separate themed copies of each component or a variant for every brand. A shared change to the default appearance belongs in the foundation component's base styles; an opt-in choice belongs in a named variant.

Reuse an existing variant first. Add a meaningful, feature-independent variant to the owning component when needed, following its existing variant mechanism (such as CVA). Do not copy the component or wrap it solely to recolor it. A composition can own its own variants when they describe the composition rather than an underlying primitive.

At call sites, use variants, props and slots for supported changes. Reserve `className` overrides for placement/layout; keep colors, typography, internal spacing and interaction-state styling in the owning component or tokens. If a feature needs a distinct treatment, give the visual choice a reusable semantic name and keep the business meaning in the feature. Avoid feature-named primitive variants and cascading selectors that reach into shared internals.

For example, DeleteCustomerDialog supplies feature copy and an action callback to ConfirmDialog, which selects the Button destructive variant. The feature owns the mutation and resulting navigation; ConfirmDialog owns the generic dialog arrangement; Button owns destructive styling. Neither shared component knows what a customer is.

## Creating and Updating Components

Before editing, inspect the owning workspace's configuration, aliases, component source, theme source, configured primitive base, installed versions and current consumers. Follow the configured base (for example Radix or Base UI); do not assume their composition APIs are interchangeable.

Use the installed `shadcn` skill when available and current official documentation for exact CLI commands, component anatomy and version-specific integration. This convention owns placement and styling decisions; vendor guidance owns the current implementation syntax.

For additions, use the project package runner and resolved component destinations. Review generated source and dependencies, then adapt the owned source to this convention. For updates, compare upstream changes with local source before applying them. Merge deliberately so local variants, tokens, accessibility behavior and consumer contracts survive; do not blindly overwrite customized components.

Identify affected consumers before changing a default, token, prop contract or shared variant. Prefer an opt-in variant when the requested difference applies to only some consumers. Keep loading, disabled, focus, validation and responsive behavior consistent with the actual component requirements.

## Component Separation

### Business vs Presentation

| Aspect        | Business Component   | Presentation Component      |
| ------------- | -------------------- | --------------------------- |
| Data fetching | Yes                  | No                          |
| Mutations     | Yes                  | No                          |
| Form state    | Owns (`useForm`)     | Consumes (`useFormContext`) |
| Navigation    | Yes                  | No                          |
| Location      | `<feature>-form.tsx` | `<feature>-form-fields.tsx` |

### Business Component Example

Both patterns below are valid. Prefer A for reuse; choose B when route-local sequencing belongs to the component while cache mechanics remain in a named sync hook.

Variant A: hook-owned invalidation (preferred)

```typescript
// src/features/profile/components/profile-form.tsx
'use client'

export default function ProfileForm() {
  const form = useForm<ProfileFormShape>({
    resolver: zodResolver(ProfileFormSchema),
    mode: "onSubmit",
  })
  const { isSubmitting } = form.formState

  // Hook owns invalidation behavior
  const updateMut = useMutProfileUpdate()

  const onSubmit = async (data: ProfileFormShape) => {
    await updateMut.mutateAsync(toUpdateProfileInput(data))
    router.push(appRoutes.dashboard)
  }
}
```

Variant B: component-coordinator sequencing (allowed)

```typescript
// sync.ts owns concrete cache mechanics
export function useModProfileSync() {
  const queryClient = useQueryClient()
  return {
    invalidateAfterUpdate: () =>
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.current() }),
  }
}

export default function ProfileForm() {
  const updateMut = useMutProfileUpdate()
  const profileSync = useModProfileSync()

  const onSubmit = async (data: ProfileFormShape) => {
    await updateMut.mutateAsync(toUpdateProfileInput(data))
    await profileSync.invalidateAfterUpdate()
    router.push(appRoutes.dashboard)
  }
}
```

See `./server-state-patterns-react.md` for complete decision rules and scenarios.

```typescript
// Shared render structure (inside either variant)
return (
  <StandardFormProvider form={form} onSubmit={onSubmit}>
    <ProfileFirstNameField />  {/* Presentation */}
    <ProfileLastNameField />   {/* Presentation */}
    <Button type='submit' disabled={isSubmitting}>Save</Button>
  </StandardFormProvider>
)
```

### Presentation Component Example

```typescript
// src/features/profile/components/profile-form-fields.tsx
'use client'

import { useFormContext } from 'react-hook-form'
import type { ProfileFormShape } from '../schemas'

export function ProfileFirstNameField() {
  const { control } = useFormContext<ProfileFormShape>()

  // Pure rendering - no business logic
  return (
    <StandardFormInput<ProfileFormShape>
      name='firstName'
      label='First Name'
      placeholder='John'
      required
    />
  )
}
```

## Verification

- Confirm ownership and import direction, including feature presentation that has no data fetching.
- Check variant typing and affected consumers when a public contract changes.
- Render affected components and representative screens in supported themes and required viewports.
- Verify relevant keyboard, focus, accessible naming, disabled, error and loading behavior; preserve the configured primitive's accessibility contract.
- Run affected type, lint and existing test checks. Add focused behavior tests when interaction or contracts change, rather than tests that merely repeat styling implementation.
- Review upstream merges for preserved local customizations and unintended default changes.

## Official Implementation References

- [shadcn/ui philosophy and composition](https://ui.shadcn.com/docs)
- [shadcn/ui theming](https://ui.shadcn.com/docs/theming)
- [shadcn/ui component configuration](https://ui.shadcn.com/docs/components-json)
- [shadcn/ui CLI](https://ui.shadcn.com/docs/cli)

Resolve exact vendor APIs from the target versions at execution time. This guide defines repository ownership and customization rules.
