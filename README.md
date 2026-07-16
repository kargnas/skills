# kargnas/skills

Agent skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Codex, and [OpenCode](https://opencode.ai). Each skill is a self-contained `skills/<name>/SKILL.md` folder following the standard agent-skills layout, so any tool that reads that layout can consume this repo.

## Install

Using [`npx skills`](https://github.com/vercel-labs/skills) (works for Claude Code, Codex, OpenCode, and more):

```bash
# All skills
npx -y skills add kargnas/skills

# One skill
npx -y skills add kargnas/skills --skill ai-ready
```

Claude Code native plugin path:

```
/plugin marketplace add kargnas/skills
/plugin install kargnas-skills@kargnas/skills
```

## Skills

| Skill | What it does |
|---|---|
| `ai-ready` | Transforms a project into an AI-ready codebase — AGENTS.md migration, `.env.ai-ready` setup, static analysis and test debugging, CI workflows, and README refresh |
| `vscode-ready` | Scaffolds one-click VS Code/Cursor debug and task configs (launch.json, tasks.json, settings.json) from the detected stack |
| `skill-manager` | Create, evaluate, harden, and merge agent skills — includes guides for anti-patterns, modular architecture, and importing external skills |
| `skill-prompter` | Rewrites skill descriptions and step prompts for reliable triggering and compliance — includes rewrite patterns and a compliance checklist |

## Contributing

PRs are welcome. Rules:

1. One skill per `skills/<name>/` folder with a `SKILL.md` (YAML frontmatter: `name`, `description`).
2. Keep skills self-contained — reference files go under the skill's own `references/`, scripts under `scripts/`.
3. No secrets, no personal data, no company-internal URLs. English for `SKILL.md` body.

## License

[PolyForm Noncommercial 1.0.0](LICENSE) — free for personal, research, and other noncommercial use. Commercial use requires a separate license from the author.

Note: `skills/skill-manager` contains portions derived from Anthropic's skill-creator (Apache-2.0); see `skills/skill-manager/LICENSE.txt`.
