# Usage Matrix

Use this matrix to choose the right template layout.

| Use case | Skill location | Instruction file | Example |
| --- | --- | --- | --- |
| Reusable source library | `skills/` | `README.md` and docs | Repository root |
| Codex project auto-discovery | `.agents/skills/` | `AGENTS.md` | [../examples/codex-project/](../examples/codex-project/) |
| Claude Code project auto-discovery | `.claude/skills/` | `CLAUDE.md` | [../examples/claude-code-project/](../examples/claude-code-project/) |
| Portable generic template | `skills/` | `AGENTS.md` and `CLAUDE.md` | [../examples/minimal/](../examples/minimal/) |
| Codex plugin & `agents/openai.yaml` adapter (optional) | `adapters/codex/skills/` | `AGENTS.md` (in target repo) | [../adapters/README.md](../adapters/README.md) |
| Claude Code plugin adapter (optional) | `adapters/claude-code/skills/` | `CLAUDE.md` (in target repo) | [../adapters/README.md](../adapters/README.md) |

## Rule Of Thumb

Keep reusable Skills in the top-level `skills/` directory of this repository. Copy selected Skills into the tool-specific project directory only when you want that tool to auto-discover them.

Example copies in this repository are declared in `examples/skill-copies.yaml`. Run `python scripts/sync_examples.py` after changing a canonical Skill and use `--check` in validation workflows.

Optional host adapters under `adapters/` are generated from `skills/` and `adapters/manifest.yaml` via `python scripts/sync_adapters.py` (checked with `--check`). See [packaging.md](packaging.md) for packaging tradeoffs and discovery details.
