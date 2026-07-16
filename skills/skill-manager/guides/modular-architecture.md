# Modular Architecture: Multiple Skills vs. Single Skill

This file expands on the architectural decision summarized in SKILL.md. Read this when planning a new capability that could be split across multiple skills, or when an existing skill is becoming too large.

## The Core Decision

| Approach | Structure | Best For |
|----------|-----------|----------|
| **Multiple separate skills** | Independent SKILL.md files, each a standalone capability | Capabilities used in isolation; teams need granular enable/disable control |
| **Single skill with reference files** | One SKILL.md plus subdirectories | Tightly coupled workflows that share schemas, patterns, or coordinate as a unit |

## Option A: Multiple Separate Skills

Use when capabilities are independent and reusable across different contexts.

```
skills/
├── pdf-extract/
│   └── SKILL.md
├── pdf-forms/
│   └── SKILL.md
├── pdf-merge/
│   └── SKILL.md
└── excel-analysis/
    └── SKILL.md
```

### Pros

- **Independent triggering** — each skill activates on its own description; only relevant skills load
- **Smaller per-trigger context** — only the matched skill's SKILL.md loads (~5k tokens), not unrelated capabilities
- **Easier maintenance** — clear ownership boundaries; updating one skill cannot break others
- **Composability** — Claude can chain multiple skills naturally based on semantic understanding
- **Selective provisioning** — admins can enable/disable individual skills per team
- **Parallel development** — different teams own different skills without coordination overhead

### Cons

- **No shared context** — each skill is isolated; common schemas must be duplicated or extracted to a separate skill
- **Discovery overhead** — more skills means more metadata in every system prompt (~100 tokens per skill)
- **Coordination complexity** — explicit chaining requires careful description writing or user awareness

### Implicit Chaining via Semantic Matching

Claude automatically chains skills when the user request matches multiple descriptions:

```
User: "Extract the tables from this PDF and create an Excel report with charts"

→ pdf-extract activates (matches "extract tables from PDF")
→ excel-analysis activates (matches "Excel report with charts")
→ Both SKILL.md files load
→ Claude executes a combined workflow
```

This is **LLM-mediated chaining** — there are no programmatic triggers, only semantic matching against descriptions.

## Option B: Single Skill with Multiple Files

Use when capabilities are tightly related and share context.

```
clickhouse-expert/
├── SKILL.md                    # Main orchestrator with routing table
├── BACKEND-CLI.md              # CLI execution backend
├── BACKEND-MCP.md              # MCP execution backend
├── agents/
│   ├── overview/
│   │   ├── prompt.md
│   │   └── queries.sql
│   ├── memory/
│   │   ├── prompt.md
│   │   └── queries.sql
│   └── ... (more agents)
├── guides/
│   └── audit-patterns.md
└── scripts/
    └── run-agent.sh
```

### Pros

- **Shared context** — all sub-components reference the same schemas, patterns, conventions
- **Unified orchestration** — SKILL.md acts as a coordinator with routing tables and workflow logic
- **Single trigger point** — one description triggers the whole system; internal routing is explicit
- **Atomic deployment** — entire capability ships as one unit; version control is simpler
- **Deep specialization** — supports sophisticated multi-component workflows under one skill

### Cons

- **SKILL.md always loads on trigger** (~5k tokens), even for narrow sub-tasks — though sub-files (agents/, guides/, api-references/) still load selectively
- **Higher maintenance burden** — changes to SKILL.md affect the entire system
- **Less reusable** — sub-components cannot be triggered independently outside this skill
- **Steeper learning curve** — new contributors must learn the internal structure

### Explicit Internal Routing

Internal chaining is controlled through the SKILL.md orchestrator, not through semantic matching:

```markdown
## Coordinator Loop (from SKILL.md)

1. Run wave 1: `overview` agent (triage)
2. Run wave 2: pick 2-3 targeted agents from the symptom table below
3. Optional wave 3: deep dives if needed
4. Produce a consolidated report

## Symptom-to-Agent Mapping

| User Symptom        | Agents to Run            |
|---------------------|--------------------------|
| "OOM" / "memory"    | memory, reporting        |
| "slow queries"      | reporting, memory        |
| "too many parts"    | merges, ingestion        |

To run an agent:
1. Read `agents/<name>/queries.sql`
2. Execute the queries
3. Read `agents/<name>/prompt.md`
4. Analyze results using the prompt
```

## Decision Framework

| Scenario | Recommended Approach | Reason |
|----------|---------------------|--------|
| Independent tools (PDF, Excel, PPTX) | Multiple skills | Each is useful alone; users may need only one |
| Domain-specific diagnostic system | Single skill | Sub-components share schemas, need coordination |
| Team-specific workflows | Multiple skills | Different teams enable different skills |
| Complex multi-step analysis | Single skill | Explicit orchestration and shared context required |
| General-purpose utilities | Multiple skills | Maximum reusability and composability |
| Compliance / audit workflows | Single skill | Strict sequencing and unified reporting |

### Quick rule

If a user might invoke capability A without ever needing capability B, make them separate skills. If A and B always work together as parts of the same workflow, make them a single skill with subdirectories.

## Hybrid Approach

A workspace can combine both patterns:

```
skills/
├── data-platform/                    # Comprehensive diagnostic skill
│   ├── SKILL.md
│   ├── agents/
│   │   ├── clickhouse/
│   │   ├── postgres/
│   │   └── redis/
│   └── guides/
├── pdf-processing/                   # Standalone utility skill
│   └── SKILL.md
└── excel-reporting/                  # Standalone utility skill
    └── SKILL.md
```

The `data-platform` skill handles complex, related diagnostics internally. PDF and Excel skills remain independent utilities that can be composed with it.

## Cross-Skill Coordination Patterns

### Pattern 1: Implicit chaining (recommended default)

Claude's semantic understanding chains skills based on context. No explicit configuration needed.

```
User: "Analyze this database, create a report, and make a presentation"

→ data-analysis triggers on "database"
→ Skill produces analysis data
→ excel-reporting triggers on "report"
→ Skill produces Excel file
→ pptx triggers on "presentation"
→ Skill creates slides from the analysis
```

### Pattern 2: Explicit invocation in user prompt

The user names the chain directly:

```
User: "Use the data-analysis skill first, then pass results to excel-reporting"
```

### Pattern 3: Coordinator skill with named invocations

A skill can instruct Claude to invoke another skill by name. This is verified to work on Claude.ai.

```yaml
---
name: data-extractor
description: Extracts and structures data from text. Use when the user asks to extract data, parse information, or analyze text content.
---

# Data Extractor

## Instructions

1. Analyze the input text
2. Extract data into a DATA_BLOCK format
3. **After extraction, invoke the `data-formatter` skill to format results**

## After Extraction

After producing the DATA_BLOCK output, invoke the `data-formatter` skill to format the results into a final report.
```

Effective phrasing for cross-skill invocation:
- "invoke the `skill-name` skill"
- "use the `skill-name` skill to ..."
- "chain to `skill-name` for ..."

### Pattern 4: MCP + Skills combination

MCP provides data access; skills provide workflow expertise. The two compose naturally:

```
MCP Server: provides database queries, file access
Skill: provides analysis methodology, formatting rules

User: "Analyze our Q3 sales"
→ MCP fetches data from the database
→ data-analysis skill interprets results
→ excel-reporting skill formats output
```

## Best Practices for Modular Architecture

1. **Start narrow, expand later.** Build single-purpose skills first. Combine them into a single comprehensive skill only after a coordination pattern repeats.

2. **Use the 3-conversation rule.** If the same skills are chained 3+ times, consider creating a coordinator skill that explicitly orchestrates them.

3. **Keep shared context in typed folders.** For single-skill architectures, put common schemas in `api-references/` and shared patterns in `guides/` so sub-components can read them on demand. Do not dump them into a bare `references/` folder (that is the untriaged inbox).

4. **Write descriptions for composition.** Include phrases like "Use with `excel-reporting` for formatted output" in descriptions when skills are commonly chained.

5. **Test both isolated and combined.** Verify each skill works alone AND when composed with others.

6. **Document internal routing explicitly.** For single-skill architectures with sub-components, include a clear routing table in SKILL.md.

7. **Consider admin needs.** Multiple skills give granular enable/disable control; a single skill gives simpler provisioning.

## Refactoring Procedures

These procedures are referenced from `SKILL.md`'s "Refactoring: Merging and Splitting Skills" section. Use them after the trigger conditions for merging or splitting are met.

### Merging multiple skills into one

**Trigger conditions:**

- The same skills are invoked together in 3+ real-use chains
- They share schemas, conventions, or domain context that would otherwise be duplicated across skills
- Internal coordination via a routing table would reduce overall surface area more than independent triggering helps

**Process:**

1. Read every SKILL.md being merged and separate shared vs. unique content
2. **Neighbour-references audit (do not skip).** Grep ALL existing skills (every skills directory on the host) for any support file (under `guides/`, `api-references/`, or a legacy `references/` inbox) that mentions the topic, model, tool, or codename of the skills being merged — even if the file lives under an unrelated skill. Pre-existing support files often contain field-verified recipes, working flags, gotcha lists, or first-run logs that took real time/money to produce. They MUST be linked from (or absorbed into) the merged skill's typed folders; otherwise the merged skill silently loses validated history. A new skill that ignores existing neighbour references is a regression. Symptom of skipping this step: rewriting an inference recipe from scratch and discovering a working, field-verified one under a sibling skill AFTER spending GPU-pod time debugging.
3. Choose the combined `name` and rewrite `description` to capture all trigger keywords from the originals
4. Move shared content into typed folders (schemas → `api-references/`, conventions/patterns → `guides/`); keep each original skill's procedures as a named subdirectory
5. Rebuild SKILL.md as an orchestrator with a routing table mapping symptoms or sub-tasks to the relevant subdirectory
6. Verify every original use case still works under the merged skill (run one dry-run scenario per original skill)
7. Delete the obsolete skill directories only after verification

**Shared-content audit:** Before deleting any source skill, grep externally for references to the old skill names. Update every external pointer (other skills, configs, docs) before removal.

### Splitting one skill into multiple skills

**Trigger conditions:**

- SKILL.md exceeds 500 lines and references group by independent domains
- Sub-capabilities are invoked independently in real usage (users hit only one branch at a time)
- Sub-capabilities have unrelated trigger keywords that compete for the same description

**Process:**

1. Identify the cleanest seam between sub-capabilities (usually a domain boundary or distinct trigger set)
2. For each sub-capability, draft a focused `description` with its own trigger keywords — verify trigger keywords do NOT overlap across the new skills
3. Move the corresponding references and scripts into the new skill directories
4. Audit shared content — duplicate only if it is genuinely small (under ~50 lines); otherwise extract it into a third common skill that the others link to
5. Test each new skill in isolation against representative requests (no skill should leak into another skill's scenarios)
6. Update any external references (other skills, configs, docs) that named the old skill

**Trade-off note:** Splitting always increases the total metadata footprint in the system prompt (~100 tokens per new skill). If the split produces fewer than ~3 distinct skills with clearly non-overlapping triggers, prefer keeping a single skill with sub-references instead.

### After every merge or split

Run BOTH the **Final Skill Quality Checklist** AND the **Dry Run Verification** procedure (defined in `SKILL.md`) for every resulting skill — for merge, that means one dry-run per ORIGINAL use case against the merged skill; for split, one dry-run per NEW skill in isolation.
