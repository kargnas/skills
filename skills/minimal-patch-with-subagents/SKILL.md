---
name: minimal-patch-with-subagents
description: Minimal patching workflow that debates fix options across parallel independent subagents and applies the smallest safe diff. Use for the smallest safe fix to a confirmed bug when you want multiple reviewers to converge on the least-risky patch location before editing.
---

# Minimal Patch with Subagents

Minimal patch workflow for any git repository. Goal: fix the confirmed problem with the fewest necessary changes while preserving existing behavior and keeping review risk low. Fix options are debated across 3-5 parallel independent subagents that vote on the least-risky patch location before any edit.

## Core Principle

This is a **minimal-scope** fix. It may be temporary or permanent, but every decision optimizes for:
1. **Fewest logic files in `git status`** (ideal: 1, max: 2) — **PRIMARY METRIC**
2. **Smallest effective diff** = `logic_lines − 0.3 × (comment_lines + md_lines)`, floor 0
3. **Lowest regression risk** for nearby behavior
4. **Fast, focused verification** proportional to the change

**The single source of truth is `git diff` on uncommitted changes.** Every edit decision MUST be justified against the current git diff output. If a file appears in `git status` that shouldn't, it's a scope violation.

**Comments + Markdown docs have NEGATIVE weight — more is strictly better.** Code comments and `.md` file edits (README, AGENTS.md, CHANGELOG, debate logs, etc.) don't just escape the budget — they *actively shrink* the effective patch size. Formula:

> `effective_lines = logic_lines − 0.3 × (comment_lines + md_lines)`  (floor at 0)

A 10-line logic patch with 20 comment lines + 10 md lines scores `10 − 0.3 × 30 = 1` — effectively a 1-line patch. The 30% cap is intentional: docs can dominate *perceived* risk delta but never fully erase real behavioral change. Comments tell the next reader *why* the fix exists; `.md` updates carry context across sessions, devs, and future AI agents. Both are insurance against re-debugging the same bug 3 months later.

**Scope of the bonus**: explanatory context only — "why this fix", "what the bug was", "what to watch on next sync", risk notes, AGENTS.md patch log entries. NOT new feature docs, marketing copy, or unrelated doc refactors (those are scope creep wearing a doc costume).

`.md` files that contain only docs/context updates also do NOT count toward the file-in-`git status` budget. The file budget tracks files with *logic* changes.

## Git Change Tracking (NON-NEGOTIABLE)

Throughout the entire workflow, the orchestrator MUST:

1. **Before starting**: Run `git status` and `git diff --stat` to establish baseline (should be clean, or note pre-existing changes).
2. **After every edit**: Run `git diff --stat` to verify only intended files changed.
3. **Before presenting results**: Run `git diff --stat` and `git diff` to confirm final scope.
4. **If unexpected files appear**: Immediately revert unintended changes before proceeding.

### Change Budget

The budget is measured by **logic files in `git status`** (primary) and **effective lines changed** (secondary). Whitespace-only changes are always excluded. Comments and `.md` doc changes count *negatively* via the 30% discount above.

| Severity | Max logic files in `git status` | Max **effective** lines changed |
|----------|----------------------------------|---------------------------------|
| Ideal    | 1                                | < 10                            |
| Acceptable | 2                              | < 25                            |
| Needs justification | 3                     | < 50                            |
| BLOCKED — ask user | 4+                     | 50+                             |

> Docs-only `.md` files (AGENTS.md context update, debate log, README note) don't count toward the file budget — only files with runtime-behavior changes do.

> **Comments and `.md` doc edits carry NEGATIVE weight — the more you add, the lower (better) the score.** Comment/`.md` lines are discounted from `effective_lines` at 30% (`effective = logic − 0.3 × (comments + md)`, floor 0). Example: 10 logic lines + 30 comment/doc lines = an effective 1-line patch. The more minimal the patch, the more richly you MUST record "why it was fixed this way", "what the original bug was", and "how it could be improved later" in comments and AGENTS.md / README. A minimal patch with no comments or docs is a time bomb. But the 30% cap means a doc dump can never hide real logic risk. And this bonus applies ONLY to docs that explain *this* patch's context — writing new feature docs or doing unrelated doc refactors is scope creep in disguise.

If the change exceeds "Acceptable" in **effective lines**, STOP and ask the user before proceeding.

## Workflow

The orchestrator MUST execute every step below in order. Do NOT skip any step. Each step ends with a VERIFY gate; do NOT advance past a step until its VERIFY succeeds.

### Step 1 [S1]: Capture Git Baseline

**Action**: MUST run `git status --porcelain` and `git diff --stat` in the repo root via the Bash tool.

Record two values for later steps:
- `baseline_clean`: true if both commands output empty, else false
- `pre_existing_files`: list of paths from `git status --porcelain`

**VERIFY**: Both git commands exited with code 0. `baseline_clean` and `pre_existing_files` are recorded.

**IF BLOCKED**: Not inside a git repo (git reports "fatal: not a git repository") → STOP and tell the user "minimal-patch requires a git repo".

---

### Step 2 [S2]: Read the Bug Report

**Action**: MUST read the user's bug description in full. If the user referenced a log file or session path, MUST use the `Read` tool on that path.

Extract and record:
- `symptom`: 1-line summary of what the user observes (verbatim phrasing where possible)
- `affected_artifacts`: filenames, log paths, session IDs, error strings (verbatim)
- `reproduction_steps`: if provided; else "none"

**VERIFY**: `symptom` is a non-empty string. `affected_artifacts` is a list (may be empty if user gave only a description).

**IF BLOCKED**: Bug description is too vague to extract a single `symptom` → MUST ask the user exactly one clarifying question before advancing.

---

### Step 3 [S3]: Quantify Bug Scope

**Action**: Apply this decision table to decide whether to delegate:

| Condition | Action |
|-----------|--------|
| `affected_artifacts` includes log/session paths OR symptom mentions "multiple / recurring / many" | MUST delegate to subagent (see below) |
| Artifacts are inline in the user's message; no scan needed | MAY skip subagent; record inline evidence directly into `evidence_table` |

**DELEGATE TO SUBAGENT** (Agent tool, `subagent_type: Explore`):
  Task: "Scan the artifacts listed and count occurrences of the symptom. Report each occurrence as a row."
  Input: `symptom` from [S2], `affected_artifacts` from [S2].
  Expected output: A markdown table `| File | Line | Timestamp | Excerpt |` with ≥ 1 row, plus a final `total: N` line.
  Max tokens: 4000.
  **IF TIMEOUT**: Subagent does not return within 120s → SHOULD grep the top 1–2 most-likely paths manually and record partial evidence.

**VERIFY**: `evidence_table` has ≥ 1 row. `occurrence_count` is an integer ≥ 1.

**IF BLOCKED**: Zero occurrences found in any artifact → STOP. Tell the user "cannot confirm bug exists; refusing to patch an unconfirmed bug." Do NOT proceed.

---

### Step 4 [S4]: Trace Root Cause to Exact Files

**Action**: MUST identify the exact files and functions where the bug originates. Apply this decision table:

| Condition | Action |
|-----------|--------|
| Files in `evidence_table` are familiar AND root cause obvious | MAY trace inline by reading 1–2 files with `Read` |
| Codebase unfamiliar OR call chain spans 3+ files | MUST delegate to subagent (see below) |

**DELEGATE TO SUBAGENT** (Agent tool, `subagent_type: Explore`):
  Task: "Given the symptom and evidence, trace the code path from symptom to root cause. Report every step in the path."
  Input: `symptom`, `evidence_table`, repo root path.
  Expected output: A markdown list, each item `path:function — role in the bug path`.
  Max tokens: 4000.
  **IF TIMEOUT**: Subagent does not return within 180s → SHOULD manually `Read` the file with the highest occurrence count in `evidence_table` and record at least one `path:function` entry.

**VERIFY**: `root_cause_path` lists ≥ 1 `path:function` entry. Spot-check: `Read` one entry's file and confirm the function exists at the named path.

---

### Step 5 [S5]: Forecast Change Plan

**Action**: MUST write a 5-line forecast block as a code block in your reasoning. Substitute concrete numbers — do NOT leave a formula unevaluated:

```text
expected_logic_files: [file1, file2]
expected_logic_lines: N
expected_comment_lines: C
expected_md_lines: D
expected_effective_lines: max(0, N − 0.3 × (C + D))   # compute the number
```

**VERIFY**: All 5 fields are filled with concrete values. `expected_effective_lines` is a number (not a formula). The value matches the Change Budget table row (Ideal / Acceptable / etc.).

**IF BLOCKED**: Cannot decide between 2+ files → MUST proceed to [S6] with all candidates as debate options.

---

### Step 6 [S6]: Define Fix Options for Debate

**Action**: MUST enumerate 2–4 distinct fix locations as rows of this table:

| Option | Files touched | One-line description |
|--------|---------------|----------------------|
| A | {file A} | Fix at choke-point A only |
| B | {file B} | Fix at call-site B only |
| C | {file A, file B} | Both layers |
| D (optional) | {other} | Alternative not in A/B/C |

**VERIFY**: `options_table` has 2 to 4 rows. Every row has non-empty `Files touched` AND non-empty `description`. No two options are identical.

---

### Step 7 [S7]: Launch Parallel Debater Subagents

**Action**: MUST launch exactly N parallel subagents where 3 ≤ N ≤ 5. MUST send a single message with multiple Agent tool calls so they run concurrently.

For each debater, use this exact prompt template — substitute `{BUG_NAME}`, `{symptom}`, `{evidence_table}`, `{options_table}`, `{repo_path}`:

```text
ROLE: Independent reviewer
GOAL: Pick the minimal safe patch for {BUG_NAME}.
      PRIMARY METRIC: fewest logic files in `git status` after the fix.

CONTEXT:
  Symptom: {symptom}
  Evidence: {evidence_table}
  Repo: {repo_path}

OPTIONS:
{options_table}

INSTRUCTIONS:
1. Read the actual source under the listed files.
2. Evaluate each option on:
   - bug_fully_stopped (yes/no)
   - logic_files_in_git_status (count; docs-only .md files excluded)
   - effective_lines = logic − 0.3 × (comments + md), floor 0
   - merge_conflict_risk (Low / Medium / High)
   - edge_cases_missed (list)
3. The winner MUST plan rich `why`-comments AND a `.md` context update — both carry NEGATIVE 30% weight.
4. Be opinionated. Pick exactly one winner.

OUTPUT (must be valid markdown, exactly these fields):
- winner: A/B/C/D
- logic_files_in_git_status: N
- effective_lines: ~N (= logic L − 0.3 × (comments C + md D), floor 0)
- planned_comments: ~C lines
- planned_md_updates: ~D lines
- why: 1-2 sentences
- exact_change: minimal diff description
- risk: what could still go wrong
```

**VERIFY**: Exactly N subagent responses returned. Each response contains all 8 OUTPUT fields. No `winner` field is empty.

**IF TIMEOUT**: A subagent does not return within 300s → MUST proceed with the remaining responses if at least 3 returned. If fewer than 3 returned, MUST re-launch the missing ones once with a 180s timeout.

---

### Step 8 [S8]: Compute Consensus

**Action**: Tally the `winner` field across all N debater responses. Apply this decision table in order; use the first row that matches:

| Vote distribution | Action |
|-------------------|--------|
| Unanimous (N/N for one option) | Set `consensus_winner` to that option |
| Clear majority (≥ ⌈N/2⌉+1 for one option) | Set `consensus_winner` to that option |
| Split with no majority AND a minority response names a valid bypass/edge-case the majority missed | Set `consensus_winner` to the minority option that closes the bypass |
| Split with no majority AND no minority closes a bypass | Pick the option with the smallest `effective_lines` |
| Tie on `effective_lines` | Pick the option with the highest `planned_comments + planned_md_updates` |

**VERIFY**: `consensus_winner` is set to exactly one of A/B/C/D. `consensus_rationale` records (1 line) which decision-table row was used.

---

### Step 9 [S9]: Present Forecast to User

**Action**: MUST print the following block to the user verbatim (substituting recorded values):

```text
📋 Minimal Patch — Debate Result
- Winner: {consensus_winner}   (votes: {tally})
- Rationale: {consensus_rationale}
- Expected `git status`: {logic_file_count} logic file(s) + {md_file_count} docs file(s)
- Expected effective lines: ~{E}   (= logic {L} − 0.3 × (comments {C} + md {D}))
- Risk notes: {top 1-2 minority concerns, or "none"}
```

**VERIFY**: The block is printed to the user channel (visible to the user, not only internal reasoning).

**IF BLOCKED**: `expected_effective_lines` exceeds the "Acceptable" budget (≥ 25) → MUST ask the user for explicit approval before advancing to [S10].

---

### Step 10 [S10]: Re-confirm Baseline Right Before Editing

**Action**: MUST run `git status --porcelain` again via Bash, immediately before the first Edit.

**VERIFY**: Output matches `pre_existing_files` from [S1]. No new files have appeared.

**IF BLOCKED**: New files appeared between [S1] and now → MUST surface the delta to the user and STOP. Do NOT silently proceed.

---

### Step 11 [S11]: Apply the Patch

**Action**: MUST apply changes using the `Edit` tool (or `Write` only for genuinely new files). Constraints:

- Every Edit MUST target a path in `expected_logic_files` from [S5] OR an explanatory `.md` path planned in `expected_md_lines`.
- MUST include inline `why`-comments alongside the logic changes (the 30% bonus only applies if comments actually ship).
- MUST NOT touch any file not forecast in [S5].

**VERIFY**: Every Edit/Write tool call returned success. The set of paths actually edited is a subset of `expected_logic_files ∪ expected_md_files`.

**IF BLOCKED**: An `Edit` fails because `old_string` is non-unique → SHOULD enlarge `old_string` with surrounding context until unique. MUST NOT use `replace_all` unless the change is genuinely a rename.

---

### Step 12 [S12]: Verify Diff Stat Against Forecast

**Action**: MUST run `git diff --stat` via Bash. Compare actual against [S5] forecast using this decision table; use the first row that matches:

| Comparison | Action |
|------------|--------|
| Files match `expected_logic_files` AND `effective_lines` within ±20% of forecast | Proceed to [S14] |
| Unexpected file appears in `git status` | Go to [S13] (revert + reapply) |
| `effective_lines` exceeds forecast by > 20% | Go to [S13] (revert + reapply with tighter scope) |
| `effective_lines` falls short of forecast by > 50% (under-fixed) | SHOULD re-run [S4] — may indicate missed entry point. Then return to [S11] |

**VERIFY**: One row of the comparison table is selected and recorded as `diff_stat_result`.

---

### Step 13 [S13]: Revert Unintended Changes (Conditional)

**Action**: Triggered only when [S12] selected the "Unexpected file" or "exceeds by >20%" row.

For each unintended path, apply this decision table:

| Condition | Action |
|-----------|--------|
| Path existed in HEAD before the patch | MUST run `git checkout -- {path}` to drop ONLY that path |
| Path is newly created (not in HEAD) AND was NOT in `pre_existing_files` from [S1] | MUST `rm {path}` |
| Path is a user-modified file from `pre_existing_files` | MUST NOT touch. Instead `git restore --staged {path}` and skip — user's pre-existing changes are off-limits |

**MUST NOT** run `git reset --hard`, `git checkout .`, or `git clean -f` — they touch unrelated work.

**VERIFY**: `git status --porcelain` no longer lists the unintended path. All paths in `pre_existing_files` from [S1] remain present and unchanged.

After revert, MUST return to [S11] and re-apply more carefully.

---

### Step 14 [S14]: Run Targeted Verification

**Action**: MUST pick exactly ONE verification command proportional to the change. Apply this decision table; use the first matching row:

| Change type | Verification command |
|-------------|----------------------|
| Logic in a function with tests nearby | Run the targeted test only (e.g., `pytest path/to/test_x.py::test_y`, `npx vitest path/to/x.test.ts`, `mix test path/to/x_test.exs:42`) |
| Type-only change | Run typecheck on the package (e.g., `pnpm tsc --noEmit`, `mypy path/`, `mix dialyzer`) |
| Build-affecting change | Run the build target (e.g., `pnpm build`, `cargo build`, `mix compile --warnings-as-errors`) |
| Reproducible runtime bug with a known repro | Re-run the reproduction command from [S2] and confirm the symptom is gone |
| Docs-only patch (rare for minimal-patch) | Run markdown lint / link check if available; else skip with a recorded reason |

**VERIFY**: Selected command exits with code 0 (or, for reproduction, the symptom is gone in the new output).

**IF BLOCKED**: Verification fails AND the errors map to lines you just changed → MUST return to [S11] to refine. If errors are pre-existing (also fail on `git stash` of the patch), SHOULD note them but proceed.

---

### Step 15 [S15]: Print Final Footprint Summary

**Action**: MUST run `git diff --stat` one final time and print this block to the user (substituting recorded values):

```text
📊 Git Change Summary
- Logic files: {N}        ({list})
- Docs (.md) files: {M}    ({list})
- Insertions: +{ins}
- Deletions: −{del}
- Comment lines added: {C}
- Effective lines: ~{E}   (= logic {L} − 0.3 × (comments {C} + md {D}))
{raw git diff --stat output}
```

**VERIFY**: The block is printed to the user channel. The printed `Effective lines` value is within ±20% of `expected_effective_lines` from [S5].

---

### Step 16 [S16]: Update Project Memory (Conditional)

**Action**: Apply this decision table; use the first matching row:

| Repo state | Action |
|------------|--------|
| `AGENTS.md` exists at repo root | MUST append a patch log entry to it |
| A docs/patches log file exists (per repo convention) | MUST append entry there |
| Neither exists AND `expected_effective_lines` ≥ 10 | SHOULD create `AGENTS.md` at repo root with a single-entry log section |
| Neither exists AND `expected_effective_lines` < 10 | MAY skip; record reason "trivial patch, no log file present" |

Entry template (MUST use exactly these labels):
```markdown
### {YYYY-MM-DD} — {one-line title}
- **File(s)**: {from git diff --stat}
- **Symptom**: {one line}
- **Root cause**: {one line}
- **Fix**: {one line}
- **Verification**: {command from S14}
- **Follow-up**: {"permanent" | "temporary, revisit when …"}
```

**VERIFY**: Either an entry was appended (and `git diff --stat` now lists the AGENTS.md change) OR the skip path was logged with reason.

---

### Step 17 [S17]: Save Debate Log

**Action**: MUST write a debate log to `{skill_dir}/logs/{YYYY-MM-DD_HH-MM-SS}_{short-bug-slug}.md` where `{skill_dir}` is the directory containing this SKILL.md.

Log MUST follow this template:
```markdown
# Minimal Patch Debate Log
- **Date**: YYYY-MM-DD HH:MM:SS
- **Orchestrator Model**: {model id, e.g. claude-opus-5}
- **Bug**: {one-line description}
- **Repo**: {repo path}

## Agents & Votes
| Agent | Model | Winner | Logic Files | Effective Lines | Planned Comments+MD | Rationale |
|-------|-------|--------|-------------|------------------|---------------------|-----------|
| Agent 1 (type) | {model id} | A/B/C/D | N | ~E (= L − 0.3×(C+D)) | C+D | 1-2 sentences |
| Agent 2 (type) | {model id} | A/B/C/D | N | ~E | C+D | … |
| …             | …          | …       | … | …               | …    | … |

## Options Considered
- **A)** {desc}
- **B)** {desc}
- **C)** {desc} (if any)
- **D)** {desc} (if any)

## Final Decision
- **Winner**: {option} (votes: N/M)
- **Decision-table row used**: {row name from S8}
- **Dissent**: {minority concerns, or "none"}
- **Files changed (logic / docs)**: {two lists}
- **Effective lines**: ~E (= logic L − 0.3 × (comments C + md D))

## Risk Notes
- {what could still go wrong}
- {follow-up if temporary}
```

> This log is an audit record: when the same bug recurs, it traces "what discussion led to this decision last time."

**VERIFY**: The log file exists at the expected path. `git log` is NOT touched (the log is local audit-only, never staged). File size > 200 bytes.

**IF BLOCKED**: `{skill_dir}/logs/` does not exist → MUST create it via `mkdir -p` first, then write the file.

---

### Step 18 [S18]: Stage Patch Files (Commit Reserved for User)

**Action**: MUST stage ONLY the files in `expected_logic_files ∪ expected_md_files` from [S5]. Use explicit paths: `git add path1 path2 …`.

Hard rules:
- MUST NOT run `git add .` or `git commit -a`.
- MUST NOT stage the debate log under `{skill_dir}/logs/`.
- MUST NOT stage anything in `pre_existing_files` from [S1] unless that file was an intentional target of this patch.

**VERIFY**: `git diff --cached --name-only` lists exactly the expected patch files, no extras. The debate log path is absent from staged output.

**IF BLOCKED**: A pre-existing user-touched file accidentally has the patch's hunks mixed in → MUST run `git reset HEAD {path}` to unstage, then `git add -p {path}` to stage only the relevant hunks.

Commit only if the user explicitly requested a commit. If they did, follow the repo's `AGENTS.md` commit conventions; default to Conventional Commits `fix: <one-line>` with the appropriate `Co-authored-by:` footer.

---

## Anti-Patterns

- ❌ Touching 3+ files for a fix that should be localized
- ❌ Modifying shared utilities when a call-site fix suffices
- ❌ "Defense in depth" with multiple layers when one choke-point fix is enough
- ❌ Sneaking in refactors, cleanup, or style churn unrelated to the bug
- ❌ Counting comment or `.md` doc additions as "scope creep" — both carry NEGATIVE 30% weight, more is strictly better (within the explanatory-only scope)
- ❌ Minimal patch WITHOUT `why`-comments AND without an AGENTS.md/README context entry — unacceptable; future devs and AI agents won't understand the fix
- ❌ Padding `.md` files with unrelated content to game the 30% discount — bonus applies only to fix-context docs, not feature docs or doc refactors
- ❌ **Skipping `git diff --stat` after edits** — this is how scope creep goes undetected
- ❌ **Using `git add .`** — always stage specific files only
- ❌ **Formatter/linter auto-fix touching unrelated lines** — revert those before committing

## Decision Heuristics

When agents disagree on fix location:

| Signal | Prefer |
|--------|--------|
| One option has fewer logic files in `git status` | Fewer files |
| One option fixes the narrow failing path, another broadens behavior | Narrow fix |
| One option blocks all entry points, other misses a bypass | Complete blocker |
| Both equal on above | Smaller effective diff wins (= logic − 0.3 × (comments + md)) |
| Tied on effective diff | Option with richer `why`-comments / AGENTS.md context wins |

## Output Checklist

Before presenting the final plan, MUST confirm every item:

- [ ] Vote tally from all agents recorded (S8)
- [ ] Winner option with logic-file count + effective line count (= logic − 0.3 × (comments + md)) (S9)
- [ ] Any dissenting edge case addressed in `consensus_rationale` (S8)
- [ ] `git diff --stat` matches expected effective-line budget (S12, S15)
- [ ] No unintended files in `git status` (docs-only `.md` changes are encouraged, not penalized) (S12)
- [ ] At least one `why`-comment in the patched code AND a context line in AGENTS.md / README (or equivalent) (S11, S16)
- [ ] Verification passes (S14)
- [ ] Debate log saved to `{skill_dir}/logs/` with full vote breakdown (S17)
- [ ] Staged files scoped to patch files only (`git add <specific files>`, NOT `git add .`) (S18)
