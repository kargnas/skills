---
name: ui-buffet
description: Previews several UI/UX design concepts in the browser and builds the pick. Activates when the user asks for several UI/UX options or wants to think over or discuss a design before building.
---

# UI Buffet

Goal: Create eight UI/UX design concepts in a browser preview, let the user pick one, then build it.

## Context

Assume a global audience that is comfortable with gaming UI patterns unless the project's docs say otherwise, and state that assumption when they are silent. The requester has a broad idea for a feature, and the idea may not travel well to that audience, so the concepts must not be limited to gaming patterns.

Assume a mature codebase with years of history unless the project shows otherwise. Much of it is already built well, so never bolt a workaround onto a new place. Even after planning, find where the new logic belongs inside the existing code. For example, for email verification: find the existing sign-up logic AND the first user-facing verification point — you should find both.

## Steps

1. **Offer the buffet when it activated on its own.** Skip this step if the user named this skill (e.g. `/ui-buffet`, `$ui-buffet`, or "UI Buffet"). If the user has already said not to ask (earlier in the conversation or in their agent instructions), skip the question: run the buffet unless they also declined it. Otherwise:
   - Offer it once for this request in a short plain-text message, not a multiple-choice prompt. Say it takes about 5–10 minutes (a time estimate, not a token cost) and that you strongly recommend it, because it shows the industry and global standard approaches next to UIs the user would not have imagined.
   - Wait at most 5 minutes for the answer when your harness can wake you after a delay. Start the timer first, add to the offer that no answer within 5 minutes means you continue without the buffet, then end your turn. In Claude Code, run `sleep 300` as a background Bash command; the harness notifies you when it exits. Otherwise, leave out the timeout sentence, end your turn, and wait for the reply.
   - If the user answers first, stop the timer and follow their answer; ignore a timer that ends after they answered. If they decline, help with the request without this skill. If the timer ends with no answer, say in one line that you are continuing without the buffet, then help the same way.
   - Example with a timer (translate as needed): `UI Buffet can show eight design concepts in your browser before anything is built. It takes about 5–10 minutes, but I strongly recommend it: you see the industry and global standard approaches next to UIs you might never have imagined. Shall I run it? If I don't hear back in 5 minutes, I'll continue without it.`
2. **Explore project context.** First read the project's design rules and design tokens, for example a `DESIGN.md`, a design-system doc, a Tailwind theme, CSS custom properties, or a tokens JSON, plus any design guidance the project's agent instructions point to. If the project has none, say so, infer the tokens from its existing UI, and state what you assumed; do not create a design file unless the user asks. Then read the files, docs, and recent commits around the surface being changed so the concepts fit the existing flow.
3. **Clarify only if the capability itself is ambiguous.** One question per message, multiple choice when possible. Do not ask about scope, token cost, or whether to open the preview.
4. **Dispatch the clean-context subagent** for concept 8 (see `## The Fresh Eyes concept`) so it runs while you draft the other seven.
5. **Start the browser preview** with `scripts/start-server.sh --project-dir <project root> --open` and follow `references/visual-companion.md`. Reaching this step is the approval: never ask before opening it, never mention token cost, and prefer an HTML preview over ASCII.
6. **Create eight distinct UI/UX concepts** (override the count only if the user asks for a specific number). Match the preview's fidelity and presentation to the design question using `references/visual-companion.md`, and make every concept available for comparison before the user chooses. Give the screen a `<title>` that names what you generated so the browser tab shows it; `references/visual-companion.md` says where it goes. Label each concept card with a badge counting the clicks and inputs needed to finish the main task (e.g. `3 clicks · 1 input`):
   1. Your own recommendation
   2. The approach a market leader would most commonly use
   3. The standard approach global developers would use
   4. An unusual approach that departs from common patterns
   5. A devil's advocate approach
   6. The standard approach Korean developers or designers would use (but it doesn't mean the characters should be in Korean)
   7. The standard approach Chinese developers or designers would use (but it doesn't mean the characters should be in Chinese)
   8. The Fresh Eyes concept from the clean-context subagent (see `## The Fresh Eyes concept`).

   Draw every concept with the project's design tokens from step 2:
   - The tokens never change, however far a concept departs from the design rules: borders, fonts, corner radius, and every other token value stay exactly as the project defines them.
   - Take every visual value from the tokens. If a concept needs a value they leave out, such as a modal scrim, derive it from a token or from the project's existing UI and state that assumption; never invent a new look.
   - A concept may break a design rule only if its card names that rule (e.g. `Breaks: one primary button per screen`).
   - Concepts 4 and 5 ignore the project's design rules and keep only its tokens; their cards still name each rule they actually break.
7. **End your turn** with the URL and a one-line summary, and ask the user to click a concept and reply in the terminal.
8. **Once the user chooses**, read the click events, push the waiting screen, and carry the build through plan, audit, and verification without asking the user. Stop and ask before committing, pushing, or deleting anything the user did not request.
9. **Verify** by running the project's tests and lint and confirming the chosen concept renders in the app.

## The Fresh Eyes concept

This is the most important concept of this skill. The one concept must be produced by a clean-context subagent that never sees the user's conditions, feature list, or implementation choices. Because the user sometimes can't think outside of the plan, so need a super fresh eyes.

You send the subagent ONE goal sentence and nothing else, not even the project's design tokens; you apply them yourself when you draw its concept.

The clean context must be guaranteed explicitly; the default behavior differs by runtime. For example:

- Claude Code / OpenCode / Cursor: the `Task` (subagent) tool passes only the prompt you write, so put only the goal sentence in the prompt.
- Codex collaboration tools: call `spawn_agent` with `fork_turns: "none"`. The default (`"all"`) forks the entire conversation into the subagent and silently breaks the clean context.
- Any environment: launching a fresh CLI process also works, e.g. `claude -p "<goal sentence>"` or `codex exec "<goal sentence>"`.

How to build the goal sentence:

1. **Keep**: the product surface (e.g. "champion detail page", "duo finder", "sign-up flow") and the single user-facing capability being changed — expressed as a user need, not as a solution.
2. **Strip**: every numbered condition, repo name, data source, tier/threshold, caching rule, rollout scope, storage detail, and UI element.
3. **Strip solution words too**: if the user's request names a mechanism ("filter", "tab", "dropdown", "fallback", "cache"), that word must NOT appear in the goal sentence. Restate it as the underlying need. Copying the user's own feature phrasing verbatim defeats the entire purpose — the subagent must be free to invent a different mechanism.
4. The sentence must be specific enough that a stranger knows WHAT capability to design, but free enough that they design HOW from scratch.

Calibration examples:

- User request: `See those repos: user-api, recommendation-api. I want to: (1) change how to treat the temporary nickname (2) the user should be able to choose their nickname when they sign up (3 choices) (3) if registering fails, fall back to a random string nickname`
  - Right: `Change the way of creating a new nickname during the user signing up`
- User request: `Duo finder: (1) add voice-chat preference filter (2) show mic icon on profiles (3) persist in localStorage`
  - Wrong (too vague — lost the capability): `Improve the duo finder experience`
  - Wrong (leaked the user's solution): `Add a voice-chat preference filter to the duo finder`
  - Right: `Let duo-finder users express whether they want voice chat when matching`

## References

- Browser preview guide: `references/visual-companion.md`
- Server scripts: `scripts/start-server.sh`, `scripts/stop-server.sh`

## NEVER do for design
- NEVER suggest Metric Card, Stat Card, or KPI Card design. That's a useless & AI smell design.
- NEVER use an Eyebrow (a.k.a. Overline/Kicker): a small, letter-spaced, ALL-CAPS label above a heading (e.g. `SUBSCRIPTION NOTICE`). That's an AI smell design.
- NEVER use a left accent border callout (a box or quote with a colored vertical bar on the left edge). That's an AI smell design.
- NEVER use a hero followed by a 3-column feature card grid (icon + title + short description). That's an AI smell design.
