# Evaluation-Driven Skill Development

This file expands on Step 5 (Iterate) of SKILL.md. Read this when creating a new skill from scratch with high reliability requirements, or when an existing skill underperforms in real use.

## The Principle: Build Evaluations First

Build evaluations BEFORE writing extensive documentation. Evaluations turn skill design into a measurable, iterative process instead of a guessing game.

## Workflow

### 1. Identify gaps without the skill

Run Claude on representative tasks WITHOUT the skill. Document where Claude:

- Asks clarifying questions that the skill should answer
- Picks the wrong tool, library, or approach
- Produces output in an inconsistent format
- Misses domain-specific edge cases
- Repeats the same mistake the user keeps correcting

These failure modes are the gaps the skill must close.

### 2. Create evaluations

Build at least 3 concrete evaluation scenarios that exercise the gaps you found.

**Each scenario should specify:**
- The exact user prompt
- The expected behavior (tool choice, output format, edge case handling)
- A pass/fail criterion that does not require human judgment for routine cases

**Example evaluations for a `pdf-forms` skill:**

```
Scenario 1: Fill a simple text form
- Prompt: "Fill out this form with name=Alice, email=alice@example.com"
- Pass: Output PDF has both fields populated; no manual XML editing in process.

Scenario 2: Fill a form with checkboxes
- Prompt: "Mark the 'Yes' checkbox in section A"
- Pass: Checkbox state changed; other checkboxes unchanged.

Scenario 3: Detect non-fillable PDF
- Prompt: "Fill this scanned form with the same data"
- Pass: Skill detects scanned PDF and recommends OCR + pdf2image flow instead of attempting to fill.
```

### 3. Establish baseline

Run all evaluations WITHOUT the skill. Record the failure rate and failure modes. This is the floor against which the skill is measured.

### 4. Write minimal instructions

Write the smallest SKILL.md that plausibly passes the evaluations. Resist the urge to document everything Claude might want to know — start lean and add only what evaluations prove necessary.

### 5. Iterate

For each scenario that fails:

1. Read Claude's actual response and tool calls
2. Identify what the skill failed to provide (missing instruction, ambiguous wording, wrong default)
3. Make the smallest change that addresses the gap
4. Re-run all evaluations (not just the failing one — additions can break previously passing scenarios)

Stop iterating when all evaluations pass and additional changes do not improve the failure rate.

## Iteration with Two Claude Instances

A useful technique for skill creation: use two Claude instances.

**Setup:**
- **Claude A** has the user's normal context (conversation history, files, repo).
- **Claude B** is a fresh instance with only the new skill loaded.

**Loop:**
1. Complete a task with Claude A using normal prompting.
2. Notice the context the user repeatedly provides (conventions, file paths, preferred libraries).
3. Ask Claude A to capture those patterns into a draft skill.
4. Test the draft with Claude B on a similar task.
5. Return to Claude A with observations from Claude B's run.
6. Refine and repeat.

This mimics the real conditions under which the skill will be used (no prior conversation context).

## Observing Claude's Skill Usage

When testing a skill, watch for these signals:

| Observation | What it Means | Fix |
|-------------|---------------|-----|
| Claude explores unexpected files | Internal structure is not intuitive | Add a navigation table or file map at the top of SKILL.md |
| Claude misses important connections | Cross-references are too implicit | Make links between sections explicit |
| Claude repeatedly asks about one section | Content is buried; should be in SKILL.md, not references | Promote the section into SKILL.md body |
| Claude ignores certain content | The content is unnecessary or unclear | Delete it or rewrite for clarity |
| Claude routes to the wrong sub-skill | Description does not differentiate | Sharpen trigger keywords in description |

## When Evaluations Are Optional

Evaluation-driven development has overhead. It is not always worth it.

**Skip formal evaluations when:**
- The skill has 1-2 simple workflows with obvious correctness criteria
- The skill is for personal use and you can manually verify each task
- The cost of failure is low (e.g., a documentation-only skill)

**Always build evaluations when:**
- The skill performs irreversible actions (database writes, file deletions, external API calls)
- The skill is shipped to a team or used in production workflows
- Failure modes are subtle (e.g., wrong output format that looks plausible)
- The skill has 5+ sub-components or branches and regressions are likely
