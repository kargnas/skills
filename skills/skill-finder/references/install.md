# Installing a discovered skill — target-safe recipe

## One target, chosen by the user (MUST)

Before installing, ask the user for exactly ONE destination skills directory, `<skills-dir>` (for example `~/.claude/skills/`, `~/.agents/skills/`, `~/.config/opencode/skills/`, `~/.codex/skills/`, or an agent-specific category folder). Install only there.

MUST NOT run a blind `npx skills add <source> -g -y` against the real home unless the user explicitly asks for multi-agent fan-out: global fan-out installs through every agent-home convention at once, blurs the source of truth, and can overwrite local customizations. Do not create symlinks from one registry to another.

## Collision check (MUST, every target)

```bash
TARGET="<skills-dir>/<skill-name>"
test ! -e "$TARGET" || { echo "target exists: $TARGET"; exit 1; }
```

If the target exists, stop and ask whether the user wants an update, a rename, or a manual merge. Re-running an install over an existing directory overwrites local customizations.

## Marketplace package (`npx skills add`): stage first, copy one directory

Use a temporary `HOME` so `npx` can fetch and normalize the package without touching real agent homes. Marketplace rows are usually `owner/repo@skill-name`.

```bash
PACKAGE="<owner/repo>"
SKILL="<skill-name>"
STAGE="$(mktemp -d)"

HOME="$STAGE" npx --yes skills add "$PACKAGE" \
  --skill "$SKILL" \
  -g \
  --agent opencode \
  --copy \
  -y

test -f "$STAGE/.agents/skills/$SKILL/SKILL.md"

TARGET="<skills-dir>/$SKILL"
test ! -e "$TARGET" || { echo "target exists: $TARGET"; exit 1; }
mkdir -p "$(dirname "$TARGET")"
cp -R "$STAGE/.agents/skills/$SKILL" "$TARGET"
test -f "$TARGET/SKILL.md"
rm -rf "$STAGE"
```

If the staged path differs, inspect `find "$STAGE" -maxdepth 5 -name SKILL.md -print` and adjust the copy source before touching the real target.

**VERIFY:** `<skills-dir>/<skill-name>/SKILL.md` exists, its `name:` frontmatter matches the directory name, and no command created a second install location or a registry-to-registry symlink.

## Installing under a different name

When the user wants a skill installed under a different name (e.g. `refactoring-patterns` → `refactor`), use the new name as the target directory and update the `name:` frontmatter to match. Agents and skill indexes resolve by directory name; a mismatch produces phantom duplicates.

```bash
UPSTREAM_SKILL="refactoring-patterns"
INSTALL_NAME="refactor"
TARGET="<skills-dir>/$INSTALL_NAME"

cp -R "$STAGE/.agents/skills/$UPSTREAM_SKILL" "$TARGET"
sed -i '' "s/^name: $UPSTREAM_SKILL$/name: $INSTALL_NAME/" "$TARGET/SKILL.md"
```

**VERIFY:** `grep '^name:' "$TARGET/SKILL.md"` prints the new name.

## Raw GitHub repo (Path B result, not on skills.sh): git clone, strip `.git`

Path B (`finder.py`) surfaces repos that are NOT marketplace packages, so `npx skills add` does not apply:

```bash
SKILL="<skill-name>"
TARGET="<skills-dir>/$SKILL"
test ! -e "$TARGET" || { echo "EXISTS: $TARGET"; exit 1; }
STAGE="$(mktemp -d)"
git clone --depth 1 "https://github.com/<owner>/<repo>.git" "$STAGE/oc"
mkdir -p "$(dirname "$TARGET")"
cp -R "$STAGE/oc" "$TARGET"
rm -rf "$TARGET/.git"          # MUST: do not ship the upstream .git into the skill tree
rm -rf "$STAGE"
test -f "$TARGET/SKILL.md"
grep -m1 '^name:' "$TARGET/SKILL.md"   # confirm frontmatter name matches dir
```

**VERIFY:** `$TARGET/SKILL.md` exists, `name:` matches the directory, and no `.git` directory remains under `$TARGET`.

## Skills that ship executable scripts

1. **The `python3` on PATH is not necessarily the interpreter that has the deps.** Agent frameworks often put their own venv first on PATH, and a bare `pip3 install` can land in a different site-packages. Install the skill's dependencies into the interpreter you will actually run, and run the scripts with that interpreter (`"$PY" -m pip install -r requirements.txt && "$PY" <skill>/<script>.py`, or `uv run --with <deps> <script>.py`).
2. **System daemons and binaries are separate from pip deps.** A skill that needs a local service (a SOCKS proxy, a database) also needs the binary installed and started; verify the listening port before testing the skill.

Capture the fix, never "the scripts don't work".

## Grouping many skills under a category folder

A package that ships many skills (e.g. a 20-skill SEO suite) does not have to stay a flat list of sibling directories, but nest them under one category folder ONLY after confirming that your agent's loader discovers nested `SKILL.md` files (load one nested skill and check it resolves). Renaming a skill = rename the directory AND sync its `name:` frontmatter in the same step.

## Bundling several skills into one workflow

| Situation | Required action |
|---|---|
| Several skills should become one reusable workflow | Use `skill-manager` to design the umbrella or merge structure. |
| The bundled skill's steps need reliability hardening | Use `skill-prompter` after the structure is chosen. |
| The only plan is "install all skills and make them point at each other" | Reject that plan. Build one standard bundle or keep the skills separate. |

**VERIFY:** The final install plan has one owner skill or clearly separate skills, with no circular cross-references between copied community skills.
