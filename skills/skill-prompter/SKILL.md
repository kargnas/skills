---
name: skill-prompter
description: "Prompting compliance specialist for AI agent skills — rewrites SKILL.md steps with RFC 2119 wording, explicit tools, VERIFY gates, and dry-run checks; also owns skill name + frontmatter description wording (trigger-surface rules). Use when skill steps get skipped, prompts need compliance hardening, or a skill needs naming or its description written/reviewed. Structural lifecycle work goes to skill-manager."
---

# Skill Prompter

> **ONE SENTENCE:** Rewrite any AI agent skill's step wording so every step is executed 100% — even by weaker LLMs that skip steps.

---

## Scope and Boundaries

Two skills cover the skill lifecycle. Use the right one — they are not interchangeable.

| Concern | Owner |
|---------|-------|
| Step wording, RFC 2119 keywords, atomic decomposition, tool naming, VERIFY gates, decision tables, subagent delegation, escape hatches, dry-run compliance, skill `name` + `description` wording (trigger surface) | **skill-prompter (this skill)** |
| Skill creation lifecycle, directory layout, file separation, references/scripts/assets organization, modular architecture, merge/split decisions, anti-patterns of structure | **skill-manager** |

**Decision rule:**
- "Steps are being skipped on weaker models" → skill-prompter
- "I need a new skill from scratch" → skill-manager (then skill-prompter to harden the steps)
- "Two skills should be merged" or "this skill is too big" → skill-manager
- "Step instructions are vague" → skill-prompter
- "Name this skill" or "write/review this skill's description" → skill-prompter (read [references/description-rules.md](references/description-rules.md))
- Both axes need work → run skill-manager first (structure), then skill-prompter (wording), then dry-run

If the request is purely structural, **delegate to skill-manager** instead of proceeding here.

---

## Name and Description Wording

The skill `name` + frontmatter `description` pair is the trigger surface — routing-prompt wording owned by this skill. When naming a skill or writing/reviewing a description (whether invoked directly or routed from skill-manager), MUST read [references/description-rules.md](references/description-rules.md) and apply its rules: name-first delta principle, length proportional to bundled sub-features, post-cutoff proper nouns spelled verbatim with category glosses and user-spoken variants, boundary clauses for sibling families.

Structural frontmatter constraints (name charset/length caps, the 1024-char description cap, the `metadata.env` manifest) remain with skill-manager.

---

## Why Skills Get Skipped

Weaker LLMs skip steps for these reasons (in order of frequency):

| Cause | Fix |
|-------|-----|
| Step is vague/ambiguous | Make it atomic with ONE concrete action |
| Step has no explicit tool call | Name the exact tool/command |
| Step depends on implicit knowledge | Provide inline context |
| Too many steps in sequence exhaust context | Delegate to subagent |
| No checkpoint forces continuation | Add VERIFY gate after each step |
| Conditional logic is complex | Use decision table, not prose |
| Step output format is unclear | Show exact output template |

---

## Procedure

MUST execute every phase below in order. Do NOT skip any phase.

### Phase 0: Setup Tracking

**Action**: Initialize the improvement tracking system.

```bash
# Initialize tracking for target skill
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py init --skill "{SKILL_NAME}" --original "{ORIGINAL_SKILL_PATH}"
```

- This creates a tracking entry in `{SKILL_PROMPTER_DIR}/data/improvements.json`
- Records: skill name, original path, start time, baseline compliance %

**VERIFY**: tracker.py prints `"initialized"` with no errors.

---

### Phase 1: Analyze Original Skill

**Action**: Resolve the installed skill name, then read the target skill's SKILL.md and ALL referenced files.

0. MUST resolve the exact installed skill name with the host's skill-listing tool before patching. Do NOT assume a filesystem/category path form like `category:skill` or `category/skill`; many installed skills are addressed by their bare tool name (for example `report-builder`, `message-retriever`, `platform-send`).
1. Read the target SKILL.md completely
2. List all files in the skill directory (`scripts/`, `references/`, `assets/`)
3. Read each referenced script and reference file
4. Detect target-skill governance rules before editing. If the skill declares an edit-discipline file, append-only changelog, fixture-coupling rule, or similar local constraints, those rules override the default instinct to patch canonical `SKILL.md` text immediately. Minor session lessons MUST go to the target skill's declared append-only sink when that governance says so.

**Analyze and record**:

```bash
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py analyze --skill "{SKILL_NAME}" \
  --total-steps {N} \
  --has-tool-calls {true|false} \
  --has-checkpoints {true|false} \
  --has-rfc2119 {true|false} \
  --has-subagent-delegation {true|false} \
  --has-decision-tables {true|false} \
  --vague-steps "{comma-separated step numbers}" \
  --notes "free text observations"
```

**VERIFY**: tracker.py prints analysis summary.

---

### Phase 2: Identify Weak Points

**Action**: For each step in the original skill, classify its compliance risk.

Classification criteria:

| Risk Level | Criteria | Action Required |
|------------|----------|-----------------|
| HIGH | Step has no explicit tool/command, OR is vague, OR has complex conditionals | MUST rewrite |
| MEDIUM | Step has tool call but no VERIFY gate, OR output format unclear | SHOULD add checkpoint |
| LOW | Step is atomic, has tool call, has checkpoint | No change needed |

```bash
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py weakpoints --skill "{SKILL_NAME}" \
  --high "{step_numbers}" \
  --medium "{step_numbers}" \
  --low "{step_numbers}"
```

**VERIFY**: All steps are classified. No step is unclassified.

---

### Phase 3: Research Improvement Patterns

**Action**: Read the improvement reference patterns.

MUST read these files (use subagent if context is tight):
- `{SKILL_PROMPTER_DIR}/references/rewrite-patterns.md` — atomic step patterns
- `{SKILL_PROMPTER_DIR}/references/compliance-checklist.md` — per-step compliance checklist

Extract applicable patterns for each HIGH and MEDIUM risk step.

**VERIFY**: You can name the specific pattern to apply to each weak step.

---

### Phase 4: Rewrite the Skill

**Action**: Create the improved SKILL.md. Apply ALL of these rules:

#### Rule 1: Atomic Steps
Each step MUST have exactly ONE action. If a step has "and" or "then", split it.

```markdown
BAD:  "Read the config file and update the database"
GOOD: Two separate steps:
  Step 3: Read config file
  Step 4: Update database using values from Step 3
```

#### Rule 2: Explicit Tool Naming
Every step that performs an action MUST name the exact tool or command.

```markdown
BAD:  "Check the website status"
GOOD: "Run: `curl -s -o /dev/null -w '%{http_code}' {URL}` to check HTTP status"
```

#### Rule 3: RFC 2119 Enforcement
Use RFC 2119 keywords to eliminate ambiguity:
- **MUST** / **SHALL** — non-negotiable requirement
- **MUST NOT** — absolute prohibition
- **SHOULD** — strong recommendation (can skip with documented reason)
- **MAY** — optional

```markdown
BAD:  "You can optionally verify the output"
GOOD: "MUST verify output matches expected format before proceeding"
```

#### Rule 4: VERIFY Gates
Every step MUST end with a VERIFY line that states the observable success condition.

```markdown
**VERIFY**: {command} prints "{expected}" OR file {path} exists with size > 0
```

#### Rule 5: Subagent Delegation
Steps that consume >2000 tokens of context SHOULD be delegated to a subagent.
Every delegation MUST include a timeout fallback so the workflow never stalls.
Verification delegations MUST be black-box: pass only the skill text, scenario, allowed tools, and required signal schema. MUST NOT pass expected answers, before/after examples, weak-point notes, diff summaries, or few-shot hints.

```markdown
**DELEGATE TO SUBAGENT**: 
  Task: "{description}"
  Input: {what to pass}
  Expected output: {what to get back}
  Max tokens: {budget}
  **IF TIMEOUT**: Subagent does not return within 60s → {inline fallback action}
```

#### Rule 6: Decision Tables Over Prose
Replace any if/else/conditional prose with a decision table.

```markdown
BAD:  "If the file exists and is not empty, read it. Otherwise, if it's a new run, create it. If it exists but is corrupted, delete and recreate."

GOOD:
| Condition | Action |
|-----------|--------|
| File exists AND size > 0 | Read file |
| File does not exist | Create new file |
| File exists AND size = 0 | Delete and recreate |
```

#### Rule 7: Progressive Context Loading
Long reference content MUST NOT be inlined. Instead:

```markdown
**LOAD REFERENCE**: Read `references/{filename}.md` for {specific section} details.
```

#### Rule 8: Step Numbering with IDs
Each step MUST have a unique ID for cross-referencing.

```markdown
### Step 3 [S3]: Validate Input Data
...
(References output from [S1])
```

#### Rule 9: Escape Hatches
Every step with external dependencies MUST have a fallback.

```markdown
**IF BLOCKED**: {tool} fails → {fallback action}. Do NOT stop the workflow.
```

#### Rule 10: No Few-Shot Answer Keys
MUST NOT include example inputs/outputs that function as answer keys for test cases. Format examples show STRUCTURE only, never actual task content.
Verification prompts MUST be stricter than documentation examples: they MUST NOT include sample successful outputs, expected artifacts, label hints, or "this should fail/pass because..." explanations.

```markdown
BAD:  Example: Input: "translate hello" → Output: "안녕하세요"
GOOD: Example format: Input: "{user_request}" → Output: "{translated_text}"
```

#### Rule 11: Step Count Budget
The improved skill MUST NOT exceed 20 total steps. Fewer well-designed steps are better than many granular ones.

| Original steps | Target steps |
|---------------|-------------|
| 1-5 | Keep same or fewer |
| 6-10 | 8-12 atomic steps |
| 11-15 | 12-18 atomic steps |
| 16+ | 15-20 atomic steps (group related actions into phases within a single step) |

```markdown
BAD:  Split "DNS + SSL check" into 6 separate steps (S3-S8)
GOOD: Keep as 1-2 steps with sub-actions listed inline:
  Step 3 [S3]: DNS and SSL Analysis
  - Run: `dig +short A {domain}` for A records
  - Run: `dig +short MX {domain}` for MX records
  - Run: `openssl s_client -connect {domain}:443 ...` for SSL check
  VERIFY: All 3 outputs saved to {domain}_dns.json
```

Why: Weaker LLMs exhaust context/output tokens on long skill files. Skills with >20 steps consistently fail to complete on MiniMax M2.7 and GLM-5-Turbo.

**Context-budget escape hatch**: Phase 4 is mechanical text surgery (add step IDs, swap 평서문→RFC 2119, append VERIFY gates) that does NOT need the parent's full conversation context. If the parent session is context-heavy (long build/iteration session), SHOULD delegate Phase 4 to a subagent: pass it the target SKILL.md path, the exact list of headers to rename, the RFC-2119 swaps, and the literal VERIFY-gate text per step. Subagent toolsets `["file","terminal"]`. The subagent self-reports, so the parent MUST re-verify by `grep -c "VERIFY \[S" SKILL.md` + header-ID grep + `quick_validate.py` before trusting "done" — do NOT take the subagent summary as proof (verified 2026-06-03: subagent reported 7 VERIFY gates, parent confirmed via grep).

**Output**: Write the improved SKILL.md to the skill's directory.

**VERIFY**: The improved SKILL.md has:
- [ ] Total step count ≤ 20
- [ ] Every step has a unique ID
- [ ] Every step has exactly ONE action (sub-actions within a step are OK if they share one VERIFY)
- [ ] Every step names the exact tool/command
- [ ] Every step ends with VERIFY
- [ ] All conditionals use decision tables
- [ ] RFC 2119 keywords are used for all requirements
- [ ] Subagent delegation for heavy steps (with timeout fallback)
- [ ] No few-shot answer keys

---

### Phase 5: Update Supporting Files

**Action**: Update or create any scripts, references, or assets needed by the improved skill.

1. If the improved skill references new scripts → create them
2. If the improved skill references new reference docs → create them
3. If existing scripts need changes to match new step structure → update them

**VERIFY**: All files referenced in the improved SKILL.md exist and are valid.

If the improved skill needs a different directory layout (e.g., split SKILL.md into multiple files, extract a sub-skill, merge with another skill), STOP this phase and delegate to **skill-manager** for the structural change. Resume Phase 5 only after structure is finalized.

---

### Phase 6: Record Improvement

```bash
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py record --skill "{SKILL_NAME}" \
  --phase "rewrite" \
  --changes "{summary of changes made}" \
  --files-modified "{comma-separated file paths}"
```

**VERIFY**: tracker.py confirms the record was saved.

---

### Phase 7: Self-Audit (Static)

**Action**: Re-read the improved SKILL.md as if you are a weaker LLM (MiniMax M2.7, GLM-5 or Deepseek V4 Flash through `opencode-go` provider with OpenCode CLI). This phase is a STATIC text review — Phase 8 will dynamically execute the skill.

For EACH step, ask:
1. Can I execute this with ZERO prior context? (Must be YES)
2. Is there exactly ONE thing to do? (Must be YES)
3. Do I know the exact tool/command? (Must be YES)
4. Do I know when I'm done? (VERIFY gate exists? Must be YES)
5. If this step fails, do I know what to do? (Escape hatch? Must be YES for external deps)

Any "NO" answer → go back to Phase 4 and fix that step.

```bash
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py audit --skill "{SKILL_NAME}" \
  --passed-steps "{step_ids}" \
  --failed-steps "{step_ids}" \
  --notes "audit findings"
```

**VERIFY**: All steps pass the 5-question audit. failed-steps is empty.

---

### Phase 8: Dry Run Execution (Dynamic)

**Action**: Execute the improved SKILL.md against a representative scenario in a fresh-context simulation. This is the final dynamic check before report — Phase 7 was a static text review; Phase 8 confirms the rewritten steps actually fire when an LLM reads them cold.

#### 8.1 Construct the scenario

Pick exactly ONE representative user request that exercises the skill end-to-end. The scenario MUST exercise at least one HIGH-risk step from Phase 2 (the steps most likely to be skipped before the rewrite).

#### 8.2 Simulate fresh-context execution

| Method | When to use |
|--------|-------------|
| **Black-box subagent delegation (preferred)** | Default. Spawn validators loaded with ONLY the improved SKILL.md, the representative scenario, allowed tools, and the signal schema. The prompt MUST NOT include expected answers, examples, diffs, known weak points, or implementation notes. |
| **Manual walkthrough** | Use only if subagent delegation is unavailable. Pretend the original conversation does not exist; for each step, name the exact tool call you would invoke and the input you would pass. Do NOT use hidden expected answers. |

Run the same black-box scenario across BOTH validation lanes:

**Provider scope (HARD): validators run on `opencode-go/*` ONLY.** All metered (종량제) providers — `opencode/*`, `anthropic/*`, `openai/*`, `github-copilot/*`, `google/*` — are FORBIDDEN for dry-run testing as standing policy, regardless of remaining budget. A family absent from `opencode-go` is simply unavailable; do NOT reach outside it.

**Model-tier scope (HARD): Fable/Mythos-class models are FORBIDDEN for dry-run.** Dry-run is multi-validator fan-out, so the validator model's per-token price multiplies across every run — Fable pricing buys zero extra compliance-checking accuracy there. The ban covers EVERY route: explicit `--model` flags, harness subagent delegation, and model inheritance (a Fable-class parent session MUST pass an explicit non-Fable model on every validator or orchestrator spawn it makes).

| Model tier | Dry-run usage |
|------------|---------------|
| Fable / Mythos (`claude-fable-*`, `claude-mythos-*`) | FORBIDDEN — never a validator, never the dry-run orchestrator, never inherited into either |
| Sonnet (latest) | DEFAULT tier for any Claude-side dry-run work (orchestration, or user-approved provider-scope widening) |
| Opus (latest) | Allowed ONLY when the user explicitly requests it for this dry-run |

| Lane (ALL on `opencode-go/*`) | Required |
|------|---------------------|
| Cost-efficient | ≥3 distinct small/fast families: Kimi, Deepseek-flash, GLM, MiniMax, Qwen-plus, Mimo |
| Higher-capability | ≥1 of `qwen3.7`, `minimax-m3`, `deepseek-v4-pro` |

Each validator is one `opencode run`. Write the black-box prompt (improved SKILL.md + scenario + signal schema, NO answer keys) to a temp file once, then:

```bash
PROMPT="$(cat /tmp/dryrun-prompt.txt)"
timeout 300 opencode run "$PROMPT" --model opencode-go/{model} >"/tmp/dryrun-{tag}.out" 2>&1
```

Two operational rules (verified 2026-06-13 failure modes):
- **Run SERIALLY** — parallel `opencode run` crashes with `database is locked` (shared SQLite). On a lock, retry that one model after the prior exits.
- **Empty-at-timeout ≠ fail** — reasoning-heavy models (minimax, qwen-max) may exceed `timeout 300`. Re-run that model with a longer timeout OR substitute another `opencode-go` family; do NOT record a signal `fail`.

**IF BLOCKED**: subagent system unavailable AND manual walkthrough impractical → Document the blocker in the dryrun record and mark the skill as "audit-only complete" rather than "dryrun verified". Do NOT claim the skill is dryrun-verified without an actual dryrun.
**IF A MODEL FAMILY IS UNAVAILABLE**: run every available validator, record the missing family in the dryrun record, and mark the dryrun incomplete unless the user explicitly accepts the gap.

#### 8.3 Record the result for every step

For each step in the simulation, record four step-level signals. For the whole dry-run, also record one model-lane signal.

| Signal | Meaning |
|--------|---------|
| `fired` | The simulated LLM invoked the step at all (yes/no) |
| `tool_call_exact` | The simulated LLM used the exact named tool/command (yes/no) |
| `verify_signal` | The VERIFY line produced an observable signal (yes/no) |
| `escape_used` | If a fallback was triggered, the reroute happened correctly (n/a, yes, or no) |

#### 8.4 Pass condition

ALL of the following MUST be true:

- Every step `fired = yes` (no silent skip)
- Every `verify_signal = yes` (every VERIFY produced a signal)
- No step has `tool_call_exact = no` for the named tool
- No `escape_used = no` for triggered fallbacks
- Every required validation lane completed without leaking answer keys or few-shot hints
- The scenario reached the documented final output

#### 8.5 Persist the dry-run record

MUST record the five signals as structured flags so the finalize gate can verify them automatically. The signal flags MUST be:

| Flag | Value when PASS |
|------|-----------------|
| `--signal-fired` | `pass` if every step fired (no silent skip), else `fail` |
| `--signal-tool-call-exact` | `pass` if every step used the named tool, else `fail` |
| `--signal-verify` | `pass` if every VERIFY gate produced a signal, else `fail` |
| `--signal-escape` | `pass` if a fallback rerouted correctly, `fail` if a triggered fallback failed, `na` if no fallback was triggered |
| `--signal-model-lanes` | `pass` if BOTH lanes ran black-box on `opencode-go/*` — cost-efficient (≥3 distinct small/fast families) AND higher-capability (≥1 of qwen3.7-max / minimax-m3 / deepseek-v4-pro) — else `fail` |

```bash
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py record --skill "{SKILL_NAME}" \
  --phase "dryrun" \
  --scenario "{one-line scenario description}" \
  --signal-fired pass \
  --signal-tool-call-exact pass \
  --signal-verify pass \
  --signal-escape na \
  --signal-model-lanes pass \
  --changes "fired={S1,S2,...} | skipped={ids} | verify-failed={ids} | escape-failed={ids}" \
  --files-modified ""
```

**VERIFY**: All pass conditions in 8.4 hold AND tracker.py confirms the dryrun record was saved with the structured `signals` block.

**IF FAILED**: Identify the specific failing steps. Record the dryrun with the matching `--signal-* fail` flag so the gate can reject finalize. Return to Phase 4 and rewrite ONLY those steps. Re-run Phase 7 → Phase 8 in tight loop until clean. Do NOT proceed to Phase 9 with any failing dryrun signal.

**Gate enforcement**: `tracker.py finalize --status completed` now REJECTS the call if:
1. No dryrun (or `prompt-dryrun`) phase record exists, OR
2. The latest dryrun record has any structured signal equal to `fail`.

The only legitimate override is `--force`, which writes `force_finalized: true` into the entry and REQUIRES the override reason to appear in `--summary`.

---

### Phase 9: Ask User for Confirmation (if needed)

**Decision Table**:

| Situation | Action |
|-----------|--------|
| Original skill was vague and user's request was to "improve" | Show diff summary + dry-run result, ask user to confirm |
| Original skill was detailed but poorly structured | Proceed without asking (structural fix only) |
| User explicitly said "create a new skill" | Ask user clarifying questions about intent |
| Changes alter the skill's purpose or scope | MUST ask user before proceeding |
| Dry-run revealed a regression that required design changes | MUST ask user before proceeding |

If asking is needed, present:
1. Summary of changes (bullet list, max 10 items)
2. Before/after comparison of the most-changed step
3. Dry-run pass/fail summary from Phase 8
4. Specific question about any ambiguous intent

**VERIFY**: User confirmed OR no confirmation needed per decision table.

---

### Phase 10: Finalize and Report

```bash
python3 {SKILL_PROMPTER_DIR}/scripts/tracker.py finalize --skill "{SKILL_NAME}" \
  --status "completed" \
  --summary "brief summary of all improvements"
```

**Output to user**:

```markdown
## Skill Improvement Complete

**Skill**: {SKILL_NAME}
**Changes**:
- {change 1}
- {change 2}
- ...

**Compliance Improvements**:
| Metric | Before | After |
|--------|--------|-------|
| Atomic steps | {N}/{total} | {N}/{total} |
| Explicit tool calls | {N}/{total} | {N}/{total} |
| VERIFY gates | {N}/{total} | {N}/{total} |
| RFC 2119 keywords | {present/absent} | {present} |
| Subagent delegation | {N} steps | {N} steps |
| Decision tables | {N} | {N} |

**Dry-Run Result**:
- Scenario: {one-line scenario}
- Steps fired: {N}/{total}
- VERIFY signals: {N}/{total}
- Escape hatches triggered: {N}
- Status: PASS | FAIL

**Files Modified**: {list}
```

**VERIFY**: Report printed. tracker.py shows status "completed".

---

## Constraints

- **MUST NOT** use few-shot examples that leak test answers
- **MUST NOT** change the skill's core purpose without user confirmation
- **MUST NOT** claim a skill is "dryrun verified" without actually executing Phase 8
- **MUST NOT** run any part of a dry-run on a Fable/Mythos-class model (`claude-fable-*`, `claude-mythos-*`) — Claude-side dry-run work defaults to Sonnet; Opus only on explicit user request (Phase 8.2 model-tier scope)
- **MUST NOT** bypass the finalize gate with `--force` unless subagent execution is genuinely unavailable AND the reason is documented in `--summary`
- **MUST** preserve all existing functionality while improving wording
- **MUST** use `scripts/tracker.py` for ALL state tracking (no manual JSON editing)
- **MUST** delegate structural changes (directory layout, merge, split, modular reorg) to **skill-manager**
- **SHOULD** delegate context-heavy analysis to subagents
- **MAY** split large SKILL.md into SKILL.md + reference files if total exceeds 5000 words (this is a structural change — coordinate with skill-manager)

## Variable Definitions

| Variable | Meaning |
|----------|---------|
| `{SKILL_PROMPTER_DIR}` | Path to this skill-prompter skill directory |
| `{SKILL_NAME}` | Name of the skill being improved |
| `{ORIGINAL_SKILL_PATH}` | Filesystem path to the original skill directory |

## Error Handling

| Error | Recovery |
|-------|----------|
| Target skill has no SKILL.md | Ask user for the correct path |
| tracker.py fails | Check Python environment, run `uv pip install -r requirements.txt` |
| Improved skill exceeds 5000 words | Delegate split to **skill-manager** |
| User rejects changes | Ask what specifically to change, go back to Phase 4 |
| Dry-run fails after 3 rewrite cycles | Stop the loop. Surface the failing steps and ask the user whether the underlying design is correct (may require structural changes — delegate to skill-manager). |
