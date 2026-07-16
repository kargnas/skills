# Name and Description Wording Rules

The `name` + frontmatter `description` pair is a skill's trigger surface: routing matches the user's request against both, name first. These rules govern wording only — structural constraints (name ≤64 chars lowercase/numbers/hyphens, description ≤1024 chars, `metadata.env` manifest) are enforced by skill-manager.

## Naming: the name is the first information carrier

Pick a name a reader can decode without the description. Prefer `arxiv-paper-search` over `apsearch`; prefer `pixel-art-icon` over `icongen`. Every word the name carries is a word the description does not have to repeat.

## Name-first delta principle

Together, name + description must convey WHAT the skill does and WHEN to trigger it — but write the description as the DELTA over the name: only what the name cannot convey (bundled sub-features, data source, method, constraints, trigger vocabulary the name lacks). Never restate the name in different words; a description that adds zero information over the name is wasted always-in-context tokens.

## Length is proportional to the delta

Not a flat target:

| | Single capability | Many bundled sub-features |
|---|---|---|
| **Self-explanatory name** (e.g. `arxiv-paper-search`) | One short sentence: only the source/tool/constraint the name omits | Capability sentence + em-dash list of every bundled sub-feature — each listed feature is a real trigger surface, so the length is earned |
| **Opaque name, or users phrase the task differently** (e.g. `quill`) | Capability sentence + explicit trigger phrases (user verbs, file types, domain terms) | Full form: capability + sub-feature list + trigger phrases |

## Writing rules

- **Always write in third person.** Descriptions are injected into the routing model's system prompt as observable capability statements, not direct address.
  - Good: "Processes Excel files and generates reports."
  - Bad: "I can help you process Excel files."
  - Bad: "You can use this to process Excel files."
- **List trigger keywords only where the name doesn't carry them.** If the name already contains the words users say, don't repeat them. If the name is opaque, or users phrase the task in other words (or another language), list those phrases explicitly.
- **Spell out proper nouns the routing model cannot know.** The router may have an older knowledge cutoff than the skill's domain. Any post-cutoff product name, codename, or niche service that should trigger the skill MUST appear verbatim in the description — without world knowledge, inference is impossible ("픽셀포지로 생성해줘" can never reach `art-studio` unless the token is literally present). Supply a category gloss when the noun alone is meaningless ("PixelForge (image-gen model)"), and include the variants users actually type — Korean transliteration, abbreviations — when they differ from the canonical spelling, because cross-script lexical match cannot be assumed.
- **Keep all "when to use" information in the description.** The body is only loaded after triggering, so a "When to Use This Skill" section in the body never reaches the router.
- **State the routing boundary when sibling skills exist.** For skills in a family (`translator-*`, `formatter-*`, ...), one clause that routes away ("English goes to translator-en"; "structural work goes to skill-manager") prevents mis-triggering.

## Examples (one per quadrant shape)

- Self-explanatory name, single capability — `arxiv-paper-search`:
  > "Search arXiv paper records from the official arxiv.org API with keyword search plus optional category/year narrowing."

  Only the source and sub-options; the name already did the triggering.
- Many bundled sub-features — `art-studio`:
  > "Unified router for image generation, editing, prompting (verified prompt packs and templates), dataset prep, model benchmarking, and image QC. Triggers on art studio, image prompt, PixelForge (픽셀포지), Gemini image, GPT Image, ..."

  Long is justified: every listed sub-feature and model name is a trigger surface the name `art-studio` alone cannot carry — and a router with an older knowledge cutoff cannot infer that "PixelForge" means image generation, so the literal token must be present.
- Anti-example — name restatement (skill `update-kit`):
  > "Update kit when the user wants to update"

  Adds zero information over the name. Either state the delta (what updating involves: which cache, which config) or keep it minimal — never paraphrase the name.

## Anti-patterns

### First or second person voice

Descriptions are injected into the routing model's system prompt as observable capability statements. First or second person voice breaks this routing context.

**Bad:**
```yaml
description: I can help you process Excel files and generate reports.
```

**Bad:**
```yaml
description: You can use this skill to extract text from PDF documents.
```

**Good:**
```yaml
description: Processes Excel files and generates reports. Use when the user uploads an .xlsx file or asks for spreadsheet analysis, pivot tables, or charts.
```

### Description restates the name

A description that merely paraphrases the name adds zero routing information and wastes always-in-context tokens.

**Bad** (skill `update-kit`):
```yaml
description: Update kit when the user wants to update
```

**Bad** (skill `agent-goal-planner`):
```yaml
description: Agent skill for goal-planner - invoke with $agent-goal-planner
```

**Good** (skill `arxiv-paper-search` — the name already triggers; the description carries only the source and sub-options):
```yaml
description: Search arXiv paper records from the official arxiv.org API with keyword search plus optional category/year narrowing.
```

### Vague description without trigger keywords

Without trigger keywords, the router cannot reliably decide when to activate the skill from a pool of 100+ candidates. This applies with full force when the name is opaque or generic — the description is then the only trigger surface. (When the name itself already carries the trigger words, a short delta-only description is correct instead — see the name-restatement anti-pattern above.)

**Bad:**
```yaml
description: Helps with documents.
```

**Good:**
```yaml
description: Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when Claude needs to work with .docx files for creating new documents, modifying or editing content, working with tracked changes, or adding comments.
```

The length here is earned: `docx` bundles many sub-capabilities, and each listed one is a trigger surface. A single-purpose skill with a self-explanatory name must NOT be padded to this length.

### Flat-length descriptions

Padding a single-purpose skill's description to look thorough, or compressing a many-featured router below its trigger surface. Length follows the delta over the name.

### Relying on world knowledge for post-cutoff proper nouns

The routing model may have an older knowledge cutoff than the skill's domain. It cannot infer that an unknown proper noun maps to a capability — matching only works when the token is literally present in the description.

**Bad** (a 2024-cutoff router has no idea what PixelForge is, so "픽셀포지로 생성해줘" never triggers):
```yaml
description: Unified router for image generation and editing with the latest models.
```

**Good** (every product name users say is spelled out; the opening sentence supplies the category gloss):
```yaml
description: Unified router for image generation, editing, prompting, dataset prep, model benchmarking, and image QC. Triggers on art studio, image prompt, PixelForge (픽셀포지), Gemini image, GPT Image, Seedream, or Qwen Image Edit.
```

When users say a variant that differs from the canonical spelling — a Korean transliteration like 픽셀포지, an abbreviation — include that variant too. Cross-script lexical match cannot be assumed, and a category gloss ("PixelForge (image-gen model)") lets even a router that has never seen the noun route it correctly.

### "When to Use" section in the body

The body is loaded only AFTER the skill triggers. Putting trigger context there means the router never sees it.

**Bad** (in SKILL.md body):
```markdown
## When to Use This Skill

Use this skill whenever the user uploads a CSV file or asks about data analysis.
```

**Good** (in YAML frontmatter description):
```yaml
description: Analyzes CSV data with pandas and produces summary statistics, plots, and pivot tables. Use when the user uploads a .csv file or asks for data analysis, descriptive statistics, or visualization.
```

## Checklist

- [ ] Written in third person
- [ ] `name` + `description` together state WHAT the skill does AND WHEN to trigger it
- [ ] Description adds only the delta over the name — no name restatement
- [ ] Length matches the delta: short for a self-explanatory single-purpose name; long only when bundled sub-features or an opaque name earn it
- [ ] Trigger keywords listed where (and only where) the name doesn't carry them
- [ ] Post-cutoff proper nouns appear verbatim, with a category gloss and user-spoken variants (Korean transliteration, abbreviations)
- [ ] Boundary clause present when a sibling family exists
- [ ] Description ≤1024 chars (structural cap — validated by skill-manager's `quick_validate.py`)
