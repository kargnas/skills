# skill-prompter

Rewrite any AI agent skill's step wording so every step is executed 100% — even by weaker LLMs that skip steps.

> **Renamed from `skill-improver`.** This skill owns prompting compliance. Structural changes (directory layout, merge, split, modular reorganization) belong to `skill-manager`.

> **Note**: The "Evolution" section below references `skill-improver` historically — that was the original name. The current procedure (10 phases including a final dry-run) is documented in [SKILL.md](SKILL.md).

## Quick Start

```
You: "Improve the skill at skills/my-skill/SKILL.md"
```

That's it. The bot reads, analyzes, rewrites, self-audits, and tracks everything.

---

## 27% → 100%: The Real Test

A **196-line `competitor-website-audit` skill** with 15 steps. DNS lookups, Playwright screenshots, pricing extraction, report generation.

```
📄 Before: 1 file, 196 lines, 15 steps
   VERIFY gates:    0
   Escape hatches:  0
   Subagent tasks:  0
   Decision tables: 0
   Step IDs:        none
```

| Model | Before | After |
|-------|--------|-------|
| MiniMax M2.7 | ❌ 27% (4/15) | ✅ **100%** (11/11) |
| GLM-5-Turbo | ❌ 33% (5/15) | ✅ **100%** (16/16) |
| Haiku 4.5 | ❌ 40% (6/15) | ✅ **100%** (16/16) |
| Opus 4.6 | ⚠️ 67% (~10/15) | — (not retested) |

```
📄 After: 1 file, 437 lines, 16 steps
   VERIFY gates:    17  (was 0)
   Escape hatches:  17  (was 0)
   Subagent tasks:   4  (was 0)
   Decision tables: 64 rows (was 0)
   Step IDs:        [S1]-[S16]
```

---

## Bot Dialogue

```
🤖 Bot: Reading skill... 15 steps found.
   Analyzing each step for compliance risk.

📊 Analysis:
   14/15 steps → HIGH risk
    1/15 steps → MEDIUM risk
    0/15 steps → LOW risk

🤖 Bot: Rewriting...
   (adds step IDs, exact CLI commands, VERIFY gates,
    IF BLOCKED fallbacks, decision tables, subagent delegation)

✅ Bot: Self-audit passed. Writing improved SKILL.md.
```

9 skills improved and tracked in `improvements.json` so far.

---

## Evolution: 2 Iterations to 100%

### 📚 Phase 1: Research

5 MiniMax M2.7 prompting research documents (~90KB) from Chinese developer communities. 3 sample skills (5KB–29KB). Key findings:

- `MUST`/`SHALL` keywords doubled compliance vs plain language
- Atomic step decomposition was the single biggest factor
- Few-shot examples were dangerous — models memorized answers instead of learning patterns (became Rule 10)

### 🔨 Phase 2: Build

```
📄 SKILL.md               — 277 lines, 10 rules, 10 phases
📄 tracker.py             — persistent JSON tracking CLI
📄 rewrite-patterns.md    — 6 rewrite patterns with examples
📄 compliance-checklist.md — mandatory/conditional/anti-pattern checks
📄 test skill (15 steps)  — deliberately complex audit skill
```

### 🟡 Phase 3: First Test — Models Over-Decompose

All 3 weak models followed skill-improver perfectly (10/10 phases). But they over-decomposed the target:

```
🤖 MiniMax (~3 min): → 15 steps → 15/15 ✅
🤖 GLM (~5 min):     → 28 steps → 27/28 ⚠️  (stuck at S28)
🤖 Haiku (~4 min):   → 40 steps → ~15/40 ❌  (timed out)
```

### 🔧 Phase 4: Data-Driven Fix

```diff
+ Rule 11: Step Count Budget
+ "MUST NOT exceed 20 total steps."
+ Why: 40 steps → models exhaust context before finishing.

  Rule 5: Subagent Delegation
+ Every delegation MUST include a timeout fallback.
+ "IF TIMEOUT: 60s → {inline fallback}"
```

### 🟢 Phase 5: Round 2 — All 100%

```
🤖 MiniMax → 11 steps (was 15, -27%)
🤖 GLM     → 16 steps (was 28, -43%)
🤖 Haiku   → 16 steps (was 40, -60%)
```

| Model | Steps | Time | Result |
|-------|-------|------|--------|
| MiniMax M2.7 | 11/11 | ~5 min | ✅ **100%** |
| GLM-5-Turbo | 16/16 | ~6 min | ✅ **100%** |
| Haiku 4.5 | 16/16 | ~4 min | ✅ **100%** |

GLM's subagent fallback in action:
```
| S11 | Core Web Vitals | ✅ PASS | API unavailable, fallback applied |
```

**3/3 models, 100%, in 2 iterations.**

---

## Before / After

**Before** (human-written):
```markdown
### Step 3: DNS and SSL Analysis
For each competitor domain, run DNS lookups and SSL certificate checks.
Use dig to get A records, MX records, and NS records. Use openssl to check
SSL certificate expiry. Also check if the site uses CDN.
```

**After** (bot-improved):
```markdown
### Step 3 [S3]: Perform DNS Lookup

**Action**: MUST run for each domain in state.json:
  dig +short A {domain} > audit_output/data/{domain}_dns_a.txt
  dig +short MX {domain} > audit_output/data/{domain}_dns_mx.txt

**VERIFY**: `cat audit_output/data/{domain}_dns.json` shows valid JSON.
**IF BLOCKED**: `dig` unavailable → Use `nslookup {domain}` instead.
```

---

## The 11 Rules

| # | Rule | Prevents |
|---|------|---------|
| 1 | Atomic Steps | "Do A and B" in one step |
| 2 | Explicit Tool Naming | "Check the website" without saying how |
| 3 | RFC 2119 Keywords | "You can optionally..." ambiguity |
| 4 | VERIFY Gates | No way to know if step succeeded |
| 5 | Subagent Delegation | Context-heavy steps (+ timeout fallback) |
| 6 | Decision Tables | if/else prose |
| 7 | Progressive Context Loading | Inlining huge reference docs |
| 8 | Step IDs | Can't cross-reference between steps |
| 9 | Escape Hatches | Tool fails = workflow stops |
| 10 | No Answer Keys | Examples that leak test answers |
| 11 | Step Count Budget | Too many steps exhausts weak LLM context |

Rules 1–10 designed upfront. **Rule 11 discovered through testing** — the fix that took compliance from 96% to 100%.

---

## File Structure

```
skill-prompter/
├── SKILL.md                     — 10 phases (incl. dry-run), 11 rules
├── scripts/
│   └── tracker.py               — Python CLI for improvement tracking
├── references/
│   ├── compliance-checklist.md  — per-step audit checklist (6 mandatory + 6 conditional checks)
│   └── rewrite-patterns.md      — 6 atomic rewrite patterns
├── data/
│   └── improvements.json        — persistent tracking
└── tests/
    └── test-complex-15step-skill-IMPROVED.md — example improved skill
```
