# Rewrite Patterns for 100% Step Compliance

## Pattern 1: Atomic Step Decomposition

**Problem**: Multi-action steps get partially executed.

**Before**:
```markdown
### Step 3: Setup and Configure
Read the config file, validate all fields, update the database connection string, and restart the service.
```

**After**:
```markdown
### Step 3 [S3]: Read Configuration File
**Action**: Run `cat config.yaml` to read the current configuration.
**VERIFY**: File contents are displayed. File is valid YAML.
**IF BLOCKED**: File not found → Run `cp config.example.yaml config.yaml` first.

### Step 4 [S4]: Validate Configuration Fields
**Action**: Run `python3 scripts/validate_config.py config.yaml`
**VERIFY**: Script prints "all fields valid" with exit code 0.
**IF BLOCKED**: Validation fails → Print the specific error and fix only that field.

### Step 5 [S5]: Update Database Connection
**Action**: Edit `config.yaml` line containing `db_host:` to set value from environment variable `$DB_HOST`.
**VERIFY**: Run `grep db_host config.yaml` shows the updated value.

### Step 6 [S6]: Restart Service
**Action**: Run `systemctl restart myservice`
**VERIFY**: Run `systemctl status myservice` shows "active (running)".
**IF BLOCKED**: Service fails to start → Read logs with `journalctl -u myservice -n 20`
```

---

## Pattern 2: Decision Table Replacement

**Problem**: Nested if/else logic confuses weaker models.

**Before**:
```markdown
If the response is a 200, parse the JSON body. If it's a 404, check if the resource was recently deleted. If it's a 429, wait and retry. If it's a 500, log the error and alert the team. Otherwise, treat it as an unknown error.
```

**After**:
```markdown
| HTTP Status | Action | Next Step |
|-------------|--------|-----------|
| 200 | Parse JSON body with `jq '.'` | Go to [S8] |
| 404 | Run `python3 scripts/check_deleted.py {id}` | Go to [S10] |
| 429 | Wait 60 seconds, then retry [S7] (max 3 retries) | Retry [S7] |
| 500 | Log error: `echo "500 error" >> errors.log` | Go to [S12] |
| Other | Log: `echo "Unknown: {status}" >> errors.log` | Go to [S12] |
```

---

## Pattern 3: Subagent Delegation

**Problem**: Token-heavy steps exhaust context and cause later steps to be skipped.

**Before**:
```markdown
### Step 5: Analyze All Source Files
Read every .py file in the src/ directory. For each file, identify all function definitions, their parameters, return types, and docstrings. Create a comprehensive API map.
```

**After**:
```markdown
### Step 5 [S5]: Delegate Source Analysis to Subagent

**DELEGATE TO SUBAGENT**:
  Task: "Read all .py files in src/. For each file, list: filename, function name, parameters, return type. Output as a markdown table."
  Input: Directory path `src/`
  Expected output: Markdown table with columns: File, Function, Params, Returns
  Max tokens: 4000

**Action**: Launch subagent with the task above.
**VERIFY**: Subagent returns a markdown table with at least 1 row.
**IF BLOCKED**: Subagent times out → Manually read the 3 most important files instead.
```

---

## Pattern 4: Checkpoint Accumulation

**Problem**: Steps produce outputs that later steps need, but weaker models lose track.

**Solution**: Use a named checkpoint file to accumulate state.

```markdown
### Step 3 [S3]: Save Checkpoint
**Action**: Write the following to `checkpoint.json`:
```bash
python3 -c "
import json
data = {'step': 'S3', 'api_key_valid': True, 'db_connected': True, 'files_found': 12}
json.dump(data, open('checkpoint.json', 'w'), indent=2)
print('checkpoint saved')
"
```
**VERIFY**: `cat checkpoint.json` shows the saved data.

### Step 7 [S7]: Read Checkpoint Before Processing
**Action**: Run `python3 -c "import json; d=json.load(open('checkpoint.json')); print(f'Files: {d[\"files_found\"]}')"` 
**VERIFY**: Prints the expected count from [S3].
```

---

## Pattern 5: Explicit Output Templates

**Problem**: Weaker models produce inconsistent output formats.

**Before**:
```markdown
### Step 8: Generate Report
Create a report summarizing the findings.
```

**After**:
```markdown
### Step 8 [S8]: Generate Report

**Action**: Write a report to `report.md` using this EXACT template:

```markdown
# {Skill Name} Improvement Report

## Summary
- **Status**: {completed|in_progress|blocked}
- **Steps improved**: {N} of {total}
- **Date**: {YYYY-MM-DD}

## Changes Made
1. {First change description}
2. {Second change description}

## Metrics
| Metric | Before | After |
|--------|--------|-------|
| Atomic steps | {N}/{total} | {N}/{total} |
| VERIFY gates | {N}/{total} | {N}/{total} |
```

**VERIFY**: `head -5 report.md` shows the header and status line.
```

---

## Pattern 6: Explicit Looping

**Problem**: "For each X, do Y" is often executed for only the first X.

**Before**:
```markdown
### Step 4: Process Each Model
For each model in the registry, run the experiment and record results.
```

**After**:
```markdown
### Step 4 [S4]: Get Pending Model List
**Action**: Run `python3 scripts/cli.py model list --status pending --format oneline`
**VERIFY**: Output shows at least 1 model ID. If 0 → skip to [S8].

### Step 5 [S5]: Process FIRST Pending Model Only
**Action**: Take the FIRST model ID from [S4] output. Run:
```bash
python3 scripts/cli.py run start --model "{first_model_id}"
```
**VERIFY**: Script prints "run started" with a run ID.

**IMPORTANT**: Process exactly 1 model per execution cycle. Do NOT loop through all models.
```
