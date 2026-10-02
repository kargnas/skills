# Path B high-star off-topic noise on workflow-class queries

A **recurring, predictable** failure mode of Path B (`finder.py`) for *workflow / agent-behavior* topics: proactive agents, task discovery, action-item extraction, feedback triage, autonomous coding, standup-to-tasks.

## The signature

Path B's top rows are almost entirely viral skill-collection repos (tens of thousands of stars) that matched a generic query token by accident and then ranked up on polish-days + stars: web-research engines matching "research" / "discovery", trading agents matching "agent" / "task", personal coding-agent configs matching "setup", token-compression modes matching "agent", frameworks whose bundled `skills/` directory matched, and drive-by 1-commit stubs in awesome-lists.

Meanwhile the genuinely on-topic skills sit in **Path A** (`npx skills find`) with low installs and 1–2 polish-days — often a single SKILL inside a popular repo.

## Why it happens

Path B ranks by polish-days × star-weighting on repos whose **descriptions** matched a query token. Workflow topics use generic, high-frequency tokens ("agent", "task", "discovery", "proactive", "feedback") that appear in the description of every trending AI-skills mega-repo, so the candidate pool fills with viral collections and [S4] has to demote nearly all of them.

## Action rule

1. **For workflow / agent-behavior topics, treat Path A as the PRIMARY surface and Path B as supplementary.** This inverts the default "Path B is broader" assumption — broader here means noisier.
2. When Path B's top 5 are all ≥9K★ general-purpose mega-repos, **do not** spend [S4] budget inspecting each. Recognize the signature, note "Path B = keyword-noise for this class", and pivot to Path A's on-topic hits.
3. The real prior art for a niche workflow is often **one SKILL inside a heavily maintained repo**: the repo has 100K★ but that SKILL.md has 1–2 polish-days. Per-SKILL polish-days correctly demote it; do not read low per-file polish as low quality when the surrounding repo is maintained. The [S4b] depth check decides here, not polish-days.
4. **Trace copies to their origin.** Skill collections frequently carry verbatim copies of another author's skill (frontmatter `source:` field). Check `source:` and a `git/trees` listing of the original author's repo before recommending a derivative.

## Build vs borrow for user-specific workflows

When the user already runs a long-maintained local skill for the class, the right output is usually **"borrow 1–2 specific patterns, don't install"** — e.g. vertical-slice / tracer-bullet decomposition with human-in-the-loop vs. unattended tagging per item, or a `needs-info` state (ask the reporter back) that a pending/in-progress/done-only queue lacks.

Per skill-finder's own "stop searching and write your own" rule: when the niche is the user's personal workflow spanning their own chat / issue-tracker / repo mapping, the user-local skill wins; community skills are idea sources, not installs.
