# Adapter And Plugin Packaging

This document records the packaging decision, tradeoffs, and host-specific installation and discovery behavior for OKF Skills.

## Packaging Decision

1. **Preserve copy-based installation as the primary path.** Copying selected Skills from top-level `skills/` into `.agents/skills/` (Codex) or `.claude/skills/` (Claude Code) remains the default, zero-dependency workflow.
2. **Keep `skills/` strictly canonical and host-neutral.** Top-level `skills/*/SKILL.md` files follow the Agent Skills standard and this repository's authoring profile without host-specific metadata or manifests.
3. **Keep OKF v0.3 conformance independent of packaging.** Adopting OKF (`okf/index.md`, `okf/log.md`, concept files) never requires installing a plugin or adapter.
4. **Ship optional, deterministically generated host adapters under `adapters/`.** Because both Codex (`agents/openai.yaml` + `.codex-plugin/plugin.json`) and Claude Code (`.claude-plugin/plugin.json` + `--plugin-dir`) provide concrete discovery and distribution ergonomics when distributing multiple Skills as a unit, this repository maintains generated adapter prototypes under [../adapters/](../adapters/README.md):
   - `adapters/codex/`: Codex plugin layout with synced `skills/*/SKILL.md` and per-Skill `agents/openai.yaml` UI and invocation policy metadata.
   - `adapters/claude-code/`: Claude Code plugin layout with `.claude-plugin/plugin.json` and synced `skills/*/SKILL.md`.
5. **Defer public directory and registry publishing until v1.0 stabilization.** Publishing to hosted marketplaces or registries is intentionally deferred until Skill conventions and evaluation baselines reach v1.0.

## Tradeoffs Evaluation

| Approach | Concrete Benefit | Tradeoffs / Limitations | Status |
| --- | --- | --- | --- |
| Copy-based installation (`skills/` -> `.agents/skills/` or `.claude/skills/`) | Zero tooling lock-in; teams adopt only the Skills they want and customize freely per repository. | Manual updates when upstream canonical Skills evolve. | **Primary (recommended)** |
| Codex `agents/openai.yaml` + plugin (`adapters/codex/`) | Adds Codex UI `display_name`, `short_description`, `default_prompt`, and `policy.allow_implicit_invocation` without polluting canonical `SKILL.md`; supports local/repo marketplace distribution. | Host-specific metadata layer; IDE extensions still rely on standalone `.agents/skills/` copies rather than plugins. | **Optional generated adapter** |
| Claude Code plugin (`adapters/claude-code/`) | Instant one-command testing (`claude --plugin-dir ./adapters/claude-code`) with `/okf-skills:<skill>` namespacing that avoids colliding with project-local Skills. | Host-specific manifest; project-specific `CLAUDE.md` and `okf/` knowledge must still live in the target repository, not inside the plugin. | **Optional generated adapter** |
| External package registries (npm / PyPI / public marketplaces) | Single-command global versioned installs. | Adds release/registry maintenance before v1.0 conventions stabilize and obscures repository-local customization. | **Deferred** |

## Host-Specific Installation And Discovery

### Codex

Codex discovers standalone local Skills across four scopes (following symlinks):

- **Repository scope:** `.agents/skills/<skill>/SKILL.md` scanned from `$CWD` upward to the Git repository root.
- **User scope:** `$HOME/.agents/skills/<skill>/SKILL.md` for personal cross-repo Skills.
- **Admin scope:** `/etc/codex/skills/<skill>/SKILL.md` for machine- or container-wide defaults.
- **System scope:** Skills bundled with Codex.

Installation options:

1. **Copy-based (recommended for project customization):** Copy selected folders from `skills/` into `.agents/skills/` in your repository. Invoke explicitly via `$skill-name` / `/skills` or implicitly via description matching.
2. **Pre-enriched Skill copy (`agents/openai.yaml`):** Copy selected folders from `adapters/codex/skills/` into `.agents/skills/` when you want Codex UI display metadata (`interface`) and invocation policy (`policy.allow_implicit_invocation`) alongside `SKILL.md`.
3. **Plugin / local marketplace (`adapters/codex/`):** Reference `./adapters/codex` from a local or repository marketplace manifest (such as `.agents/plugins/marketplace.json`) when distributing the full Skill set together in Codex CLI (`/plugins`) or desktop workflows. Keep `AGENTS.md` and `okf/` inside your target repository.

### Claude Code

Claude Code discovers standalone Skills under `.claude/skills/<skill>/SKILL.md` (project scope) and `~/.claude/skills/<skill>/SKILL.md` (user scope), pre-loading only `name` and `description` until invoked.

Installation options:

1. **Copy-based (recommended for project customization):** Copy selected folders from `skills/` into `.claude/skills/` in your repository.
2. **Session-scoped plugin (`adapters/claude-code/`):** Load all five canonical Skills in a single command without copying files into the target repository:

```sh
claude --plugin-dir /path/to/okf-skills/adapters/claude-code
```

Plugin Skills are namespaced as `/okf-skills:<skill-name>` (for example, `/okf-skills:implement-feature`) so they do not collide with project-local Skills. You can validate the plugin layout with `claude plugin validate ./adapters/claude-code` and reload edits in-session with `/reload-plugins`. Keep `CLAUDE.md` and `okf/` inside your target repository rather than inside the plugin root.

## Preventing Adapter Drift

Adapter-owned copies are never hand-edited. All host metadata lives in [../adapters/manifest.yaml](../adapters/manifest.yaml), and all Skill bodies are copied byte-for-byte from `skills/*/SKILL.md`:

```sh
# Regenerate adapters/codex/ and adapters/claude-code/
python scripts/sync_adapters.py

# Deterministic CI check (fails on missing, extra, or drifted files)
python scripts/sync_adapters.py --check
```

`scripts/validate_skills.py` also validates every generated `SKILL.md` file alongside canonical `skills/` and `examples/` copies.
