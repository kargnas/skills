---
name: dont-trust-my-ui-idea
description: "A skill for transforming a broad/non-standard/Korean-standard idea/plan into a global-standard idea for OP.GG services. You must use `superpowers:brainstorming` or `brainstorming` skill together when using this skill."
---

Goal: Create multiple UI design concepts using the Visual Companion feature of `brainstorming` skill, and I choose one from the generated concepts.

## Context

I am making a new feature for our services (OP.GG) - I have an extremely broad idea for the feature but it could be a bad idea for a global audience of our service. Our users are mostly gamers, so they are already familiar with gaming-related UI patterns but don't be limited to the only gaming-related UI patterns.

Our repository is usually old with a lot of existing source code and years of history. Much of it is already built well, so never bolt a workaround onto a new place. Even after planning, find where the new logic belongs inside the existing code. For example, for email verification: find the existing sign-up logic AND the first user-facing verification point — you should find both.

## Steps

1. Use `superpowers:brainstorming` or `brainstorming` skill. Ask to install if it's not installed.
2. Create multiple concepts of UI mockups with Visual Companion in `brainstorming` skill.
  1. Using `dont-trust-my-ui-idea` means wanting to create the Visual Companion without any additional approval of `token-intensive`. Don't ask additional approval to avoid unnecessary interruptions.
  2. Propose eight approaches (override this default if the user wants to create only a specific number of approaches):
    1. Your own recommendation
    2. The approach a market leader would most commonly use
    3. The standard approach global developers would use
    4. An unusual approach that departs from common patterns
    5. A devil's advocate approach
    6. The standard approach Korean developers or designers would use (but it doesn't mean the characters should be in Korean)
    7. The standard approach Chinese developers or designers would use (but it doesn't mean the characters should be in Chinese)
    8. Imagine extremely differently -- this is specified in the bottom section `## The Don't Trust My Idea` concept.

## Working on the `brainstorming` skill

The skill has many guardrails to get approval from the user, but `dont-trust-my-ui-idea` is specifically designed for using Visual Companion feature of it, so you don't need to get approval for using that feature.

Two of its steps are explicitly overridden while this skill is active:

- Skip the just-in-time Visual Companion offer (the "own message + wait for the user's response" rule). Invoking `dont-trust-my-ui-idea` is the acceptance, so start the Visual Companion directly.
- The eight approaches in this skill replace `brainstorming`'s "Propose 2-3 approaches" step.

For examples:
- Prefer an HTML preview over ASCII and treat the visual preview as approved for creation.
- I know Visual Companion is token-intensive, and I approve it once I use `dont-trust-my-ui-idea`. So, never ask me like:
  - "It's better to see in your eyes in this case." -> I ALWAYS PREFER VISUAL PREVIEW in `dont-trust-my-ui-idea`
  - "Are you fine with heavy token usage?" -> YES
  - "This is a new feature, so I need to ask ..." -> I LOVE THIS NEW FEATURES

## The `Don't Trust My Idea` concept

This is the most important concept of this skill. The one concept must be produced by a clean-context subagent that never sees the user's conditions, feature list, or implementation choices. Because the user sometimes can't think outside of the plan, so need a super fresh eyes.

You send the subagent ONE goal sentence and nothing else.

The clean context must be guaranteed explicitly; the default behavior differs by runtime. For example:

- Claude Code / OpenCode / Cursor: the `Task` (subagent) tool passes only the prompt you write, so put only the goal sentence in the prompt.
- Codex collaboration tools: call `spawn_agent` with `fork_turns: "none"`. The default (`"all"`) forks the entire conversation into the subagent and silently breaks the clean context.
- Any environment: launching a fresh CLI process also works, e.g. `ag claude agp -p "<goal sentence>"` or `ag codex agp "<goal sentence>"`.

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
- Official repository of `superpowers` skills: https://github.com/obra/superpowers
