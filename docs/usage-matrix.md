# Usage Matrix

Use this matrix to choose the right template layout.

| Use case | Skill location | Instruction file | Example |
| --- | --- | --- | --- |
| Reusable source library | `skills/` | `README.md` and docs | Repository root |
| Codex project auto-discovery | `.agents/skills/` | `AGENTS.md` | [../examples/codex-project/](../examples/codex-project/) |
| Claude Code project auto-discovery | `.claude/skills/` | `CLAUDE.md` | [../examples/claude-code-project/](../examples/claude-code-project/) |
| Portable generic template | `skills/` | `AGENTS.md` and `CLAUDE.md` | [../examples/minimal/](../examples/minimal/) |

## Rule Of Thumb

Keep reusable Skills in the top-level `skills/` directory of this repository. Copy selected Skills into the tool-specific project directory only when you want that tool to auto-discover them.
