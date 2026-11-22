---
name: git-lore
description: Captures, queries, and configures decision context in native Git trailers. Use for non-trivial commit messages, decisions, rejected alternatives, follow-ups, Lore history queries, pull request decision summaries, or Lore rules in agent instructions.
---

# Git Lore

Preserve decision context beside code by using Git's native commit trailers. Route commit writing and history queries through one skill.

The commit message is the only record. Never write Lore data to git notes, extra refs or branches, or tracked files, and never link a commit to an outside conversation record.

## Route the Request

| Request | Mode |
|---|---|
| Write or perform a non-trivial commit | Commit mode |
| Find decisions, constraints, rejected options, directives, follow-ups, verification gaps, or other Lore data in history | Query mode |
| Check earlier decisions before changing existing code | Query mode |
| Summarize a branch's decisions for a pull request description | Query mode |
| Configure Lore rules in project or global agent instructions | Setup mode |

Repository instructions remain authoritative. Lore supplements existing commit-message rules; it does not replace Conventional Commits, language rules, or repository-specific formats.

## Privacy

Everyone who can read the repository can read a commit message, and a pushed message cannot be taken back. Write every part of it in your own words, from the outcome of the work:

- Never paste or quote the conversation: user prompts, chat excerpts, agent reasoning, or transcripts. Restate what was asked as the goal of the change.
- Never add session IDs, chat or transcript URLs, transcript paths, or a trailer that points to a conversation record.
- Never include secrets, tokens, passwords, credentials, personal data, file contents, or raw command output. A measured result stated in your own words is fine: `Tested:` names the check and its result, not its output.

## Commit Mode

1. Inspect the staged diff and the verified work from the current task. If the user asked for a commit and nothing is staged, stop and report it; do not stage files unless the user authorized staging them. Never stage unrelated files.
2. Collect decision facts from all the work since the previous commit, not only from the last request. When the last request is only "commit it", the decisions came from earlier requests.
3. Write the summary in the repository's required format.
   If none exists, use a locale-appropriate summary that names the resulting
   change: an imperative phrase in English. (or a concise noun phrase in Korean if the user or other rules explicitly want to write in Korean)
   Do not assume Conventional Commits.
4. Write the body:
   - **Intent**: one to three sentences on the problem or goal the change serves and why this approach.
   - **Shape** (optional): see [Shape](#shape).
5. Harvest only decision facts supported by the work. Never invent decisions, constraints, rejected options, or tests. Follow [Decision and Rejected Rules](#decision-and-rejected-rules).
6. Append only useful trailers after a blank line.
7. Re-read the message. Remove trailers that merely restate the diff or the Intent, and check every line against [Privacy](#privacy).
8. If the user requested an actual commit, run `git commit` with the completed message and report the commit hash. If the user requested only a message draft, return the draft without running Git.

Skip the body Shape and the Lore trailers for typo-only, formatting-only, or other trivial commits with no decision context.

### Shape

Shape shows the change from outside, for a reviewer who has not read the diff yet. Pick the one or two forms that say the most, never two that tell the same thing. Start every Shape line with `- ` so Git never parses it as a trailer.

| Form | Use it for | Line format |
|---|---|---|
| Before/after | A fix, a new default, or a rule that now says yes or no | `- <case>: <before> → <after>`, at most 8 lines |
| Interface | A changed command, flag, exported function, config key, or stored field reached from outside the module | `- <item>: <before> → <after>`, `—` for nothing |
| Example | One concrete case with real values; a new or changed command or flag always gets one | `- <input> → <result>` |
| Steps | Logic that stays inside one module | `- 1. <step>`, naming the functions and files |

Skip Shape for a change nobody would notice from outside (a refactor or a rename), for release or version bumps, lockfiles, and CHANGELOG updates, and for changes of fewer than 5 lines.

### Decision and Rejected Rules

- `Decision:` names who decided. `user`: the user chose it. `agreed`: the user explicitly approved a proposal; a proposal the user did not answer is not a decision. `agent`: a technical choice made within the task. Add it only for a choice that a future modifier could reverse.
- `Rejected:` lists only options that the user or the agent actually considered before the decision: named in the discussion, tried, or measured. Never infer an alternative from the decision, never list the current state as one, and never add durations, sizes, or reasons that the work does not support. A postponed option is not rejected; record it as `Follow-up:` when it stays open.
- Both cover the product and the code only, not how the work was run: which tool, agent, or model did it, or when to post or release.

### Trailer Vocabulary

| Trailer | Content |
|---|---|
| `Decision:` | Choice, reason, and who decided, as `choice \| reason \| user, agreed, or agent` |
| `Constraint:` | External limit that shaped the decision |
| `Rejected:` | Rejected alternative and reason as `alternative \| reason` |
| `Confidence:` | `high`, `medium`, or `low` |
| `Scope-risk:` | `narrow`, `moderate`, or `broad` |
| `Reversibility:` | `clean`, `moderate`, or `difficult` |
| `Directive:` | Warning or prerequisite for future modifiers |
| `Tested:` | Verification that ran |
| `Not-tested:` | Known verification gap |
| `Follow-up:` | Work that came up and stays open; end it with `(needs user)` when its next step needs the user's decision or action |
| `Related:` | Related commit hash or decision chain |

Trailers are optional and repeatable. Add a custom trailer only when the repository has a recurring query need for it.

### Message Template

```text
<repository-compliant summary>

<Intent: the goal and why this approach>

<optional Shape lines, each starting with "- ">

Decision: <choice> | <reason> | <user | agreed | agent>
Constraint: <external limit>
Rejected: <alternative> | <reason>
Confidence: <high | medium | low>
Scope-risk: <narrow | moderate | broad>
Reversibility: <clean | moderate | difficult>
Directive: <future warning>
Tested: <verification>
Not-tested: <known gap>
Follow-up: <open work> (needs user)
Related: <commit>
```

Example:

```text
Rotate refresh tokens on use

A leaked refresh token kept working until it expired. Each refresh now
issues a new token pair and revokes the used token.

- reused refresh token: accepted → whole token family revoked
- second refresh from another tab within 30 s: accepted → accepted

Decision: Keep a used token valid for 30 seconds | two tabs refresh at the same time | agreed
Rejected: Shorten the token lifetime | signs people out too often
Tested: Auth refresh unit tests (12/12 pass)
Follow-up: Add a revocation count to the auth dashboard (needs user)
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

Ask which agent the user uses only when it cannot be detected. Read the target first. If it already has a Lore section, do not add a duplicate; when that section differs from the block below, show the difference and ask before replacing it.

Append this block:

~~~markdown
## Commit Messages: Lore Format

For non-trivial changes, write a repository-compliant summary that names the
resulting change. Use an imperative phrase. Add a body with the goal and why
this approach. When a reviewer would notice the change from outside, add a few
lines that start with "- " and show it (before → after, a changed interface,
or one example). Then append only useful Git trailers:

- Decision: choice, reason, and who decided (user, agreed, or agent), separated by vertical bars
- Constraint: external limit that shaped the decision
- Rejected: alternative actually considered before the decision, and reason, separated by a vertical bar
- Confidence: high, medium, or low
- Scope-risk: narrow, moderate, or broad
- Reversibility: clean, moderate, or difficult
- Directive: warning or prerequisite for future modifiers
- Tested: verification that ran
- Not-tested: known verification gap
- Follow-up: work that stays open, ending with "(needs user)" when its next step needs the user
- Related: linked commit or decision chain

Trailers are optional and repeatable. Skip them for typo-only, formatting-only, and other trivial commits.
Write every part in your own words. Never put conversation text, prompts,
session IDs, chat links, secrets, personal data, file contents, or raw command
output in a commit message.
Before a non-trivial change to existing code, read the Directive, Constraint,
and Decision trailers on the paths you will change. Change a user or agreed
decision only with the user's approval.
~~~

After writing, report the target path. For project scope, remind the user that the instruction file should be committed.

## Query Mode

Treat this mode as read-only. Never amend, rebase, or otherwise rewrite history. Read only commit messages.

### Map Common Names

| User phrase | Trailer |
|---|---|
| 결정, decision | `Decision` |
| 제약조건, constraints | `Constraint` |
| 리젝, rejected | `Rejected` |
| 디렉티브, directive | `Directive` |
| 후속, 남은 일, follow-up | `Follow-up` |
| 미테스트, not-tested | `Not-tested` |
| 테스트, tested | `Tested` |
| 신뢰도, confidence | `Confidence` |
| 범위위험, scope-risk | `Scope-risk` |
| 가역성, reversibility | `Reversibility` |
| 관련, related | `Related` |

Treat an unrecognized name as a custom trailer. Preserve it exactly except for one trailing colon. Use it only when it matches `[A-Za-z][A-Za-z0-9-]*`; otherwise ask for the trailer name, because the name becomes part of a `--grep` pattern.

### Run the Query

For one trailer, run:

```bash
git log -n 20 --all --grep="^TRAILER:" --format="%h %s%n%b" -- [PATH]
```

Replace `TRAILER` with the mapped name. Omit `-- [PATH]` when no path was requested. Pass the path as a quoted argument; do not build or execute a shell string from user input. Repeat `--grep` to match any of several trailers.

For example, query rejected alternatives under `src/auth/` with:

```bash
git log -n 20 --all --grep="^Rejected:" --format="%h %s%n%b" -- "src/auth/"
```

For a summary, run:

```bash
git log -n 20 --all --format="%h %s%n%b" -- [PATH]
```

Keep commits containing known Lore trailers. Default to 20 commits unless the user specifies another limit.

### Before Changing Code

Before a non-trivial change to existing code, query the paths you will change:

```bash
git log -n 20 --grep="^Directive:" --grep="^Constraint:" --grep="^Decision:" --format="%h %s%n%b" -- [PATH]...
```

This reads only the current branch's history, because a decision on an unmerged branch does not bind this code. Follow the directives and constraints you find. Change a `user` or `agreed` decision only with the user's approval, and say which commit recorded it.

### Summarize a Branch for a Pull Request

Use the pull request's base branch as `BASE`; without one, use the remote's default branch. Run:

```bash
git log --reverse --format="%h %s%n%b" "BASE..HEAD"
```

Write the description from those messages only:

```markdown
## Goal
<one or two sentences merged from the commits' Intent>

## Decisions
- <choice>: <reason> (<who decided>) `<hash>`
  - Rejected: <alternative>: <reason>

## Open
- <Follow-up or Not-tested> `<hash>`
```

Omit a section that has no entries. List commits without Lore trailers under `## Commits without recorded decisions` only when they change more than formatting or versions.

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
eed689c27adbf9dab3f13c07ad3d95b217ed1454. The upstream README declares MIT.

The Intent, Shape, decision owner, rejected-option, follow-up, and pull
request summary rules adapt ideas from
[erensrtky/cogit](https://github.com/erensrtky/cogit) at revision
151b25e209555f6e288c7217c02b7fb969df14c2 (MIT). cogit keeps its record outside
the branch history; this skill keeps the same information in the commit
message. See THIRD_PARTY_NOTICES.md.
