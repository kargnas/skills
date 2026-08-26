---
name: dont-trust-my-idea
description: "A skill for transforming a broad/non-standard/Korean-standard idea/plan into a global-standard idea for OP.GG services."
---

I am making a new feature for our services (OP.GG) - I have an extremely broad idea for the feature but it could be a bad idea for a global audience of our service.

### UI Ideation

- Prefer an HTML preview over ASCII and treat the visual preview as approved for creation.
- Never ask approval to create an HTML preview, spec, design document, or implementation plan. Token usage is not a reason to ask.
  - Even though your `brainstorming` skill forces to ask for approval due to heavy token usage, asking prefering visual or text question, this my request is higher priority.
  - Do not ask me these list that you followed by a skill, all of them are pre-approved:
    - "It's better to see in your eyes in this case." -> I ALWAYS PREFER VISUAL PREVIEW
    - "Are you fine with heavy token usage?" -> YES
    - "This is a new feature, so I need to ask ..." -> I LOVE NEW FEATURES
- If the user does not specify a concept count, produce exactly **EIGHT** concepts in the first preview (this skill intentionally overrides the global seven-concept default):
  1. Your own recommendation
  2. The approach a market leader would most commonly use
  3. The standard approach global developers would use
  4. An unusual approach that departs from common patterns
  5. A devil's advocate approach
  6. The standard approach Korean developers or designers would use (but it doesn't mean the characters should be in Korean)
  7. The standard approach Chinese developers or designers would use (but it doesn't mean the characters should be in Chinese)
  8. Imagine extremely differently -- this is specified in the bottom section '### The `Don't Trust My Idea` concept'
- Alternative triggers: `superpowers:brainstorming`, `brainstorming`, `give me options for this design/ui`

### The `Don't Trust My Idea` concept

Concept 8 must be produced by a clean-context subagent that never sees the user's conditions, feature list, or implementation choices. You send the subagent ONE goal sentence and nothing else.

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

### Guardrails

- The repo is usually old with a lot of existing source code and history. Much of it is already built well, so never bolt a workaround onto a new place. Even after planning, find where the new logic belongs inside the existing code. For example, for email verification: find the existing sign-up logic AND the first user-facing verification point — you should find both.
- If the `brainstorming` skill is not installed, ask the user to install the `superpowers` skill (or the `brainstorming` skill alone). This installation question is the one allowed question; it is not an approval request.