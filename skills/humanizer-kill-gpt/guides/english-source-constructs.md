# English source-constructs → Korean tells (Pass A reference)

The premise of this skill: when Korean reads like GPT wrote it, the cause is usually upstream — an English GPT-construct translated literally. Fix the English, and the Korean tell never forms. This file gives the full mapping with before/after, so Pass A replacements are grounded, not guesswork.

Use this when the text is English bound for Korean, or Korean you know was translated from English. For English that stays English, the same constructs are still GPT tells — just ignore the Korean column.

---

## 1. Copula avoidance → 번역체 역할 명사구

GPT avoids the plain "is" with "serves as / stands as / acts as / functions as / represents". Translated, this becomes `~역할을 합니다` / `~로 자리합니다` / `~를 나타냅니다`, which a Korean reader clocks instantly as 번역체.

- ❌ EN: "r/examplebrand serves as the official community."
- ❌ KO(직역): "r/examplebrand는 공식 커뮤니티의 역할을 합니다."
- ✅ EN: "r/examplebrand is our official community."
- ✅ KO: "r/examplebrand는 우리 공식 커뮤니티입니다."

## 2. Rule of three → GPT식 3개 명사 나열

GPT forces triads to sound complete. The triad survives translation as a stiff `A, B, C` 나열 where only one or two items carry weight.

- ❌ EN: "It's our name, our domain, and our trademark."
- ❌ KO(직역): "그것은 우리의 이름, 우리의 도메인, 그리고 우리의 상표입니다."
- ✅ EN: "We own the name and the examplebrand.example domain, and it's our trademark."
- ✅ KO: "'ExampleBrand'라는 이름과 examplebrand.example 도메인은 우리 거고, 상표도 우리 겁니다."

Keep the triad ONLY when all three items genuinely matter and the speaker would actually list three.

## 3. Colon apposition → 부연 패딩

"X: a Y that does Z" restates X with fake depth after a colon. Korean gets `~하는 Y로` / `즉 ~하는` padding that adds nothing.

- ❌ EN: "Run it as the official community: a moderated space where users discuss our products and send feedback."
- ❌ KO(직역): "공식 커뮤니티로 운영합니다. 즉 사용자들이 제품을 논하고 피드백을 보내는, 관리되는 공간으로서 말입니다."
- ✅ EN: "Run it ourselves as the official ExampleBrand community. Our users get a real place to talk about our products, and we'd actually moderate it."
- ✅ KO: 두 문장으로 쪼개서 평서로.

## 4. -ing tail clauses → 어색한 연결 어미

Bolt-on participles ("..., ensuring/highlighting/reflecting/underscoring X") add fake significance. Korean renders them as `~을 보장하며` / `~을 보여주며` / `~을 반영하며` mid-sentence connectors that feel machine-glued.

- ❌ EN: "We'll moderate it properly, ensuring a healthy community."
- ❌ KO(직역): "우리는 그것을 제대로 관리하여, 건강한 커뮤니티를 보장합니다."
- ✅ EN: "We'll moderate it properly so the community stays healthy."
- ✅ KO: "우리가 제대로 관리해서 커뮤니티를 건강하게 유지할 겁니다."

## 5. Hedging stack → 이중유보

"it could potentially be argued that it might..." stacks qualifiers. Korean becomes `~일 수도 있다고 볼 수도 있습니다` — a double hedge that reads as evasive AI prose.

- ❌ EN: "It might possibly have some effect on the outcome."
- ✅ EN: "It affects the outcome." (or, if truly uncertain, "It may affect the outcome.")
- ✅ KO: "결과에 영향을 줍니다." / 정말 불확실하면 "영향을 줄 수 있습니다." (한 번만 유보)

## 6. Negative parallelism → `~가 아니라 ~` / 꼬리 부정

"not just X, it's Y" and tail negations ("..., no guessing") are GPT contrast frames. Korean: `단순한 X가 아니라 Y입니다` and `~없이` tails that feel templated.

- ❌ EN: "It's not just an information site; it's a community."
- ✅ EN: "It's an information site, and we want a real community around it."
- ✅ KO: 긍정 절로 직접: "제품 정보 사이트이고, 그 주변에 진짜 커뮤니티를 두고 싶습니다."

## 7. Corporate softener → 군더더기 정중어

"whatever you need", "feel free to", "I'd be happy to", "at your convenience" are servile padding. Korean auto-inserts `부탁드립니다`, `혹시 괜찮으시다면`, `편하실 때` even where the original had none.

- ❌ EN: "We can provide whatever you need to verify ownership."
- ✅ EN: "We can verify ownership with the domain and trademark."
- ✅ KO: "도메인과 상표로 소유권을 증명할 수 있습니다."

Keep at most ONE polite marker in the whole message. Stack two and it reads as machine politeness.

## 8. Significance inflation → 과장 명사구

"marks a pivotal moment", "underscores its importance", "in today's evolving landscape", "a testament to". Korean: `중대한 전환점`, `~의 중요성을 보여주는`, `급변하는 환경 속에서`. Pure puffery in both languages.

- ❌ EN: "This marks a pivotal moment for the community."
- ✅ EN: "This gives the community a fresh start." (or cut entirely)

## 9. Em-dash overuse → 줄표 남발

GPT uses 3+ em dashes for "punchy" sales rhythm. Translated, Korean either keeps the dashes (남발) or inserts awkward pauses.

- ❌ EN: "The sub — banned for spam — was never ours — and we want it back."
- ✅ EN: "The sub was banned for spam. It was never ours, and we want it back."

## 10. Signposting → 본론 예고 연출

"Let's dive in", "Here's what you need to know", "Two ways this could go", "Without further ado". Korean: `자, 그럼`, `여기서 알아둘 점은`, `정리하자면 두 가지입니다`. Tutorial-script warm-up — just say the thing.

- ❌ EN: "So I'm asking for two things. Two ways this could go."
- ✅ EN: "I'm asking you to either reinstate r/examplebrand, or tell me how a brand owner claims the name."

---

## Pass A self-check loop

For every English line bound for Korean, after rewriting, ask: **"If I translate this literally right now, does a Korean tell from Pass B come back?"** If yes, the source construct isn't dead — rewrite again. Only when the literal Korean translation is already clean do you move to Pass B for the surface polish.
