# skill-prompter

약한 LLM이 실행해도 모든 step을 100% 따르도록 AI 에이전트 스킬의 step wording을 다시 작성합니다.

> **`skill-improver`에서 이름이 바뀌었습니다.** 이 스킬은 프롬프팅 컴플라이언스를 담당합니다. 디렉토리 구조, 통합, 분리, 모듈 재구성 같은 구조적 변경은 `skill-manager`가 담당합니다.

> **참고**: 아래 "진화 과정" 섹션에서 `skill-improver`라고 언급되는 부분은 이전 이름을 그대로 유지한 historical 기록입니다. 현재 절차(dry-run 포함 10 phase)는 [SKILL.md](SKILL.md)에 정의되어 있습니다.

## Quick Start

```
사용자: "skills/my-skill/SKILL.md 스킬 개선해줘"
```

이게 끝. 봇이 읽고, 분석하고, 재작성하고, 자체 감사하고, 추적까지 합니다.

---

## 27% → 100%: 실제 테스트

196줄짜리 `competitor-website-audit` 스킬. DNS 조회, Playwright 스크린샷, 가격 추출, 리포트 생성까지 15단계.

```
📄 Before: 1개 파일, 196줄, 15 steps
   VERIFY 게이트:    0개
   폴백(escape):    0개
   서브에이전트 작업: 0개
   결정 테이블:      0개
   Step ID:         없음
```

| 모델 | Before | After |
|------|--------|-------|
| MiniMax M2.7 | ❌ 27% (4/15) | ✅ **100%** (11/11) |
| GLM-5-Turbo | ❌ 33% (5/15) | ✅ **100%** (16/16) |
| Haiku 4.5 | ❌ 40% (6/15) | ✅ **100%** (16/16) |
| Opus 4.6 | ⚠️ 67% (~10/15) | — (재테스트 안 함) |

```
📄 After: 1개 파일, 437줄, 16 steps
   VERIFY 게이트:    17개  (0 → 17)
   폴백(escape):    17개  (0 → 17)
   서브에이전트 작업:  4개  (0 → 4)
   결정 테이블:      64행  (0 → 64)
   Step ID:         [S1]-[S16]
```

---

## 봇 대화

```
🤖 봇: 스킬 읽는 중... 15 step 발견.
   각 step 리스크 분석 중.

📊 분석 결과:
   14/15 step → HIGH 리스크
    1/15 step → MEDIUM 리스크
    0/15 step → LOW 리스크

🤖 봇: 재작성 중...
   (step ID, 정확한 CLI 명령어, VERIFY 게이트,
    IF BLOCKED 폴백, 결정 테이블, 서브에이전트 위임 추가)

✅ 봇: 자체 감사 통과. 개선된 SKILL.md 작성 완료.
```

현재까지 9개 스킬이 `improvements.json`에 개선 및 추적됨.

---

## 진화 과정: 2번의 Iteration으로 100% 달성

### 📚 Phase 1: 리서치

중국 개발자 커뮤니티에서 MiniMax M2.7 프롬프팅 리서치 문서 5개 (~90KB) 수집. 샘플 스킬 3개 (5KB–29KB) 연구. 핵심 발견:

- `MUST`/`SHALL` 키워드가 일반 언어 대비 준수율 2배
- Atomic step 분해가 step 따르기에서 가장 큰 단일 요인
- Few-shot 예시는 위험 — 모델이 패턴을 배우는 게 아니라 답을 외움 (→ Rule 10)

### 🔨 Phase 2: 빌드

```
📄 SKILL.md               — 277줄, 10개 규칙, 10개 Phase
📄 tracker.py             — JSON 기반 영속 추적 CLI
📄 rewrite-patterns.md    — 6개 재작성 패턴 + 예시
📄 compliance-checklist.md — 필수/조건부/안티패턴 체크
📄 테스트 스킬 (15 steps)   — 일부러 복잡하게 만든 감사 스킬
```

### 🟡 Phase 3: 첫 테스트 — 모델이 과도하게 분해

약한 모델 3개가 skill-improver를 완벽히 따름 (10/10 Phase). 하지만 타겟 스킬을 과도하게 분해:

```
🤖 MiniMax (~3분): → 15 steps → 15/15 ✅
🤖 GLM (~5분):     → 28 steps → 27/28 ⚠️  (S28에서 멈춤)
🤖 Haiku (~4분):   → 40 steps → ~15/40 ❌  (타임아웃)
```

문제: skill-improver는 완벽히 따랐지만 타겟을 과분해함.

### 🔧 Phase 4: 데이터 기반 수정

```diff
+ Rule 11: Step Count Budget
+ "총 20 steps를 초과하면 안 됨(MUST NOT)."
+ 이유: 40 steps → 모델이 끝까지 가기 전에 컨텍스트 소진.

  Rule 5: Subagent Delegation
+ 모든 위임에 timeout fallback 필수.
+ "IF TIMEOUT: 60초 내 미반환 → {인라인 폴백}"
```

### 🟢 Phase 5: Round 2 — 전원 100%

```
🤖 MiniMax → 11 steps (기존 15, -27%)
🤖 GLM     → 16 steps (기존 28, -43%)
🤖 Haiku   → 16 steps (기존 40, -60%)
```

| 모델 | Steps | 소요시간 | 결과 |
|------|-------|---------|------|
| MiniMax M2.7 | 11/11 | ~5분 | ✅ **100%** |
| GLM-5-Turbo | 16/16 | ~6분 | ✅ **100%** |
| Haiku 4.5 | 16/16 | ~4분 | ✅ **100%** |

GLM의 서브에이전트 폴백 실전 작동:
```
| S11 | Core Web Vitals | ✅ PASS | API 사용 불가, fallback 적용 |
```

**3/3 모델, 100%, 2번의 iteration만에 달성.**

---

## Before / After

**Before** (사람이 쓴 원본):
```markdown
### Step 3: DNS and SSL Analysis
For each competitor domain, run DNS lookups and SSL certificate checks.
Use dig to get A records, MX records, and NS records. Use openssl to check
SSL certificate expiry. Also check if the site uses CDN.
```

**After** (봇이 개선):
```markdown
### Step 3 [S3]: Perform DNS Lookup

**Action**: state.json의 각 domain에 대해 MUST 실행:
  dig +short A {domain} > audit_output/data/{domain}_dns_a.txt
  dig +short MX {domain} > audit_output/data/{domain}_dns_mx.txt

**VERIFY**: `cat audit_output/data/{domain}_dns.json`이 유효한 JSON.
**IF BLOCKED**: `dig` 사용 불가 → `nslookup {domain}`으로 대체.
```

---

## 11가지 규칙

| # | 규칙 | 방지하는 문제 |
|---|------|-------------|
| 1 | Atomic Steps | "A하고 B해라"를 한 step에 |
| 2 | Explicit Tool Naming | 어떻게 하는지 안 알려줌 |
| 3 | RFC 2119 Keywords | "선택적으로..." 모호함 |
| 4 | VERIFY Gates | step 성공 여부 확인 불가 |
| 5 | Subagent Delegation | 무거운 step (+ timeout fallback) |
| 6 | Decision Tables | if/else 산문으로 인한 혼란 |
| 7 | Progressive Context Loading | 거대한 참조 문서 인라인 |
| 8 | Step IDs | step 간 교차 참조 불가 |
| 9 | Escape Hatches | 도구 실패 = 워크플로우 중단 |
| 10 | No Answer Keys | 테스트 답 누출 |
| 11 | Step Count Budget | step 너무 많으면 약한 LLM 컨텍스트 소진 |

Rule 1–10은 사전 설계. **Rule 11은 테스트 중 발견** — 96%에서 100%로 올린 결정적 규칙.

---

## 파일 구조

```
skill-prompter/
├── SKILL.md                     — 10개 Phase (dry-run 포함), 11개 규칙
├── scripts/
│   └── tracker.py               — 개선 추적 Python CLI
├── references/
│   ├── compliance-checklist.md  — step별 감사 체크리스트 (필수 6 + 조건부 6)
│   └── rewrite-patterns.md      — 6개 atomic 재작성 패턴
├── data/
│   └── improvements.json        — 영속 추적 데이터
└── tests/
    └── test-complex-15step-skill-IMPROVED.md — 개선 예시 스킬
```
