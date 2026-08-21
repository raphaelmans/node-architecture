---
status: accepted
---

# Support single-project and monorepo as equal canonical topologies

The architecture contracts define roles, ownership, and dependency direction independently of physical repository topology. We will maintain single-project and monorepo topologies as equal canonical mappings, with scaffolding selecting the mapping from repository evidence; this accepts the cost of maintaining and verifying both mappings in exchange for portability and avoids coupling the core contracts to a monorepo build system or forcing consumers to migrate.
