---
name: git-lore
description: Captures, queries, and configures decision context in native Git trailers. Use for non-trivial commit messages, constraints, rejected alternatives, directives, test gaps, Lore history queries, or installing Lore rules in project or global agent instructions.
---

# Git Lore

Preserve decision context beside code by using Git's native commit trailers. Route commit writing and history queries through one skill.

## Route the Request

| Request | Mode |
|---|---|
| Write or perform a non-trivial commit | Commit mode |
| Find constraints, rejected options, directives, verification gaps, or other Lore data in history | Query mode |
| Configure Lore rules in project or global agent instructions | Setup mode |

Repository instructions remain authoritative. Lore supplements existing commit-message rules; it does not replace Conventional Commits, language rules, or repository-specific formats.

## Commit Mode

1. Inspect the staged diff and the verified work from the current task. If nothing is staged, stop and report it; do not stage files unless the user authorized staging them. Never stage unrelated files.
2. Write the summary and body in the repository's required format.
   If none exists, use a locale-appropriate summary that names the resulting
   change: a concise noun phrase in Korean or an imperative phrase in English.
   Add an optional body explaining why; do not assume Conventional Commits.
3. Harvest only decision facts supported by the work. Never invent constraints, rejected options, or tests.
4. Append only useful trailers after a blank line.
5. Re-read the message and remove trailers that merely restate the diff.
6. If the user requested an actual commit, run `git commit` with the completed message and report the commit hash. If the user requested only a message draft, return the draft without running Git.

Skip Lore trailers for typo-only, formatting-only, or other trivial commits with no decision context.

### Trailer Vocabulary

| Trailer | Content |
|---|---|
| `Constraint:` | External limit that shaped the decision |
| `Rejected:` | Rejected alternative and reason as `alternative \| reason` |
| `Confidence:` | `high`, `medium`, or `low` |
| `Scope-risk:` | `narrow`, `moderate`, or `broad` |
| `Reversibility:` | `clean`, `moderate`, or `difficult` |
| `Directive:` | Warning or prerequisite for future modifiers |
| `Tested:` | Verification that ran |
| `Not-tested:` | Known verification gap |
| `Related:` | Related commit hash or decision chain |

Trailers are optional and repeatable. Add a custom trailer only when the repository has a recurring query need for it.

### Commit Shape

```text
<repository-compliant summary>

<optional body explaining why or how>

Constraint: <external limit>
Rejected: <alternative> | <reason>
Confidence: <high | medium | low>
Scope-risk: <narrow | moderate | broad>
Reversibility: <clean | moderate | difficult>
Directive: <future warning>
Tested: <verification>
Not-tested: <known gap>
Related: <commit>
```

## Setup Mode

Configure agent instructions so future sessions write Lore trailers without requiring this skill to be invoked for each commit.

1. Ask whether the scope is project or global.
2. Detect the active agent CLI and select its normal instruction file:

| Agent CLI | Project | Global |
|---|---|---|
| Claude Code | CLAUDE.md or AGENTS.md | ~/.claude/CLAUDE.md |
| Codex CLI | AGENTS.md | ~/.codex/AGENTS.md |
| Kimi Code | AGENTS.md | ~/.agents/AGENTS.md |
| Qwen Code | QWEN.md | ~/.qwen/QWEN.md |
| Universal fallback | AGENTS.md | ~/.agents/AGENTS.md |

Ask which agent the user uses only when it cannot be detected. Read the target first. If it already has a Lore section, do not add a duplicate.

Append this block:

~~~markdown
## Commit Messages: Lore Format

For non-trivial changes, write a repository-compliant summary that names the
resulting change. Use a concise noun phrase for Korean and an imperative phrase
for English. Add an optional explanatory body, then append only useful Git
trailers:

- Constraint: external limit that shaped the decision
- Rejected: alternative and reason, separated by a vertical bar
- Confidence: high, medium, or low
- Scope-risk: narrow, moderate, or broad
- Reversibility: clean, moderate, or difficult
- Directive: warning or prerequisite for future modifiers
- Tested: verification that ran
- Not-tested: known verification gap
- Related: linked commit or decision chain

Trailers are optional and repeatable. Skip them for typo-only, formatting-only, and other trivial commits.
~~~

After writing, report the target path. For project scope, remind the user that the instruction file should be committed.

## Query Mode

Treat this mode as read-only. Never amend, rebase, or otherwise rewrite history.

### Map Common Names

| User phrase | Trailer |
|---|---|
| 제약조건, constraints | `Constraint` |
| 리젝, rejected | `Rejected` |
| 디렉티브, directive | `Directive` |
| 미테스트, not-tested | `Not-tested` |
| 테스트, tested | `Tested` |
| 신뢰도, confidence | `Confidence` |
| 범위위험, scope-risk | `Scope-risk` |
| 가역성, reversibility | `Reversibility` |
| 관련, related | `Related` |

Treat an unrecognized name as a custom trailer. Preserve it exactly except for one trailing colon.

### Run the Query

For one trailer, run:

```bash
git log -n 20 --all --grep="^TRAILER:" --format="%h %s%n%b" -- [PATH]
```

Replace `TRAILER` with the mapped name. Omit `-- [PATH]` when no path was requested. Pass the path as a quoted argument; do not build or execute a shell string from user input.

For example, query rejected alternatives under `src/auth/` with:

```bash
git log -n 20 --all --grep="^Rejected:" --format="%h %s%n%b" -- "src/auth/"
```

For a summary, run:

```bash
git log -n 20 --all --format="%h %s%n%b" -- [PATH]
```

Keep commits containing known Lore trailers. Default to 20 commits unless the user specifies another limit.

### Present Results

Group by commit and show the short hash, summary, and matching trailer lines:

```text
a1b2c3d Prevent silent session drops
  Constraint: Auth service does not support token introspection
  Directive: Verify upstream behavior before narrowing 4xx handling
```

State clearly when no matching trailers exist.

## Upstream

This skill adapts the commit, query, and setup workflows from
[tmdgusya/lora](https://github.com/tmdgusya/lora) at revision
eed689c27adbf9dab3f13c07ad3d95b217ed1454. The upstream README declares MIT;
see THIRD_PARTY_NOTICES.md.
