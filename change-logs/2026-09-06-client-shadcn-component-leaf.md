# Client Shadcn Component Convention

Date: 2026-09-06

## Changes

- Added the conditionally loaded `react/shadcn` convention leaf beneath the React slice, with router triggers for component creation, updates, themes, variants and styling reviews.
- Updated the canonical React UI guide to require shadcn and distinguish foundation components, shared compositions and feature UI. New shared namespaces use `composed-ui/`; existing form abstractions remain in the composition tier.
- Assigned themes to semantic tokens, reusable visual choices to the owning component's variants, and feature overrides to supported props, slots and layout.
- Added deliberate upstream merge and affected-consumer verification guidance; removed outdated copied primitive and vendor examples while retaining feature coordination examples.
- Recorded ownership terminology, updated the React index and source mapping, and reviewed the React derivative.
- Deferred Paper/OpenSpec integration and framework-agnostic component-system guidance.

## Validation

- Reviewed canonical and portable guidance together and refreshed their source fingerprints.
- Validated the client skill with the official skill validator.
- Checked changed Markdown local links, code fences and Git whitespace.
