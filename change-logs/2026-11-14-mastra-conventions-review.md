# Mastra conventions review

Date: 2026-11-14

- Recorded ADR 0009: agent tools and workflow business steps enter through controllers even for internal operations, while non-AI workers keep the direct-call allowance.
- Defined execution identity for workflow steps and required re-authorization on every business step; added the glossary term.
- Added the step-granularity rule: one step is one retry unit, per-item model or provider work uses native iteration, and cheap deterministic checks precede paid calls.
- Promoted schema ownership to its own section in the core AI boundaries guide and reduced the Mastra guide's workflow section to a mapping onto the core rules.
- Required an adoption spike on the installed engine version before the rules bind a project.
- Daily Brief example and call tree: split discovery from per-candidate resolution, moved the exact source-key lookup ahead of embedding, replaced the review queue with observe and enforce duplicate-policy stages, and showed execution identity in every step.
- Reduced the proposal's skill-discovery section to the adoption decision.
- Updated the derived server skill references and refreshed their fingerprints.
