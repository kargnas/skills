---
name: skill-manager
description: Skill structure and lifecycle manager — creates, edits, merges, splits, and sanitizes skills (model-reference checks against models.dev). Use for any create/update/merge/split/cleanup skill request; step wording and name/description wording go to skill-prompter.
license: Complete terms in LICENSE.txt
---

# Skill Manager

This skill provides guidance for the full lifecycle of skill structure — creating new skills, modifying skill structure, merging related skills together, splitting overgrown skills into focused ones, and refactoring directory and file layout.

## Scope and Boundaries

Two skills cover the skill lifecycle. Use the right one — they are not interchangeable.

| Concern | Owner |
|---------|-------|
| Skill creation, directory layout, file separation, typed bundled-resource organization (guides/api-references/sub-skills/scripts/assets), modular architecture decisions, merge/split, structural anti-patterns | **skill-manager (this skill)** |
| Step wording, RFC 2119 keywords, atomic step decomposition, explicit tool naming, VERIFY gates, decision tables, subagent delegation, escape hatches, dry-run compliance for weaker LLMs, skill name + description wording (trigger surface) | **skill-prompter** |

**Decision rule:**
- "I need a new skill from scratch" → skill-manager (then hand the resulting steps to skill-prompter for compliance hardening)
- "Two skills should be merged" or "this skill is too big to split" → skill-manager
- "Steps in my skill are getting skipped on weaker models" → skill-prompter
- "Step instructions are vague or have no VERIFY gate" → skill-prompter
- "Pick the skill's name" or "write/review the description" → skill-prompter (its `references/description-rules.md`)
- Both axes need work → skill-manager first (structure), then skill-prompter (wording), then dry-run on both

If the request is purely about step wording or compliance, **delegate to skill-prompter** instead of proceeding here.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform Claude from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else Claude needs: system prompt, conversation history, other Skills' metadata, and the actual user request.

**Default assumption: Claude is already very smart.** Only add context Claude doesn't already have. Challenge each piece of information: "Does Claude really need this explanation?" and "Does this paragraph justify its token cost?"

Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

Think of Claude as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).

### Modular Architecture Decision (Multiple Skills vs. Single Skill)

Before creating a skill, decide whether the capability belongs as a standalone skill or as sub-content under an existing skill. This is one of the most important architectural decisions.

| Approach | Use When | Trade-off |
|----------|----------|-----------|
| **Multiple separate skills** | Capabilities are independent and reusable in isolation (e.g., `pdf-extract`, `excel-analysis`) | Each triggers individually; smaller context per use; but no shared schemas |
| **Single skill with multiple files** | Capabilities are tightly related and share context (e.g., a `clickhouse-expert` with sub-agents per diagnostic area) | Unified orchestration and shared context; but SKILL.md always loads on trigger |

**Quick decision rule:** If a user might invoke capability A without ever needing capability B, make them separate skills. If A and B always work together as parts of the same workflow, make them a single skill with subdirectories.

For detailed criteria, cross-skill chaining patterns, and hybrid architectures, see [guides/modular-architecture.md](guides/modular-architecture.md).

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional, TYPED by kind — see taxonomy below)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── guides/           - How-to / design prose Claude READS while working
    ├── api-references/   - Lookup data that is GREPPED (API docs, schemas, specs)
    ├── sub-skills/       - Bundled sub-capabilities with their own instructions, INVOKED
    ├── assets/           - Files used in output (templates, icons, fonts, etc.)
    └── references/       - UNTRIAGED INBOX (agent dumps land here; not curated)
```

Create only the folders a skill actually needs — `guides/`, `api-references/`, and `sub-skills/` are documented here as the available kinds, NOT mandatory empty directories.

#### Where the skill directory lives — flat vs categorized

Skill anatomy is `skill-name/SKILL.md`. There is NO category folder layer in the anatomy itself. But different agents have different host-directory conventions:

| Host | Convention | Category folder allowed? |
|------|------------|--------------------------|
| Shared / cross-agent (`~/.agents/skills/`) | FLAT — `~/.agents/skills/<skill-name>/SKILL.md` | NO. Do not insert category dirs like `~/.agents/skills/research/<skill-name>/`. The host is treated as a flat skill registry. |
| Category-based hosts (`<agent-home>/skills/`) | Categorized — `<agent-home>/skills/<category>/<skill-name>/SKILL.md` | YES, when the host uses category subfolders for browsability. |
| Codex (`$CODEX_HOME/skills/`) | Flat — `$CODEX_HOME/skills/<skill-name>/SKILL.md` | NO. |

**Cross-agent sharing pattern (when authoring a skill that should run from multiple agents):**

1. Place the canonical body in the shared flat location: `~/.agents/skills/<skill-name>/`.
2. From each per-agent host that uses categories, create a symlink under the appropriate category:
   `ln -s ~/.agents/skills/<skill-name> <agent-home>/skills/<category>/<skill-name>`
3. Inside SKILL.md and any bundled scripts, hard-code paths to the canonical location (`~/.agents/skills/<skill-name>/...`), NOT to the per-agent symlink path. Symlinks can be re-pointed; the canonical path is stable.
4. Cache directories should live under the host's own cache, but be namespaced by the canonical skill name (e.g., `<agent-home>/cache/<skill-name>/`), not by the symlinked category path.

**Name-collision check before placing a skill in `~/.agents/skills/`:** the shared registry is flat, so `ls ~/.agents/skills/ | grep <proposed-name>` MUST return zero matches. If it doesn't, rename to a more specific name (e.g., if `find-skills` already exists for an npm-registry search, a GitHub-search variant must be `find-github-skills`).

#### SKILL.md (required)

Every SKILL.md consists of:

- **Frontmatter** (YAML): Contains `name` and `description` fields. These are the only fields that Claude reads to determine when the skill gets used, thus it is very important to be clear and comprehensive in describing what the skill is, and when it should be used.
- **Body** (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the skill triggers (if at all).

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by Claude for patching or environment-specific adjustments

##### Typed reference resources — classify by kind, NOT a single `references/` dump

Documentation and reference material is loaded into context as needed to inform Claude's process. Historically all of it went into one `references/` folder, which degrades into an undifferentiated junk drawer the moment more than a few files accumulate — and worse, some agent harnesses HARDCODE their writes into `references/`, mixing genuine curated docs with throwaway session slop so the two can no longer be told apart.

To keep curated content distinguishable, **classify each documentation resource by its KIND and route it to a typed folder**:

| Folder | Kind | Lifecycle / access | Examples |
|--------|------|--------------------|----------|
| `guides/` | How-to and design prose | Claude READS the whole file while working | `guides/communication.md`, `guides/modular-architecture.md`, workflow walkthroughs, decision criteria |
| `api-references/` | Lookup data | Usually GREPPED for a specific entry, not read end-to-end | `api-references/finance.md` (schemas), `api-references/endpoints.md`, format specs, DB table catalogs |
| `sub-skills/` | A bundled sub-capability | INVOKED as a mini-procedure, not merely read | `sub-skills/redline-docx/` — its own instructions + optional resources, run when that branch triggers |
| `references/` | **UNTRIAGED INBOX** | Not curated; awaiting promotion or deletion | Whatever agents dump here. See the inbox rule below. |

**Classification decision rule:** ask *how the file is consumed*. Read front-to-back as guidance → `guides/`. Searched for one fact → `api-references/`. Carries its own steps that get executed → `sub-skills/`. If a resource fits none of these, name a new folder by its kind (e.g. `templates/`, `schemas/`) rather than falling back to `references/`.

**The `references/` inbox rule (why this diverges from the upstream Anthropic spec):** upstream skills use `references/` as the normal home for curated docs. This registry deliberately does NOT, *because* some agent harnesses hardcode their dumps into `references/` and cannot be redirected. So here `references/` is redefined as an untriaged inbox: periodically TRIAGE it — promote anything worth keeping into the matching typed folder (rewriting it into the skill's voice), and delete the rest. Never link curated workflow content to a `references/` path and never treat a `references/` file as authoritative; if it matters, it must be promoted out first. (A future agent that "fixes" this back to the upstream meaning would re-merge the slop — keep this note.)

**Migrating an EXISTING skill's `references/` — MUST ask the user first, never auto-migrate.** When applying this taxonomy to a skill that already has a populated `references/` folder, do NOT silently move or classify its files. That folder may already be packed with accumulated slop, half-finished notes, and a few genuinely valuable docs all mixed together — and only a human knows which is which. Auto-promoting would launder slop into `guides/`; auto-deleting would destroy validated history. Instead:

1. **Inventory, don't touch.** List every file in `references/` with a one-line summary of what it contains (read enough of each to summarize).
2. **Propose a triage table** mapping each file to a suggested action — `→ guides/`, `→ api-references/`, `→ sub-skills/`, `keep in inbox`, or `delete` — with a short reason per row.
3. **Ask the user to confirm or amend the table.** MUST get explicit approval before any move or delete. Bulk approval ("apply all suggestions") is fine, but the user has to give it.
4. **Only then** execute the moves/deletes, re-point any SKILL.md links, and re-run `scripts/audit_skill_links.py` to confirm zero unexpected orphans.

For a brand-new skill there is nothing to triage — just create typed folders directly. This ask-first rule applies ONLY to migrating pre-existing `references/` content.

- **When to include**: For documentation Claude should consult while working — placed in the typed folder matching its kind.
- **Benefits**: Keeps SKILL.md lean; the folder name alone tells the next agent what kind of content it is and whether it is curated or inbox slop.
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md (especially for `api-references/`).
- **Linkage requirement**: Every file in a typed folder MUST be linked from SKILL.md. `scripts/audit_skill_links.py` reports unlinked typed-folder files as ORPHANS (an error) and unlinked `references/` files as TO TRIAGE (expected).
- **Avoid duplication**: Information should live in either SKILL.md or a typed reference file, not both. Prefer the typed file for detailed material unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window.

##### Assets (`assets/`)

Files not intended to be loaded into context, but rather used within the output Claude produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables Claude to use files without loading them into context

#### What to Not Include in a Skill

A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files, including:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- etc.

The skill should only contain the information needed for an AI agent to do the job at hand. It should not contain auxilary context about the process that went into creating it, setup and testing procedures, user-facing documentation, etc. Creating additional documentation files just adds clutter and confusion.

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by Claude (Unlimited because scripts can be executed without reading into context window)

#### Progressive Disclosure Patterns

Keep SKILL.md body to the essentials and under 500 lines to minimize context bloat. Split content into separate files when approaching this limit. When splitting out content into other files, it is very important to reference them from SKILL.md and describe clearly when to read them, to ensure the reader of the skill knows they exist and when to use them.

**Key principle:** When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in SKILL.md. Move variant-specific details (patterns, examples, configuration) into separate reference files.

**Pattern 1: High-level guide with references**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

Claude loads FORMS.md, REFERENCE.md, or EXAMPLES.md only when needed.

**Pattern 2: Domain-specific organization**

For Skills with multiple domains, organize content by domain to avoid loading irrelevant context:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── api-references/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

When a user asks about sales metrics, Claude only reads sales.md.

Similarly, for skills supporting multiple frameworks or variants, organize by variant:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── guides/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

When the user chooses AWS, Claude only reads aws.md.

**Pattern 3: Conditional details**

Show basic content, link to advanced content:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

Claude reads REDLINING.md or OOXML.md only when the user needs those features.

**Important guidelines:**

- **Avoid deeply nested references** - Keep references one level deep from SKILL.md. All reference files should link directly from SKILL.md.
- **Structure longer reference files** - For files longer than 100 lines, include a table of contents at the top so Claude can see the full scope when previewing.

## Skill Creation Process

Skill creation involves these steps:

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Choose the skill location (ask the user)
4. Initialize the skill (run init_skill.py)
5. Edit the skill (implement resources and write SKILL.md)
6. Iterate based on real usage

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. An `api-references/schema.md` file documenting the table schemas would be helpful to store in the skill

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

### Step 3: Choose Skill Location

Before initializing, resolve where the skill should live. If the user explicitly named a target path or host, use that target after checking for existing symlinks and name collisions.

If the user did not specify a location and the environment allows asking the user, ask "Where do you want to install the skill?" and recommend one of these default choices:

| Priority | Scope | Path | Recommend when |
|----------|-------|------|----------------|
| 1 | Project — shared | `<projectroot>/.agents/skills/<skill-name>/` | The skill is likely to be reused often inside the current repository, or it encodes project-specific workflows, conventions, commands, or files. |
| 2 | User — shared registry | `<userhome>/.agents/skills/<skill-name>/` | Default fallback when the skill is general-purpose, cross-project, or the project-specific signal is weak. |

If the environment cannot ask the user (unattended automation, non-interactive run, or question tools unavailable), choose automatically using the same priority order: Project — shared only when there is concrete evidence that the skill belongs to the current repository; otherwise User — shared registry.

**Auto-select guardrail — host-specific folders are off-limits to the automatic path.** When choosing automatically (no user confirmation), the resolved location MUST be one of the two `.agents` shared locations only (`<projectroot>/.agents/skills/` or `<userhome>/.agents/skills/`). The automatic path MUST NOT select any host-specific skills folder — `.claude/skills/` (User or Project Claude Code), `.config/opencode/skills/`, or any other per-agent skills dir — because those single-host targets bypass cross-agent sharing and their loader precedence makes the choice hard to reverse. Host-specific folders are reachable ONLY when the user explicitly names that path or host (the first sentence of this step); they are never an auto-default. The `.agents` → `.claude/skills` symlink rule below is the supported way Claude Code still discovers an auto-placed `.agents` skill — the skill body lives in `.agents`, not in `.claude`.

The resolved location determines the path passed to `init_skill.py` and decides whether a symlink needs to be created. Check if there are any symlinks already before proposing or auto-selecting locations.

**Standard locations:**

| Scope | Path | Used by |
|-------|------|---------|
| Project — shared | `<projectroot>/.agents/skills/<skill-name>/` | All agents working in this project |
| User — shared registry | `<userhome>/.agents/skills/<skill-name>/` | All agents on this machine |
| User — Claude Code | `<userhome>/.claude/skills/<skill-name>/` | Claude Code only |
| User — OpenCode | `<userhome>/.config/opencode/skills/<skill-name>/` | OpenCode only |
| Project — Claude Code | `<projectroot>/.claude/skills/<skill-name>/` | Claude Code working in this project |
| User — other agent host | That agent's own skills dir (may use category subfolders) | That agent only |
| Other | User-specified path | Custom integrations |

Phrase the question concretely (e.g. "Where do you want to install the skill?") and list the options above. Wait for confirmation before continuing.

**Project-level `.agents` → `.claude/skills` symlink rule:**

When the user picks `<projectroot>/.agents/skills/`:
1. Check whether `<projectroot>/.claude/skills/` already exists (real directory or any symlink).
2. If it does NOT exist, create a relative symlink so Claude Code discovers the same skills:
   ```bash
   mkdir -p <projectroot>/.claude
   ln -s ../.agents/skills <projectroot>/.claude/skills
   ```
   The relative target (`../.agents/skills`) survives project relocation.
3. If `<projectroot>/.claude/skills/` already exists, do NOT overwrite. Report the conflict to the user and ask how to resolve (keep existing, merge, replace).

For the shared `~/.agents/skills/` registry, also run the name-collision check from "Where the skill directory lives" before placing the new directory.

### Step 4: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists. In this case, continue to the next step.

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates example resource directories: `scripts/`, `guides/`, and `assets/`
- Adds example files in each directory that can be customized or deleted

After initialization, customize or remove the generated SKILL.md and example files as needed.

### Step 5: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Claude to use. Include information that would be beneficial and non-obvious to Claude. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Claude instance execute these tasks more effectively.

#### Importing or repackaging external skills

When importing a community skill into a host registry, treat it as skill architecture work, not a blind copy:

1. Check for name collisions in the target registry before copying.
2. Rename to the user's class-level naming convention when needed (for example, language suffixes like `translator-ko`, `translator-zh`, `translator-ja`).
3. Normalize frontmatter to the target host's routing rules. If upstream uses non-standard routing fields such as `when_to_use`, merge those trigger phrases into `description` so the skill actually triggers.
4. Preserve upstream provenance in `metadata.upstream` and `metadata.upstream-version` when available.
5. Prefer extracting reusable pattern packs or references from a large upstream skill when the whole upstream package would collide with existing class-level skills.
6. Patch related router/umbrella skills so future agents know the new skill or reference exists.

#### Learn Proven Design Patterns

Consult these helpful guides based on your skill's needs:

- **Multi-step processes**: See guides/workflows.md for sequential workflows and conditional logic
- **Specific output formats or quality standards**: See guides/output-patterns.md for template and example patterns

These files contain established best practices for effective skill design.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, typed reference folders (`guides/`, `api-references/`, `sub-skills/`), and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `guides/`.

Added scripts must be tested by actually running them to ensure there are no bugs and that the output matches what is expected. If there are many similar scripts, only a representative sample needs to be tested to ensure confidence that they all work while balancing time to completion.

Any example files and directories not needed for the skill should be deleted. The initialization script creates example files in `scripts/`, `guides/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter with `name` and `description`:

- `name`: The skill name. Max 64 chars, lowercase letters/numbers/hyphens only. No reserved words ("anthropic", "claude").
- `description`: Together with `name`, the triggering mechanism for the skill. Structural constraints: max 1024 chars, non-empty.

  **Wording is skill-prompter's domain.** How to pick the name and write the description — the name-first delta principle, length proportional to bundled sub-features, trigger keywords, post-cutoff proper nouns, sibling boundary clauses — is trigger-surface prompt wording. When naming a skill or writing/reviewing a description, route that work to **skill-prompter** and apply its rules in `~/.agents/skills/skill-prompter/references/description-rules.md`. Only the structural constraints above (plus the `metadata.env` manifest below) are enforced here.

###### Metadata: ENV variable manifest (mandatory when the skill reads env vars)

Any skill whose body, `scripts/`, or bundled resource files (`guides/`, `api-references/`, `sub-skills/`, `references/`) reads an environment variable MUST declare every such variable under `metadata.env` in the frontmatter. This makes a skill's runtime secret/config dependencies discoverable without reading the whole skill, and it is enforced on every create / edit / merge / split pass.

**Format** — a map keyed by the exact variable name the skill reads; value is `<required|optional> — <one-line purpose>`:

```yaml
metadata:
  env:
    OPENROUTER_API_KEY: "required — LLM calls via OpenRouter"
    GEMINI_API_KEY: "optional — image-gen fallback"
```

**Rules:**

| Rule | Keyword |
|------|---------|
| Declare every env var the skill actually reads (`os.environ`, `process.env`, `getenv`, `$VAR`, `${VAR}`) | MUST |
| Key each entry by the variable name the skill reads, not the source it is mapped from | MUST |
| Mark each entry `required` or `optional` and give a one-line purpose | MUST |
| List machine-local source variables (the private vars a local `.env` maps secrets from) anywhere in metadata, body, or scripts | MUST NOT |
| Omit `metadata.env` entirely when the skill reads zero env vars | MAY |

The source-variable prohibition exists because those are local-`.env`-only source secrets. A skill reads the mapped name (e.g. `OPENROUTER_API_KEY`), so that mapped name — never the machine-local source it is mapped from — is what gets declared.

**VERIFY** — run from the skill directory; every variable the grep surfaces (excluding machine-local source variables) MUST appear as a `metadata.env` key:

```bash
grep -rhoE '\$\{?[A-Z][A-Z0-9_]+\}?|process\.env\.[A-Z][A-Z0-9_]+|os\.environ(\.get)?\(['"'"'"][A-Z0-9_]+|getenv\(['"'"'"][A-Z0-9_]+' SKILL.md scripts/ guides/ api-references/ sub-skills/ references/ 2>/dev/null | sort -u
```

Reconcile the grep output against the `metadata.env` keys. If grep finds a var missing from `metadata.env`, add it before finalizing.

**IF BLOCKED**: grep unavailable → manually scan every script and the body for env access and reconcile against `metadata.env`. Do NOT skip the reconciliation.

Beyond `name` and `description`, the only permitted frontmatter is the optional `metadata` block (e.g. `metadata.env` above, `metadata.upstream`). Do not add other top-level frontmatter fields.

##### Body

Write instructions for using the skill and its bundled resources.

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again

For an evaluation-driven approach (build evaluations BEFORE writing extensive documentation), see [guides/evaluation.md](guides/evaluation.md).

## Conversation-review maintenance pass

When the user asks to review a session and update the skill library, treat it as an action-biased maintenance pass, not a passive summary.

### Update preference order

1. **Patch a currently-used skill first** if the new learning belongs to a skill that was loaded or explicitly invoked in the session.
2. **Otherwise patch an existing class-level umbrella skill** that already governs the class of task.
3. **Otherwise add a support file** under the best existing umbrella. Use `references/<topic>.md` for session-specific detail, error transcripts, reproduction recipes, provider quirks, condensed research/API/domain notes; use `templates/<name>.<ext>` for copy-and-modify starter files; use `scripts/<name>.<ext>` for deterministic re-runnable actions. Add a one-line SKILL.md pointer to any new support file so future agents discover it.
4. **Create a new class-level umbrella skill only when no existing class-level skill covers the learning.** Never create one-session-one-skill entries named after a PR number, error string, feature codename, library-alone name, or today's fix/debug/audit artifact.

If the touched skill still has a populated legacy `references/` inbox, do NOT fold it into this pass automatically — migrating it to the typed taxonomy is a separate, ask-first operation (see "Migrating an EXISTING skill's `references/`" in the typed-resources section).

### What counts as update-worthy

Any of the following should normally produce a skill update:
- User correction about style, tone, verbosity, formatting, or legibility
- User correction about workflow, sequencing, or how the task should be carried out
- A reusable workaround, verification pattern, or debugging path that future runs would benefit from
- Evidence that a consulted skill was missing a step, pitfall, or boundary

### Storage rule: memory vs skill

- Use **memory** for stable facts about the user or environment.
- Use **skills** for repeatable how-to knowledge.
- If the user complained about *how a task was handled*, encode that lesson in the governing skill body, not only in memory.

### Bias against no-op reviews

`Nothing to save.` is acceptable only when the session truly produced no correction, no reusable technique, and no skill gap. Do **not** default to no-op just because the learning is small; a one-paragraph pitfall or a small support reference often has real future value.

### Interrupted-session review rule

If the conversation contains an unfinished earlier task plus a later explicit request to review the session and update the skill library, the **review request becomes the active task**. Do not resume the interrupted task during the maintenance pass. Instead, mine that earlier work for learnings and patch the governing skill or support files.

### Prefer support-file capture for session-specific lessons

When the learning is real but too session-specific to justify canonical SKILL.md edits, prefer updating the currently-relevant umbrella skill with a concise support file entry (or appending to its existing session/changelog reference) rather than forcing a new narrow skill or bloating the main SKILL.md.

### Oversize-skill patch failure rule

If `skill_manage(action='patch')` fails because the target `SKILL.md` exceeds the tool's content limit (observed failure shape: `SKILL.md content is ... > 100000 characters`), do **not** keep retrying tiny inline patches against that same oversized file. Treat the umbrella as structurally full for this pass and capture the learning in the smallest valid place instead:

1. patch an existing typed support file (`guides/*.md`, `api-references/*.md`) that already governs the pitfall, or
2. append a concise entry to the skill's existing changelog/session reference, or
3. add a new support file in the typed folder matching its kind and mention the deferred canonicalization in your reply.

This is a tool-limit problem, not evidence that the lesson is too small to save.

## Importing External Skills (community SKILL.md → local skills dir)

When the user wants to install a community skill (typically discovered via a skill-discovery search) into their local skills directory, follow the full procedure in [guides/importing-external-skills.md](guides/importing-external-skills.md). For HEAVY / collector-bundled framework repos (10MB+, ships network data-collectors + marketing assets) where the user asks to "verify first," also read [references/importing-heavy-collector-repos.md](references/importing-heavy-collector-repos.md) — it has the exfil/data-destination grep gate, the rsync slim-on-import pattern, and the empty-shell collision check. Key points:

- **Collision check first** — `ls <skills-dir> | grep <name>` before clone. Never blind-`cp -r` into the target.
- **Frontmatter normalization** — strip non-standard fields like `when_to_use` by merging keywords into `description` (router ignores unknown fields, so a copy-paste import often doesn't trigger).
- **Provenance** — record `metadata.upstream: "<repo-url> (<path>)"` so future updates can re-sync.
- **Commit message format** — include source URL, version, and the frontmatter changes made.

## Refactoring: Merging and Splitting Skills

A skill rarely stays in its original shape forever. Apply the modular architecture decision rule when boundaries need to change.

**Merging trigger conditions** (combine multiple skills into one):
- Same skills invoked together in 3+ real-use chains
- Shared schemas/conventions that would otherwise be duplicated
- Coordination via routing table reduces overall surface area more than independent triggering helps

**Splitting trigger conditions** (break one skill into multiple):
- SKILL.md exceeds 500 lines with references grouped by independent domains
- Sub-capabilities are invoked independently (users hit only one branch at a time)
- Sub-capabilities have unrelated trigger keywords that compete for the same description

For the full merging and splitting procedures (6 numbered steps each, plus shared-content audit rules and trade-offs), see [guides/modular-architecture.md](guides/modular-architecture.md).

**Absorption variant of merge** (sources stay on disk, new skill is runtime-independent): when the merge is across community / shared / general-purpose source skills that have OTHER consumers, use the absorption pattern instead of the standard merge — sources do NOT get deleted, the new skill ABSORBS their relevant knowledge into its own voice, and a grep gate enforces self-containment. See [guides/merge-via-absorption.md](guides/merge-via-absorption.md) for the full spec template, grep-gate acceptance criteria, and delegate-of-choice guidance (verified 2026-05-24 on a mobile-ux audit skill that absorbed two source skills via an in-session subagent delegation in 9 min after CLI delegations failed on auth quota).

After merging or splitting, re-run the **Final Skill Quality Checklist** AND **Dry Run Verification** for every resulting skill.

When the umbrella has many internal files (~20+, multiple subdirectories), also run the link-graph audit to catch broken cross-file links and orphan files left behind by the move:

```bash
uv run python scripts/audit_skill_links.py <skill-dir>
```

See [guides/link-graph-audit.md](guides/link-graph-audit.md) for triage rules and known false-positive patterns.

## Anti-Patterns to Avoid

These patterns appear frequently in low-quality skills and must be avoided when creating or editing any skill.

### Description anti-patterns

Owned by **skill-prompter** — first/second person voice, name restatement, vague trigger surface, flat length, post-cutoff proper nouns, "when to use" in the body. See `~/.agents/skills/skill-prompter/references/description-rules.md`.

### Structure anti-patterns

- **Windows-style paths** (`scripts\helper.py`). Always use forward slashes (`scripts/helper.py`).
- **Deeply nested references** (SKILL.md → advanced.md → details.md). Keep references one level deep from SKILL.md to avoid partial reads.
- **Time-sensitive information** ("If before August 2025, use old API"). This rots quickly; isolate legacy notes into a separate section.
- **Extraneous documentation files** like README.md, INSTALLATION_GUIDE.md, QUICK_REFERENCE.md, CHANGELOG.md inside the skill directory. Skills contain only what an AI agent needs to do the job.
- **Duplicating content** between SKILL.md and reference files. Information should live in exactly one place.

### Content anti-patterns

- **Too many options** ("Use pypdf, or pdfplumber, or PyMuPDF, or..."). Pick one default and document narrow exceptions.
- **Verbose explanations of common knowledge.** Trust that Claude already knows what a PDF is or what a database does.
- **Abstract examples** instead of concrete ones. Show actual input/output, not "imagine a scenario where...".
- **Few-shot answer keys in verification prompts.** Documentation examples may teach structure, but dry-run or subagent verification prompts MUST be black-box and MUST NOT include expected answers, known weak points, before/after examples, label hints, or pass/fail explanations.

### Script anti-patterns

- **Punting errors back to Claude** instead of handling them in the script. Scripts should solve problems, not delegate failures.
- **Magic constants without justification** (`TIMEOUT = 47`). Every numeric constant should have a comment explaining the choice.

### Cross-agent / multi-host anti-patterns

When a skill lives under the shared `~/.agents/skills/` store and is consumed by multiple agents (Claude Code, Codex, OpenCode, others) via symlinks:

- **Don't put host-specific category folders** (`research/`, `creative/`) inside `~/.agents/skills/`. Keep `<skill-name>/SKILL.md` flat. Each host symlinks into its own category convention.
- **Don't blind-`mv` into the shared store** without checking for a same-named collision — `mv my-skill ~/.agents/skills/` silently nests inside an existing `my-skill/` directory, producing `~/.agents/skills/my-skill/my-skill/SKILL.md`. Run `ls ~/.agents/skills/ | grep -i <name>` first and decide rename / absorb / drop explicitly.
- **Don't hardcode host paths** (`~/.claude/skills/...`, `~/.codex/skills/...`) inside SKILL.md or scripts. Reference the canonical `~/.agents/skills/<name>/...` path so every host loading the skill via symlink gets a working path.

For detailed examples and counter-examples, see [guides/anti-patterns.md](guides/anti-patterns.md). For script-specific best practices, see [guides/scripts-best-practices.md](guides/scripts-best-practices.md).

## Sanitization Pass: Outdated LLM Model Detection

When a skill references LLM model IDs in its body, scripts, or references, MUST run this sanitization pass before finalizing. Outdated model IDs ship inferior quality and often cost more per token than current alternatives. The user MUST be offered an upgrade with a cost comparison before the skill is marked complete.

### When this pass runs

MUST run during:
- Skill creation, during Step 4 (Edit the Skill), before SKILL.md is written to disk
- Skill editing whenever the diff touches any string matching an LLM model ID pattern
- Conversation-review maintenance pass when a touched skill references models
- Explicit user request: "sanitize skill", "check skill models", "스킬 검증", "모델 업그레이드"

### Step 1 [SAN1]: Scan for model references

**Action**: Run grep across the skill directory for known LLM model ID patterns.

```bash
grep -rEn '(gpt-[0-9.]+[a-z0-9.-]*|o[0-9]+(-[a-z]+)?|claude-(opus|sonnet|haiku)-[0-9.]+[a-z0-9.-]*|gemini-[0-9.]+[a-z0-9.-]*)' <skill-dir>/
```

Save every match as a `(file, line, matched_id)` tuple.

**VERIFY**: grep exit code is 0 (matches found) or 1 (no matches). If no matches, SKIP remaining sanitize steps and proceed to Dry Run Verification.

### Step 2 [SAN2]: Classify each match

**Action**: For each matched ID, look up its status using the reference table below. MUST also confirm via `WebFetch https://models.dev` for any ID not present in the table, or when the table's freshness is uncertain.

| Detected pattern | Status | Suggested replacement (verify with models.dev) |
|------------------|--------|------------------------------------------------|
| `gemini-1.x-*` | OUTDATED | `gemini-3-flash-preview` or `gemini-3.1-pro-preview` |
| `gemini-2.0-*` | OUTDATED | `gemini-3-flash-preview` |
| `gemini-2.5-flash` | OUTDATED | `gemini-3-flash-preview` |
| `gemini-2.5-flash-lite` | OUTDATED | `gemini-3-flash-preview` (no flash-lite at 3.x as of 2026-05; reconfirm via models.dev) |
| `gemini-2.5-pro` | OUTDATED | `gemini-3.1-pro-preview` |
| `gemini-3-*` (non-preview) | CHECK | reconfirm whether a newer preview revision exists |
| `claude-3-*`, `claude-3-5-*` | OUTDATED | `claude-haiku-4-5-20251001` / `claude-sonnet-4-5-20250929` |
| `claude-sonnet-4-20250514` | OUTDATED | `claude-sonnet-4-5-20250929` |
| `claude-opus-4*` (4.0–4.5) | OUTDATED | `claude-opus-4-7` |
| `gpt-4*`, `o1-*`, `o3-*` | OUTDATED | `gpt-5.2-2025-12-11` or `gpt-5.2-pro` |
| `gpt-5-2025-08-07`, `gpt-5-mini-*`, `gpt-5-nano-*` | OUTDATED | `gpt-5.2-2025-12-11` |
| `gpt-5.1-*` | OUTDATED | `gpt-5.2-2025-12-11` |

| Lookup outcome | Action |
|----------------|--------|
| In table as OUTDATED | Carry replacement to SAN3 |
| In table as CURRENT | Skip — no proposal needed |
| Not in table | WebFetch models.dev → classify → if still ambiguous, mark UNKNOWN and continue |

**VERIFY**: Every match has status ∈ {CURRENT, OUTDATED, UNKNOWN}. No match is left unclassified.

### Step 3 [SAN3]: Look up cost for each upgrade pair

**Action**: For every OUTDATED → replacement pair, collect input and output cost per 1M tokens.

Lookup priority:
1. `WebFetch https://models.dev` (authoritative live data)
2. Provider pricing pages (fallback)
3. CLAUDE.md "AI Models" table (cached snapshot; note the date stamp)

**VERIFY**: Each pair has four numbers: `old_input_$/1M`, `old_output_$/1M`, `new_input_$/1M`, `new_output_$/1M`. Missing numbers mark the pair as "cost-unknown" and continue.

### Step 4 [SAN4]: Build the upgrade proposal

**Action**: MUST emit one proposal block per OUTDATED finding.

```
Outdated model detected: `{old_id}` at `{file}:{line}`

| Metric    | Current `{old_id}` | Proposed `{new_id}` | Δ      |
|-----------|--------------------|---------------------|--------|
| Input/1M  | ${old_in}          | ${new_in}           | {±X%}  |
| Output/1M | ${old_out}         | ${new_out}          | {±X%}  |

Apply upgrade? (y / n / skip-all)
```

`Δ` MUST be signed (`+12%` increase, `-30%` decrease). For "cost-unknown" pairs, replace the numeric rows with `(cost data unavailable — see models.dev)`.

**VERIFY**: One proposal block exists per OUTDATED finding. No proposal exists for CURRENT or UNKNOWN findings.

### Step 5 [SAN5]: Apply the user's decision

**Action**: For each proposal, process the user's reply using the decision table.

| User reply | Action |
|------------|--------|
| `y` / `yes` / `apply` | Edit the file in-place: replace `{old_id}` with `{new_id}` at the recorded line. Log the change. |
| `n` / `no` / `keep` | Leave the file unchanged. Log the decline (with reason if provided). |
| `skip-all` | Leave all remaining findings unchanged. Halt the sanitize pass. |
| anything else | Re-ask once verbatim. On the second non-matching reply, treat as `n`. |

MUST NOT auto-upgrade without explicit affirmative reply. Lower cost alone is not authorization to edit.

**VERIFY**: Every emitted proposal has a recorded outcome ∈ {applied, declined, skipped}.

### Step 6 [SAN6]: Re-scan and finalize

**Action**: If any replacement was applied in SAN5, re-run the SAN1 grep. Then write a one-line summary to stdout (and to the skill's session/changelog reference if one exists):

```
sanitize-{YYYY-MM-DD}: scanned={N}, outdated={K}, applied={A}, declined={D}, unknown={U}
```

**VERIFY**: Re-scan grep returns no OUTDATED matches OR every remaining OUTDATED match was explicitly declined in SAN5. Summary line is recorded.

### Escape hatches

| Blocker | Fallback |
|---------|----------|
| No internet → cannot WebFetch models.dev | Use CLAUDE.md AI Models table only; append "(live confirmation unavailable)" to every proposal |
| User unreachable (unattended/automated run) | Do NOT edit files. Append `SANITIZE_PENDING.md` inside the skill dir listing every OUTDATED finding for later human review |
| WebFetch fails AND model not in table | Mark UNKNOWN. Do NOT propose. Append to `SANITIZE_PENDING.md` |
| User declined an upgrade earlier in the same session | Do NOT re-prompt for the same `(file, line, old_id)` tuple |

## Dry Run Verification

Every skill creation, modification, merge, or split MUST end with a dry-run verification before being considered complete. Anti-Patterns review and the Final Quality Checklist are static reviews — dry-run is the dynamic execution check that confirms the skill actually triggers and runs end-to-end.

### When dry-run is required

- After creating a new skill (Step 4 complete)
- After updating an existing skill's structure
- After merging multiple skills into one
- After splitting one skill into multiple skills

### Dry-run procedure

1. **Construct one representative scenario per skill.** Pick a real user request that should trigger the skill end-to-end. For merge/split outcomes, construct one scenario per resulting skill and verify each independently. The scenario MUST be black-box: do NOT include expected outputs, example solutions, known weak points, or pass/fail hints.

2. **Simulate fresh-context execution.** Use the method that best approximates a clean LLM session:

   | Method | Purpose |
   |--------|---------|
   | Black-box subagent delegation (preferred) | Spawn validators loaded with ONLY the skill metadata/body, the scenario, allowed tools, and the signal table below. The prompt MUST NOT include expected answers, examples, diffs, known weak points, or implementation notes. |
   | Manual walkthrough | Pretend the original conversation does not exist. For each step in the skill body, name the exact action you would invoke given only what the skill provides. Do NOT use hidden expected answers. |

   MUST run the same black-box scenario through both validation lanes:

   | Lane | Required validators |
   |------|---------------------|
   | Cost-efficient | One Sonnet-family validator, one Kimi-family validator, one GPT-mini(or nano)-family validator, one Deepseek-flash-family validator and one GLM-family validator available in the active runner. (Use `opencode-go` provider with OpenCode CLI) |
   | Frontier | At least one high-cost frontier validator available in the active runner — NEVER a Fable/Mythos-class model (see the validator model policy below). Opus qualifies for this lane ONLY when the user explicitly requests it; otherwise pick a non-Anthropic frontier family. |

   **Validator model policy (HARD): Fable/Mythos-class models (`claude-fable-*`, `claude-mythos-*`) are FORBIDDEN for dry-run.** "High-cost frontier" MUST NOT be read as "most expensive model available": dry-run fans out across many validators, so the validator model's per-token price multiplies with no added verification value. The ban covers every route — explicit model flags, harness subagent delegation, and model inheritance (a Fable-class parent session MUST pass an explicit non-Fable model on every validator or orchestrator spawn). The Claude-family default for dry-run work is Sonnet (latest); Opus MAY be used ONLY on the user's explicit request.

   If a required model family is unavailable, run every available validator and write `DRYRUN_PENDING.md` with the missing family. The dry-run is not PASS until all required lanes run or the user explicitly accepts the gap.

3. **Verify these signals during the simulated run:**

   | Signal | Pass criterion |
   |--------|----------------|
   | Trigger | The skill's `description` correctly matches the scenario request (the simulator chooses to load this skill) |
   | Body usage | The simulator follows the documented procedure without inventing missing steps |
   | References | Every typed-folder link the simulator follows (e.g. `[guides/X.md]`, `[api-references/X.md]`) actually exists and loads |
   | Outputs | The simulator produces an artifact in the documented final shape |
   | No silent skips | No step is bypassed without an explicit, documented reason |
   | No answer leakage | Validator prompts contain no few-shot hints, expected outputs, weak-point notes, or pass/fail explanations |
   | Model coverage | Sonnet, Kimi, GLM, and frontier validators all ran the same black-box scenario; ZERO validators ran on a Fable/Mythos-class model |

4. **For merged skills:** verify that every use case from each original skill still works. Run one scenario per original skill against the merged skill — every original use case MUST pass.

5. **For split skills:** verify that each new skill is triggered ONLY by its intended scenarios (no cross-contamination), AND that scenarios that previously hit one boundary now correctly route to the appropriate new skill.

### Pass condition

Dry-run is PASS only when every signal in the table above holds for every constructed scenario. Any failure → return to the relevant Step or Refactoring procedure, fix the issue, and re-run dry-run. Do NOT mark the skill complete with any failing dry-run signal.

### Persistence: DRYRUN_PENDING.md fallback

Because skill-manager has no `tracker.py` of its own, dry-run completion is enforced by an in-tree marker file:

| Outcome | Required artifact |
|---------|-------------------|
| Dry-run PASSED for every scenario | Do nothing. The Final Quality Checklist's dry-run box may be ticked. |
| Dry-run skipped (subagent unavailable AND manual walkthrough impractical) | MUST write `DRYRUN_PENDING.md` at the skill's root containing: today's date, the constructed scenario(s), the reason dry-run could not run, and the human follow-up needed. |
| Dry-run executed but at least one signal FAILED | MUST write `DRYRUN_PENDING.md` listing each failing signal and the responsible step ID. Do NOT delete the file until a fresh dry-run passes. |

The Final Quality Checklist's dry-run box CANNOT be ticked while `DRYRUN_PENDING.md` exists in the skill directory. Any later edit to the skill that removes the file MUST be paired with a re-executed, passing dry-run for every original scenario.

For skills that ARE backed by `skill-prompter/scripts/tracker.py` (i.e., the skill has been touched by skill-prompter), the tracker's finalize gate is authoritative and `DRYRUN_PENDING.md` is unnecessary — tracker rejection of `finalize --status completed` plays the same role.

### Hand-off to skill-prompter

If the dry-run reveals that steps are getting skipped, that VERIFY gates are missing, or that wording is too vague for the simulator to follow, that is a **prompting compliance issue, not a structure issue**. Hand off to **skill-prompter** for step wording rewrite, then return for a fresh dry-run on the rewritten skill.

## Final Skill Quality Checklist

Before considering a skill complete (whether newly created or modified), verify every item below. Treat this as a hard gate, not a suggestion.

### Description and triggering

- [ ] `name` follows naming rules (lowercase, hyphens, max 64 chars, no reserved words)
- [ ] `name` + `description` wording passes the skill-prompter checklist in `~/.agents/skills/skill-prompter/references/description-rules.md` (name-first delta, length-by-delta, trigger keywords, post-cutoff proper nouns, boundary clauses)
- [ ] `description` is under 1024 chars
- [ ] **ENV manifest complete** — if the skill reads any env var, every one is declared under `metadata.env` (required/optional + purpose) and the VERIFY grep surfaces no undeclared var; no machine-local source var is listed anywhere (see "Metadata: ENV variable manifest")

### Structure

- [ ] SKILL.md body is under 500 lines (split into references if approaching the limit)
- [ ] All references are one level deep from SKILL.md (no nested chains)
- [ ] No extraneous files (README.md, CHANGELOG.md, etc.)
- [ ] No duplicated content between SKILL.md and references
- [ ] All paths use forward slashes

### Content quality

- [ ] No first or second person voice ("I", "you")
- [ ] Examples are concrete (real input/output, not abstract scenarios)
- [ ] Terminology is consistent throughout
- [ ] No time-sensitive information mixed with current guidance
- [ ] One default approach is clear; alternatives are narrow exceptions

### Scripts (if any)

- [ ] Scripts handle errors explicitly rather than punting to Claude
- [ ] Magic constants have justifying comments
- [ ] Scripts have been tested by actual execution
- [ ] SKILL.md clearly states whether each script should be EXECUTED or READ as reference

### Validation

- [ ] The skill has been tested on at least one real task end-to-end
- [ ] At least 3 example user requests that should trigger the skill have been verified
- [ ] The skill works with a fresh Claude instance (no hidden context dependencies)
- [ ] **Sanitization pass complete** — every LLM model ID in SKILL.md, scripts, and references is CURRENT, or the user explicitly declined the upgrade for that finding (see "Sanitization Pass" section above)
- [ ] **Dry-run verification passed** every signal, including black-box prompt hygiene and Sonnet/Kimi/GLM/frontier model coverage (see "Dry Run Verification" section above) — REQUIRED for any skill that was created, modified, merged, or split
- [ ] **No `DRYRUN_PENDING.md`** present in the skill directory (skill-manager-tracked skills) OR `tracker.py show` reports `Latest signals: PASS` for skill-prompter-tracked skills
