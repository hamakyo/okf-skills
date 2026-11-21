# Host Adapters (Optional Generated Packages)

This directory contains optional, host-specific adapter prototypes generated from the canonical portable Skills under [../skills/](../skills/) and the adapter manifest in [manifest.yaml](manifest.yaml).

- **Copy-based installation remains the primary workflow** (copy selected Skills from `skills/` into `.agents/skills/` for Codex or `.claude/skills/` for Claude Code).
- **Do not hand-edit files under `adapters/codex/` or `adapters/claude-code/`.** Edit canonical `skills/*/SKILL.md` or [manifest.yaml](manifest.yaml), then regenerate and verify:

```sh
python scripts/sync_adapters.py
python scripts/sync_adapters.py --check
```

## Included Adapters

| Adapter | Host | Generated Contents | Quick Usage |
| --- | --- | --- | --- |
| `adapters/codex/` | Codex | `.codex-plugin/plugin.json`, synced `skills/*/SKILL.md`, and per-Skill `agents/openai.yaml` metadata | Reference via `.agents/plugins/marketplace.json` or copy pre-enriched Skill folders into `.agents/skills/` |
| `adapters/claude-code/` | Claude Code | `.claude-plugin/plugin.json` and synced `skills/*/SKILL.md` | Load directly for a session with `claude --plugin-dir ./adapters/claude-code` |

See [../docs/packaging.md](../docs/packaging.md) for the packaging decision, tradeoffs, and host-specific installation and discovery details.
