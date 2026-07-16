# Skill Anti-Patterns: Detailed Examples

This file expands on the anti-patterns listed in SKILL.md with concrete bad/good examples. Read this when reviewing an existing skill or when unsure whether a pattern is acceptable.

## Description Anti-Patterns

Name + description wording — including its anti-patterns (first/second person voice, name restatement, vague trigger surface, flat length, post-cutoff proper nouns, "when to use" in the body) — is owned by **skill-prompter**. See `~/.agents/skills/skill-prompter/references/description-rules.md` for the full rules with bad/good examples.

## Structure Anti-Patterns

### Anti-Pattern: Windows-style paths

Forward slashes work on every platform; backslashes break on macOS and Linux.

**Bad:**
```markdown
Run `scripts\rotate_pdf.py` to rotate the document.
```

**Good:**
```markdown
Run `scripts/rotate_pdf.py` to rotate the document.
```

### Anti-Pattern: Deeply nested references

Claude reads references on-demand. Deep chains cause partial reads — Claude sees a link to one file, follows it, sees another link, and may stop without reaching the actual content.

**Bad:**
```
SKILL.md → advanced.md → patterns.md → details.md → examples.md
```

**Good:**
```
SKILL.md
├── guides/patterns.md (linked directly from SKILL.md)
├── guides/details.md  (linked directly from SKILL.md)
└── guides/examples.md (linked directly from SKILL.md)
```

All curated typed-folder files should link directly from SKILL.md.

### Anti-Pattern: Time-sensitive information mixed with current guidance

Time-sensitive content rots quickly and confuses Claude when the date drifts.

**Bad:**
```markdown
## API Usage

If you are calling this before August 2025, use the v1 endpoint. After August 2025, use v2 with the new auth headers.
```

**Good:**
```markdown
## API Usage

Use the v2 endpoint with the new auth headers.

## Legacy patterns (rarely needed)

The v1 endpoint is deprecated. If a project explicitly pins to v1, see [guides/legacy-v1.md](legacy-v1.md).
```

### Anti-Pattern: Extraneous documentation files

Skills are not for human onboarding. They contain only what an AI agent needs to do the job.

**Files to avoid creating in a skill directory:**
- `README.md`
- `INSTALLATION_GUIDE.md`
- `QUICK_REFERENCE.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `TODO.md`

If history or installation notes are needed, keep them outside the skill directory entirely.

### Anti-Pattern: Duplicating content between SKILL.md and references

Information should live in exactly one place. Duplication creates drift — the two copies disagree after the first edit.

**Bad** (SKILL.md):
```markdown
## API Schema

The users table has columns: id, email, created_at, deleted_at.
The orders table has columns: id, user_id, total, status.
[full schema repeated]

For more schema details, see api-references/schema.md.
```

**Good** (SKILL.md):
```markdown
## API Schema

For all table schemas and column definitions, see [api-references/schema.md](api-references/schema.md).
```

## Content Anti-Patterns

### Anti-Pattern: Too many options

Listing every alternative paralyzes Claude. Pick one default and document narrow exceptions.

**Bad:**
```markdown
For PDF text extraction, you can use pypdf, or pdfplumber, or PyMuPDF, or pdfminer.six, or Tika, or Apache PDFBox, or...
```

**Good:**
```markdown
Use pdfplumber for PDF text extraction. For scanned PDFs requiring OCR, use pdf2image + tesseract instead.
```

### Anti-Pattern: Verbose explanations of common knowledge

Trust that Claude already knows what a PDF is, what a database does, or what HTTP means. Only document the non-obvious specifics of your skill.

**Bad:**
```markdown
PDF (Portable Document Format) files are a common file format developed by Adobe Systems in 1993. They contain text, images, vector graphics, fonts, and other content. PDFs are widely used because...
```

**Good:**
```markdown
## Extract PDF text

Use pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

### Anti-Pattern: Abstract examples

Concrete input/output beats every abstract description.

**Bad:**
```markdown
The script accepts a query and returns results based on the query parameters and the configured filters.
```

**Good:**
```markdown
**Example:**
```bash
$ python scripts/query_users.py --created-after 2024-01-01 --status active
{"count": 1247, "users": [{"id": 1, "email": "alice@example.com"}, ...]}
```

## Script Anti-Patterns

### Anti-Pattern: Punting errors back to Claude

Scripts should solve problems deterministically. Failing back to Claude defeats the purpose of having a script.

**Bad:**
```python
def load_config(path):
    with open(path) as f:
        return json.load(f)
# Crashes with FileNotFoundError if path missing — Claude has to handle it
```

**Good:**
```python
def load_config(path):
    """Load config from path, creating an empty config if the file is missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        # First run: create empty config so the workflow can proceed.
        empty = {}
        with open(path, "w") as f:
            json.dump(empty, f)
        return empty
```

### Anti-Pattern: Magic constants without justification

Numeric constants without comments are unreadable in six months and impossible for Claude to safely tune.

**Bad:**
```python
TIMEOUT = 47
MAX_RETRIES = 3
BATCH_SIZE = 128
```

**Good:**
```python
# HTTP requests typically complete within 30s; 47s leaves headroom for slow connections.
REQUEST_TIMEOUT = 47

# Three retries balances reliability against latency for transient network errors.
MAX_RETRIES = 3

# OpenAI embedding endpoint accepts up to 2048 inputs per request; 128 keeps memory usage low.
BATCH_SIZE = 128
```

## Cross-Agent / Multi-Host Anti-Patterns

### Anti-Pattern: Putting agent-specific category folders inside the shared skills dir

The shared `~/.agents/skills/` directory is consumed by multiple agents (Claude Code, Codex, OpenCode, others). The Skill anatomy is `<skill-name>/SKILL.md` — a flat layout. Category folders like `research/`, `creative/`, `productivity/` are HOST-specific organization, not part of the skill itself.

**Bad** (forces every agent to know your category layout):
```
~/.agents/skills/research/paper-search/SKILL.md
~/.agents/skills/creative/art-studio/SKILL.md
```

**Good** (flat shared store; each host symlinks into its own category convention):
```
~/.agents/skills/paper-search/SKILL.md
~/.agents/skills/art-studio/SKILL.md

# Then each category-based host symlinks into its own layout:
<agent-home>/skills/research/paper-search → ~/.agents/skills/paper-search
<agent-home>/skills/creative/art-studio → ~/.agents/skills/art-studio
```

### Anti-Pattern: Blind `mv` into a directory that already contains a same-named skill

When promoting a local skill into the shared `~/.agents/skills/` store, ALWAYS check for an existing skill with the same name first. A blind `mv my-skill ~/.agents/skills/` will silently nest `my-skill` INSIDE the existing `my-skill/` directory, producing `~/.agents/skills/my-skill/my-skill/SKILL.md` — broken on every host.

**Bad:**
```bash
mv ./paper-search ~/.agents/skills/   # silently nested if paper-search/ already exists
```

**Good:**
```bash
# 1. Check for collision
ls ~/.agents/skills/ | grep -i paper-search

# 2. If collision: read the existing SKILL.md and decide:
#    - DIFFERENT purpose → rename your skill (e.g. arxiv-paper-search)
#    - OVERLAPPING purpose → absorb the existing one's best ideas, then replace
#    - DUPLICATE → drop yours, patch theirs

# 3. Only mv after the decision is explicit
mv ./paper-search ~/.agents/skills/paper-search
```

### Anti-Pattern: Hardcoding host-specific paths inside a shared SKILL.md

A skill living under `~/.agents/skills/` will be loaded by multiple hosts via symlink. SKILL.md should reference its OWN canonical path (`~/.agents/skills/<name>/scripts/...`), not any host's symlink path (`~/.claude/skills/...`, `~/.codex/skills/...`). Same applies to cache directories — pick a single shared location.

**Bad** (works only when loaded via one host's symlink):
```markdown
python3 <agent-home>/skills/research/paper-search/scripts/finder.py
```

**Good** (works from any host):
```markdown
python3 ~/.agents/skills/paper-search/scripts/finder.py
```
