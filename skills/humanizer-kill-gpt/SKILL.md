---
name: humanizer-kill-gpt
description: Removes GPT-specific writing tells from English and Korean text, including English source constructs that survive translation and Korean-surface translationese. Use when de-GPTing a draft, polishing English bound for Korean readers, or removing robotic contrast frames, hedging, forced lists, and translated AI phrasing.
---

# Humanizer: Kill GPT Tells

Remove GPT/AI fingerprints from English and Korean text. Most GPT-like Korean translated from English starts upstream: an English GPT construct survives literal translation. This skill therefore uses two coupled passes.

| Text situation | Run |
|---|---|
| English draft | Pass A only |
| Korean draft written natively | Pass B only |
| Korean translated from English, or English that will be translated to Korean | Pass A first, then Pass B |

This skill targets GPT-specific cross-language patterns. A broader Korean-language cleanup workflow may cover additional punctuation, spacing, and lexical-distribution patterns that are outside this skill's scope.

When the user asks for generation-time speaking guidance instead of post-editing, read [references/generative-speaking-directive.md](references/generative-speaking-directive.md). Do not invert the catalog into a long prohibition list. Correct the three root behaviors instead: exhaustive coverage, over-helping, and formal-writing defaults.

## Procedure

1. **Detect language and origin.** Choose the applicable passes from the table above. If the user says the Korean came from English, or the English will be translated, Pass A is mandatory.
   - An English draft paired with a Korean-targeted request is not a mismatch. Treat it as English intended for Korean readers and remove the source constructs that would become Korean translationese.
2. **Scan** the text against every pattern in the applicable passes.
3. **Flag** each hit with the exact line, category, and reason it reads as a GPT tell. For translated text, name both the English source construct and the Korean tell it produces.
4. **Propose a natural replacement.** Preserve meaning and change only the GPT-shaped wording. Read [guides/natural-korean-patterns.md](guides/natural-korean-patterns.md) for Korean endings, connectors, and politeness, and [guides/english-source-constructs.md](guides/english-source-constructs.md) for English-to-Korean mappings.
5. **Apply** the fixes, or present a diff when the user requests review first.
6. **Re-scan** after editing. Confirm that no GPT tell survived and no replacement introduced another one. For translation-bound text, verify that the rewritten English will not regenerate a Korean tell.

Never replace one GPT tell with another. Check each proposed replacement against the full catalog before using it.

---

## Pass A: English source constructs

These English-side habits produce recognizable Korean translationese. Removing them in English is the cleanest fix. See [guides/english-source-constructs.md](guides/english-source-constructs.md) for detailed before-and-after examples.

Negative parallelism is the highest-priority pattern to rewrite.

| English GPT construct | Why it is a tell | Korean tell it becomes | Fix in English |
|---|---|---|---|
| **Negative parallelism**: "not just X, it's Y" or a "no guessing" tail | Overused contrast frame | `~가 아니라 ...`, `~하기보다`, or a `~없이` tail | State the positive clause directly and give the reason |
| **Copula avoidance**: "serves as / stands as / acts as / functions as a X" | Inflated alternative to plain "is" | `~역할을 합니다`, `~로 자리합니다` | Use "is" or "is the" |
| **Fit assertion**: "X is a natural fit for Y" | Asserts suitability through another copula-avoidance frame | `~에 자연스럽게 맞습니다`, `~가 잘 맞습니다` | Use "X fits Y" or "use X for Y" |
| **Rule of three**: "fast, simple, and reliable" | Forced completeness through a triad | GPT-style three-noun list | Keep only the one or two items that matter |
| **Colon apposition**: "the official community: a moderated place where..." | Restates the noun with artificial depth | `~하는 공간으로` padding | Split it into plain sentences |
| **-ing tail clauses**: "..., ensuring/highlighting/reflecting X" | Adds bolt-on significance | `~을 보장하며`, `~을 반영하며` | Make it a separate sentence or delete it |
| **Hedging stack**: "it could potentially be argued that it might..." | Stacks unnecessary qualification | `~일 수도 있다고 볼 수도 있습니다` | Hedge once, or state it directly |
| **Corporate softener**: "whatever you need", "feel free to", "I'd be happy to" | Servile padding | `부탁드립니다`, `혹시 괜찮으시다면` padding | Delete it; keep at most one polite marker |
| **Significance inflation**: "marks a pivotal moment", "underscores its importance" | Inflates an ordinary fact | `중대한 전환점`, `~의 중요성을 보여주는` | State the fact or cut the sentence |
| **Em-dash overuse** | Creates synthetic sales-copy rhythm | Repeated dashes or awkward translated pauses | Use commas, periods, or parentheses |
| **Signposting**: "Let's dive in", "Here's what you need to know" | Tutorial-script warm-up | `자, 그럼 ~`, `여기서 알아둘 점은` | Start with the substance |
| **Exhaustive if-else branching** | Covers every branch instead of committing to the likely one | `~했다면 ..., 안 했다면 ...` | Choose one branch or ask one short question |
| **Contraction avoidance** in casual or spoken English | Sounds robotic in small talk and voice output | English-only tell | Use don't, didn't, and can't |
| **Small-talk-to-coaching conversion** | Turns a greeting into unsolicited advice | Advice appended to a simple greeting | Reply briefly, match the register, and return the question |

**Pass A self-check:** Translate each rewritten English line literally. If a Pass B tell comes back, rewrite the English again.

---

## Pass B: Korean-surface GPT tells

Run this pass on Korean text, whether native or translated. The tables identify what to remove; [guides/natural-korean-patterns.md](guides/natural-korean-patterns.md) provides natural alternatives and rhythm.

### B1. Non-native Korean

These machine-translated structures sound immediately unnatural to native speakers.

| GPT expression | Problem | Natural direction |
|---|---|---|
| `<English word> 계열 <English word>` | Mixes English terms through the vague noun `계열` | Translate the relationship or use `~ 종류의` |
| `A 없음은 B를 proxy로 봤습` | Non-native nominalization and case marking | `A가 없어서 B를 대신 봤음` |
| `흐름 안에서` | Habitual insertion in an unnatural position | Delete it, or use `~ 과정에서` / `~ 중에` |
| `...은 받지 않겠습니다` | Needlessly hard and imperious | Use `~는 어렵습니다` or `~는 수용하기 힘듭니다` as context requires |
| `다른 분들 평가서에 보면...` | Non-native `-서에 보면` construction | `다른 분들의 평가를 보면` |

### B2. Grammatically valid but GPT-shaped Korean

| GPT expression | Problem | Natural direction |
|---|---|---|
| Repeated topic-marker forms such as `...에서는`, `...보다는`, `...으로는` | Translationese topic marking | Rebuild the sentence and remove unnecessary `는` forms |
| `...으로는 ...지만, ...지는 않았습니다` | Double reservation | Assert once or hedge once |
| `-로 봤습니다` | Overused judgment phrase | `~라고 판단했습니다`, `~로 생각했습니다`, or a direct assertion |
| `~가 자연스럽게/잘/딱 맞습니다` as a suitability claim | Literal "is a fit" construction | `~가 제격입니다`, `~면 됩니다`, `~로 가면 됩니다` |
| `...정도로 넓혀도 N건 수준이라` | Stacks `정도` and `수준` | State the number directly |
| `넓히다`, `좁히다` for abstract scope | Overused metaphor | `늘리다/줄이다`, `확대하다/축소하다` |
| `열다`, `닫다` for discussions or businesses | Overused physical metaphor | `시작하다`, `마무리하다`, `정리하다` |
| `두께` for abstract data, relationships, or experience | Literal "depth/thickness" metaphor | Use `양`, `깊이`, or explain what accumulated |
| `척추`, `등뼈` for a business or system | Literal body metaphor | `근간`, `뼈대`, `토대`, `기반` |
| `-지는 않았습니다` | Unnecessary reservation | End with a direct assertion |
| `...쪽이었고` | Padding through `쪽` | Use `~였고` |
| `~한 거 맞음` as self-confirmation | The speaker re-confirms their own statement | Delete the confirmation tail |
| `니 말이 맞음`, `말씀이 맞습니다`, `말씀하신 대로` as an opener | Reflexive agreement and flattery | Start with the evidence or the answer |
| `하나로 묶다` | Overused abstraction | `합치다`, `한데 모으다` |
| `...로 봅니다`, `...로 보지 않고` | Repetitive translated judgment frame | Use natural spoken Korean or a direct assertion |
| `그 위에서`, `... 위에서` with an abstract object | Physical positioning attached to an abstraction | `그걸 바탕으로`, `그 다음에` |
| `다투다` in neutral competition contexts | Overused dramatic verb | `겨루다`, `경쟁하다`, `부딪히다` |
| `그 지점은` | Habitual abstraction | `그 부분은` |
| `-하고자 합니다` | Stiff intention form | `제안드립니다`, `말씀드립니다` |
| `~기가 쉽지 않은 상황입니다`, `~상황입니다` | Adds a padded situation noun | State the difficulty with a verb |
| `~점도 충분히 이해하고 있습니다` | Scripted empathy padding | Use brief, context-specific empathy only when needed |
| `가능한 범위 안에서` | Stock phrase | `가능한 선에서`, `가능한 선까지` |
| `박하게` with estimates or offers | Often sounds forced | Use `낮게` or explain the decision |
| Six or more nouns in a list | Exhaustive cataloging | Keep three or four representative items |
| `~게 아니라 ~니다` | Negative parallelism preserved in Korean | Split it or state the positive claim directly |
| `토대/기반 위에 세우다`, `그 위에서` | Literal construction metaphor | `~를 바탕으로`, `~에서 출발하다` |
| `레이어` for abstract capabilities | Literal "layer" metaphor | Explain the capability, use `기능`, or delete it |
| `해자` in ordinary business prose | Literal "moat" jargon | Explain the barrier directly |
| `묶이다`, `~에 묶입니다` as "bound to" | Literal English mapping | `~를 벗어나지 못하다`, `~ 안에서만 돌아가다` |
| A full root-cause analysis in response to a one-line status question | Over-explanation is itself an AI tell | Answer `지금은 정상`, `재현 안 됨`; explain only when asked |

### B3. Corporate softeners inserted without need

Delete ceremonial padding that was absent from the source:

- `부탁드립니다`, `양해 부탁드립니다`
- `미리 감사합니다`, `감사합니다 (미리)`
- `말씀 드리고 싶었습니다`
- `혹시 괜찮으시다면`

Keep one polite marker only when the context genuinely requires it.

### B4. Hedging adverbs

Check `아마`, `혹시`, `어쩌면`, `다소`, and `충분히`. Remove them when the source makes a direct claim. Preserve one only when the uncertainty is real.

### B5. AI-slop and robotic markers

| Marker | Problem | Alternative |
|---|---|---|
| `·` | Machine-generated visual texture | Comma, line break, or `와/과` |
| Honorifics applied to objects | Incorrect elevation | Use the ordinary verb form |
| `-십시오` | Mechanical register | `-세요` |
| Sentence-final `-니까` in a question | Awkward ending | `-나요?` when appropriate |
| `당신` | Translated second person | Use a name, handle, or omit the pronoun |
| `-합시다` | Mechanical suggestion | `-하면 좋겠습니다`, `-해주세요`, `어떻게 생각하세요?` |
| `-라고 봅니다` | Translationese judgment | `-라고 생각합니다` or a direct assertion |
| `-쪽`, `-쪽으로`, `-쪽입니다` | Padding | Delete it or use `~로` |

### B6. Artificial narrative structure

These patterns are structurally theatrical even when each word is grammatical.

- **Narrative verbs for plain facts:** Replace unnecessary `들어갑니다`, `나갑니다`, and `넘어갑니다` with `시작합니다`, `추가됩니다`, or a direct state. Example: `신제품은 7월입니다`, `그다음은 이 제품군 밖입니다`.
- **Physical motion assigned to abstract actors:** Replace `저희 도구는 작업 안에서 움직입니다` with the actual meaning, such as `저희 도구는 작업 중에 실시간으로 함께 작동합니다`.
- **Dramatic subject reveal:** Put the subject before the judgment. Replace `그중 제일 잘한 건 인정합니다. 제품 X는...` with `그중 제품 X는 솔직히 잘 만들었습니다`.
- **Dropped object particles:** Restore `을/를` when headline-style omission makes the sentence sound generated: `보이스 라인업을 준비 중입니다`.

### B7. Defensive echoing

Do not delay a new answer by repeating the user's premise or defending the previous answer.

- **Echoing the user:** Delete openers such as `말씀하신 대로 ~라면` and answer directly.
- **Re-explaining the previous answer:** Remove the defense and address the new question. If context acknowledgment is necessary, keep it to one short clause.

## Preservation rules

Do not damage natural text through over-correction:

- Preserve intentional loanwords and code-switching such as `프로세스`, `톤`, and `내로남불`.
- Preserve genuine rhetorical questions such as `내가 왜 이해해줘야 함?`.
- Preserve the source's certainty and intensity. Do not add corporate softeners.
- Preserve a consistent nonstandard spacing pattern or voice when it is intentional.
- In English, preserve an intentional single em dash, real terms of art, and the author's own asserted strength.

## Output format

Present findings in a table before applying them:

```text
| Original line | Pass/category | Why it reads as GPT | Replacement |
```

For translation-bound text, include the English source construct and the Korean tell in the same row. After editing, show the complete revised text and report the re-scan result in one line. If there are no hits, say `GPT tells: none`.
