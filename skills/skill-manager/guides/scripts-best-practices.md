# Scripts Best Practices

This file expands on the script anti-patterns listed in SKILL.md. Read this before adding any script to a skill, or when refactoring existing skill scripts.

## Solve, Don't Punt

Scripts inside skills exist to handle problems deterministically. If a script fails or returns ambiguous output, Claude has to fall back to LLM-driven recovery — defeating the purpose of having the script.

**Rule:** Every error a script can encounter should be either resolved in the script itself or surfaced as a clear, actionable message that tells Claude exactly what to do next.

### Bad: silent crash on missing file

```python
def load_config(path):
    with open(path) as f:
        return json.load(f)
```

If `path` does not exist, this raises `FileNotFoundError` and Claude must guess how to recover.

### Good: handle the missing-file case in the script

```python
def load_config(path):
    """Load config from path, creating an empty config if missing.

    On first run, the config file may not exist yet. Creating an
    empty default lets the workflow continue without requiring Claude
    to write recovery logic.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        empty = {}
        with open(path, "w") as f:
            json.dump(empty, f)
        return empty
```

### Bad: ambiguous error message

```python
if not is_valid(data):
    raise ValueError("Invalid data")
```

Claude cannot tell what is invalid or how to fix it.

### Good: actionable error message

```python
if not is_valid(data):
    raise ValueError(
        f"Field 'email' missing from record {record_id}. "
        f"Required fields: email, name. "
        f"Re-run with --include-email or check the source CSV."
    )
```

## Self-Documenting Constants

Every numeric or string constant should explain itself. Future readers (Claude or human) cannot safely tune values they do not understand.

### Bad: unexplained magic numbers

```python
TIMEOUT = 47
MAX_RETRIES = 3
BATCH_SIZE = 128
RATE_LIMIT_SLEEP = 1.7
```

### Good: justified constants

```python
# OpenAI embedding endpoint typically responds in 5-15s; 47s leaves headroom
# for slow upstream connections without causing the workflow to stall.
REQUEST_TIMEOUT = 47

# Three retries empirically clears 99% of transient network errors;
# more retries delay legitimate failure detection.
MAX_RETRIES = 3

# OpenAI embedding endpoint accepts up to 2048 inputs per request.
# 128 keeps memory usage manageable for typical input sizes.
BATCH_SIZE = 128

# Provider rate limit is 60 req/min. 1.7s sleep between requests
# keeps us under the limit even with two concurrent workers.
RATE_LIMIT_SLEEP = 1.7
```

## Verifiable Intermediate Outputs

For complex multi-step operations, structure scripts as: **plan → validate plan → execute → verify**.

This pattern lets Claude catch errors before they cause damage and provides natural checkpoints for iteration.

### Example: PDF form filling

**Without intermediate output:**
```python
def fill_form(pdf_path, data):
    # Reads PDF, fills fields, writes output — all in one step
    ...
```

If anything goes wrong, Claude has to rerun the whole flow blind.

**With intermediate output:**
```python
def analyze_form(pdf_path) -> dict:
    """Step 1: Extract form structure into a plan."""
    # Returns {"fields": [{"name": "email", "type": "text", ...}]}
    ...

def validate_mapping(plan: dict, data: dict) -> list[str]:
    """Step 2: Validate that data maps cleanly to plan fields."""
    # Returns a list of issues; empty list = valid
    ...

def fill_form(pdf_path, plan, data) -> str:
    """Step 3: Execute the validated mapping."""
    ...

def verify_output(output_path, plan) -> bool:
    """Step 4: Verify the output PDF has all expected fields populated."""
    ...
```

The skill's workflow then becomes:

```markdown
1. Run `python scripts/analyze_form.py input.pdf > plan.json`
2. Edit `plan.json` to add user data
3. Run `python scripts/validate_mapping.py plan.json` — fix issues until empty
4. Run `python scripts/fill_form.py input.pdf plan.json output.pdf`
5. Run `python scripts/verify_output.py output.pdf plan.json` — must return True
```

Each step produces a verifiable artifact. Failures are localized, and Claude can resume from any checkpoint.

## Clarify EXECUTE vs. READ

Make it explicit in SKILL.md whether each script should be EXECUTED by Claude or READ as a reference.

**EXECUTE example:**
```markdown
## Rotate a PDF

Run the script with the input path and rotation angle:

```bash
python scripts/rotate_pdf.py input.pdf 90
```

This does not require reading the script.
```

**READ example:**
```markdown
## Custom rotation logic

For non-standard rotation (e.g., per-page rotation), see `scripts/rotate_pdf.py`
as a reference implementation. Adapt the rotation logic for the specific case.
```

Without this distinction, Claude may waste tokens reading executable scripts unnecessarily, or fail to read reference scripts that contain critical patterns.

## Test Scripts by Actual Execution

Every script in a skill must be tested by actually running it before the skill is considered complete. Untested scripts are a frequent source of skill failures.

**Minimum testing:**
- Run the script with realistic inputs
- Verify the output matches what SKILL.md claims it produces
- Test the documented error cases (missing files, bad input)

**For skills with many similar scripts:** test a representative sample (e.g., 1 of each variant) rather than all of them, but document which were tested.

## Required Packages

If a script requires non-standard packages, verify they are available in the target environment before relying on them.

**SKILL.md should state:**
```markdown
## Requirements

- Python 3.10+
- `pdfplumber` (pre-installed in Claude Code execution environment)
- `pillow` (pre-installed)
```

**Avoid:**
- Skills that quietly import packages not available in the target runtime
- Skills that recommend `pip install` of arbitrary packages without confirming the runtime allows it

## MCP Tool References in Scripts

When a script delegates to MCP tools, always use fully qualified names: `ServerName:tool_name`.

```markdown
Use the BigQuery:bigquery_schema tool to retrieve table schemas before query construction.
```

This avoids ambiguity when multiple MCP servers expose tools with similar names.
