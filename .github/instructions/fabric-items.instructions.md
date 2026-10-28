---
description: The item folders that Fabric's Git integration writes under fabric/
applyTo: "fabric/**"
---
- Fabric writes these folders. Change only notebook code cells and semantic model measures; nothing else.
- Never edit `.platform` files, `# METADATA` blocks or `# META` lines, `lineageTag` lines, or item folder names: Fabric uses them to match each item in the workspace.
- IDs in these files belong to the Dev workspace. Deployment replaces them through `fabric/parameter.yml`; never edit them by hand.
- A measure's definition, folder, format and description come from `docs/measures.md`.
- Change Fabric items only through these files, never through an MCP tool that writes to a workspace.
