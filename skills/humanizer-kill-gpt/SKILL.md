---
name: humanizer-kill-gpt
description: "Runs a cross-language cleanup for writing tells shared by large frontier LLMs, not only GPT: English source constructs that survive other language translation and language-surface translationese. Use only when the user asks to remove AI/GPT tells from text (de-GPT, GPT 티, AI 티, 번역체 GPT, 자폐 말투 — colloquial shorthand for rigid or over-complete model prose, not a claim about autism)."
---

# Humanizer: Kill GPT Tells

When starting, let the user know in one line that this skill is being used.

Remove recurring AI-writing fingerprints from English and Korean text. Despite the skill name, these patterns are not unique to GPT: large frontier language models commonly converge on the same over-complete, over-explained, overly balanced, and translation-shaped prose. The catalog keeps “GPT tell” as a familiar shorthand.

Some users call this style `자폐 말투`. Treat that phrase only as colloquial request vocabulary for rigid or socially miscalibrated model prose. MUST NOT equate the writing patterns with autism or use the phrase to characterize autistic people.

Most translated Korean tells start upstream: an English model-writing construct survives literal translation. This skill therefore uses two coupled passes.

| Text situation | Run |
|---|---|
| English draft | Pass A only |
| Korean draft written natively | Pass B only |
| Korean translated from English, or English that will be translated to Korean | Pass A first, then Pass B |

This skill targets cross-language patterns shared by large frontier models. A broader Korean-language cleanup workflow may cover additional punctuation, spacing, and lexical-distribution patterns that are outside this skill's scope.

When the user asks for generation-time speaking guidance instead of post-editing, read [references/generative-speaking-directive.md](references/generative-speaking-directive.md). Do not invert the catalog into a long prohibition list. Correct the three root behaviors instead: exhaustive coverage, over-helping, and formal-writing defaults.

## Procedure

### Input contract

Resolve `INPUT_TEXT` before [S1].

- `SKILL_DIR` MUST be the absolute directory containing this `SKILL.md`. If the host exposes only an installed alias, run `realpath "{installed-skill-path}"` and use the returned directory.
- Preserve the source line breaks and number them from 1 for findings output.
- Initialize `A_HITS=[]` and `B_HITS=[]` before route-specific scans.

| Input condition | Exact action |
|---|---|
| Text is present in the current conversation | Use that text verbatim as `INPUT_TEXT`; no external tool call is required |
| User supplies a file path | Run `sed -n '1,240p' "{path}"`; continue with `sed -n '241,480p'` and later ranges until EOF |
| No text or file is available | MUST ask one short question requesting the text, then wait |

### Step 1 [S1]: Select the execution route

**Tool**: Current-context language classification; no external command or model.

**Action**: MUST classify `INPUT_TEXT` with the decision table below. Use in-context language analysis; MUST NOT call an external rewriting model.

| Condition | Set `ROUTE` | Required path |
|---|---|---|
| English text that stays English | `A` | [S2] → [S3] → [S5]–[S9] |
| Korean text written natively | `B` | [S2] → [S4]–[S9] |
| Korean translated from English | `A+B` | [S2]–[S9] |
| English text intended for Korean readers or later translation | `A+B` | [S2]–[S9]; [S4] performs a prospective Korean-tell check |
| User requests generation-time persona or speaking guidance instead of post-editing | `DIRECTIVE` | [S2] → [S9] |

**VERIFY [S1]**: A working line exists in the form `Route: {A|B|A+B|DIRECTIVE}` and exactly one route is selected.

### Step 2 [S2]: Load the route references

**Tool**: The host's file-read tool; fallback to the shell command `sed`.

**Action**: MUST read the files selected below from `SKILL_DIR`, the directory containing this `SKILL.md`.

| `ROUTE` from [S1] | Exact file-read path |
|---|---|
| `A` | `{SKILL_DIR}/guides/english-source-constructs.md` |
| `B` | `{SKILL_DIR}/guides/natural-korean-patterns.md` |
| `A+B` | Read both guide paths above |
| `DIRECTIVE` | `{SKILL_DIR}/references/generative-speaking-directive.md` |

**IF BLOCKED**: If the host has no file-read tool, MUST run `sed -n '1,240p' "{exact-path}"` and continue with later 240-line ranges until EOF. If a guide still cannot be read, use the inline catalog below and disclose the missing guide in the final response.

**VERIFY [S2]**: Every file required by the selected route was read through EOF, or its missing-path fallback was recorded.

### Step 3 [S3]: Scan English source constructs

**Tool**: Current-context sentence comparison; no external rewriting model or web service.

**Action**: For `ROUTE=A` or `ROUTE=A+B`, MUST compare `INPUT_TEXT` against all 14 Pass A body rows exactly once, in table order. Use in-context text analysis; MUST NOT rewrite during this step. Store each match as `A_HITS` with fields `line`, `source span`, `pattern`, `reason`, and `Korean consequence`.

**VERIFY [S3]**: The working record states `A_ROWS_CHECKED=14`; `A_HITS` contains one record per Pass A match, including zero records when no match exists.

### Step 4 [S4]: Scan Korean-surface tells

**Tool**: Current-context sentence comparison; no external rewriting model or web service.

**Action**: For `ROUTE=B` or Korean `ROUTE=A+B`, MUST compare `INPUT_TEXT` against B1–B7 exactly once, section order first and row order second. For English `ROUTE=A+B`, MUST instead test whether a literal Korean translation of each sentence would regenerate any B1–B7 tell. Store matches as `B_HITS` with fields `line`, `pattern`, and `reason`.

**VERIFY [S4]**: `B_HITS` contains one record per applicable B1–B7 match, including zero records when no match exists; every applicable section was checked.

### Step 5 [S5]: Build the findings table

**Tool**: Current-context table synthesis; no external tool.

**Action**: MUST assign every hit `DEDUP_KEY={line}|{source span}`, merge `A_HITS` and `B_HITS` by that key, and produce the exact structure below. `source span` means the smallest contiguous substring that triggered one or more categories; MUST NOT widen it to the whole line. Overlapping or nested hits share one key, while non-overlapping hits on the same line keep separate keys. Combine every category and reason attached to the same key in one row. Each replacement MUST preserve facts, certainty, intensity, register, and intentional code-switching.

```text
| Original line | Pass/category | Why it reads as model-written | Proposed replacement |
```

For translation-bound text, the same row MUST name the English source construct and the Korean tell it would produce. A proposed replacement MUST be checked against the full catalog before inclusion.

**VERIFY [S5]**: The table row count equals the count of distinct `DEDUP_KEY` values; no key appears twice, and every row has a concrete replacement that introduces no cataloged tell.

### Step 6 [S6]: Apply the requested edit mode

**Tool**: Current-context text rewriting; no file-write tool unless the user explicitly requested an in-place file edit.

**Action**: MUST select one mode from the decision table and produce `EDITED_TEXT`.

| Condition | Required action |
|---|---|
| User explicitly requests no edits, review only, findings only, or diff only | Set `EDITED_TEXT=INPUT_TEXT`; preserve the findings table as the proposed diff |
| Findings exist and review-only mode was not requested | Apply every proposed replacement to a full rewritten text |
| No findings exist | Set `EDITED_TEXT=INPUT_TEXT` without cosmetic rewriting |

**VERIFY [S6]**: `EDITED_TEXT` exists, preserves the source meaning, and reflects exactly one mode from the table.

### Step 7 [S7]: Run the deterministic residual gate

**Tool**: Execute the bundled `scripts/residual_check.py` with `python3 "{SKILL_DIR}/scripts/residual_check.py"`. Replace `{SKILL_DIR}` with the absolute path resolved in the input contract. Reading the script is unnecessary but MUST NOT replace execution.

**Action**: MUST map the findings-table categories to the deterministic IDs below, deduplicate the IDs, and pipe the complete `EDITED_TEXT` from [S6] to the script. In review-only mode, pipe the proposed replacement text instead of unchanged source lines. The residual-check command MUST be the first and only shell invocation in this step. Keep the JSON result in the current response context; MUST NOT write `EDITED_TEXT`, script output, or intermediate findings to any file, including a temporary file.

| Findings category | Deterministic ID |
|---|---|
| Negative parallelism | `negative-parallelism` |
| Rule of three | `rule-of-three` |
| Copula avoidance | `copula-avoidance` |
| Fit assertion | `fit-assertion` |
| Significance inflation | `significance-inflation` |
| `-ing` tail clause | `ing-tail` |
| Corporate softener | `corporate-softener` |
| Signposting | `signposting` |

Set `CATEGORY_FLAGS` to one `--category {deterministic-id}` flag per unique mapped ID. If the findings contain none of these categories, set `CATEGORY_FLAGS=--category none`.

```bash
python3 "{SKILL_DIR}/scripts/residual_check.py" {CATEGORY_FLAGS} <<'EDITED_TEXT'
{complete EDITED_TEXT or proposed replacement text}
EDITED_TEXT
```

The script emits one JSON object and uses exit codes `0=pass`, `1=residual found`, `2=invalid invocation or input`.

| Script result | Required action |
|---|---|
| Exit `0`, JSON `status=pass` | Set `deterministic_remaining=0`; continue to [S8] |
| Exit `1`, JSON findings present | Rewrite only the reported spans, then repeat [S7] once |
| Second exit `1` | Set `deterministic_unresolved` to the reported findings; go directly to [S9] and disclose them |
| Exit `2` | Fix the invocation or input named in JSON, then repeat [S7] once |
| Second exit `2` | Go directly to [S9] and disclose that deterministic verification failed |

**IF BLOCKED**: If the direct `python3` command exits `127`, run the same command once with `python`. If that also exits `127`, go directly to [S9] and disclose that the deterministic gate was unavailable.

**VERIFY [S7]**: Before [S8], the residual-check command exits `0`; JSON has `status=pass` and `finding_count=0`; `checked_categories` exactly matches the unique mapped IDs, or is empty only when `--category none` was used; S7 used no `ls`, `stat`, `which`, or artifact-write call.

### Step 8 [S8]: Re-scan the full catalog

**Tool**: Current-context sentence comparison using the same catalogs loaded in [S2].

**Action**: MUST compare every proposed replacement first with the category that triggered its row, then repeat the applicable [S3] and [S4] comparison order against `EDITED_TEXT`. In review-only mode, scan the proposed replacement text. A synonym that retains the same structure MUST count as `same_category_remaining`.

| Re-scan result | Required action |
|---|---|
| `same_category_remaining=0` and no other avoidable tell remains | Continue to [S9] |
| A replacement retains its source category or introduces another tell | Rewrite only that replacement, then repeat [S7] → [S8] once |
| The repeated [S7] or [S8] still fails | Set `unresolved` to the remaining items and continue to [S9] without claiming a clean result |

**VERIFY [S8]**: The re-scan record lists `same_category_remaining`, `remaining`, `introduced`, and `unresolved`; a clean result requires the first three counts to equal `0`.

### Step 9 [S9]: Deliver the result

**Tool**: The host's final-response renderer; MUST NOT write an artifact unless the user requested one.

**Action**: MUST emit exactly one output shape from the decision table.

| Condition | Output shape |
|---|---|
| `ROUTE=DIRECTIVE` | Generation-time directive from the loaded reference, followed by one short rationale |
| No findings | `Route: {ROUTE}` followed by `GPT/frontier-model tells: none` |
| [S7] verifier unavailable or errored twice | Route line → findings table → proposed or edited text → verifier error; MUST NOT claim a clean re-scan |
| Review-only mode | Route line → findings table → proposed diff or replacement text → deterministic and full-catalog forecast |
| Applied mode | Route line → findings table → complete `EDITED_TEXT` → `Re-scan: deterministic_remaining=0, same_category_remaining=0, remaining={N}, introduced=0, unresolved={N}` |

**VERIFY [S9]**: The response contains the selected route and required artifacts. Post-editing routes include the actual deterministic plus full-catalog status without overstating success; `DIRECTIVE` omits scan status by design.

MUST NOT replace one model-writing tell with another. MUST preserve all existing functionality and the user's intended voice.

---

## Pass A: English source constructs

These English-side habits occur across large frontier LLMs and produce recognizable Korean translationese. Removing them in English is the cleanest fix. See [guides/english-source-constructs.md](guides/english-source-constructs.md) for detailed before-and-after examples.

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
| `열다`, `닫다`, `굴리다` for discussions or businesses | Overused physical metaphor | `시작하다`, `마무리하다`, `정리하다`, `다루다` |
| `두께`, `두텁다` for abstract data, relationships, or experience | Literal "depth/thickness" metaphor | Use `양`, `깊이`, or explain what accumulated |
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

The mandatory output contract is defined in [S5] and [S9]. MUST NOT substitute another format.
