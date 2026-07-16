# Per-Step Compliance Checklist

Use this checklist to audit EVERY step in an improved skill. Each step MUST pass ALL applicable checks.

## Mandatory Checks (ALL steps)

| # | Check | Pass Criteria |
|---|-------|---------------|
| M1 | Unique Step ID | Step has format `### Step N [SN]:` |
| M2 | Single Action | Step describes exactly ONE thing to do |
| M3 | Explicit Tool/Command | Step names the exact tool, CLI command, or API call |
| M4 | VERIFY Gate | Step ends with `**VERIFY**: {observable condition}` |
| M5 | No Ambiguous Pronouns | No "it", "this", "that" without clear antecedent |
| M6 | No Implicit Knowledge | A reader with ZERO prior context can execute the step |

## Conditional Checks

| # | Check | When Required | Pass Criteria |
|---|-------|---------------|---------------|
| C1 | Decision Table | Step has ANY conditional logic | if/else replaced with table |
| C2 | Escape Hatch | Step calls external service/tool | `**IF BLOCKED**: {fallback}` present |
| C3 | Subagent Delegation | Step would consume >2000 tokens | `**DELEGATE TO SUBAGENT**` block present |
| C4 | Cross-Reference | Step uses output from prior step | `(from [SN])` reference present |
| C5 | Loop Constraint | Step iterates over a collection | Explicit count limit or "FIRST only" |
| C6 | RFC 2119 Keyword | Step states a requirement | MUST/SHALL/SHOULD/MAY used |

## Anti-Pattern Checks (MUST NOT have)

| # | Anti-Pattern | Detection |
|---|-------------|-----------|
| A1 | Multi-action step | Contains "and then", "after that", "also" joining TWO actions |
| A2 | Vague tool reference | "check", "verify", "look at" without naming a tool |
| A3 | Implicit loop | "for each", "all of", "every" without explicit iteration strategy |
| A4 | Missing output format | Step produces output but doesn't specify the format |
| A5 | Few-shot answer key | Example contains actual content that would satisfy a test case |
| A6 | Unbounded retry | "retry until success" without a max attempt count |
| A7 | Context dependency | "as mentioned above" or "from earlier" without step ID reference |

## Scoring

For each step, count:
- **Pass**: Check is satisfied
- **Fail**: Check is not satisfied
- **N/A**: Check is not applicable to this step

**Compliance Score** = Passed / (Passed + Failed) * 100

Target: **100%** for all steps.

## Quick Audit Command

To audit a step quickly, answer these 5 questions:

1. **Can I execute this with ZERO prior context?** → Tests M5, M6
2. **Is there exactly ONE thing to do?** → Tests M2, A1
3. **Do I know the EXACT tool/command?** → Tests M3, A2
4. **Do I know when I'm done?** → Tests M4
5. **If this fails, do I know what to do?** → Tests C2

All YES = step passes. Any NO = step needs rewrite.
