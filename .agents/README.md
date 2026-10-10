# Project agent skills

`.agents/skills/` is the project skill directory. Cursor and other agents
that follow the Agent Skills layout load it from the repo. Each skill is a
folder with `SKILL.md`. `name` matches the folder name.

Shared checklists for the engineering pack are in `.agents/references/`.
Provenance for the copied pack is in `skills/VENDOR.md`.

`.agents/mcp_config.json` stays on this machine. It can hold tokens.
`mcp_config.example.json` shows the shape with a placeholder. Do not commit
the real file.
