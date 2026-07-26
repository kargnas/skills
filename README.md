# kargnas/skills

제가 [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Codex,
[OpenCode](https://opencode.ai)에서 사용하고 있는 스킬들 중 일부를 발췌하여 올렸습니다.

각 스킬은 표준 에이전트 스킬 구조인 `skills/<이름>/SKILL.md` 형태로 독립되어 있습니다.

## 전체 스킬 설치

[`npx skills`](https://github.com/vercel-labs/skills)로 모든 스킬을 한 번에 설치합니다.

```bash
npx -y skills add kargnas/skills --skill '*'
```

설치 대상을 직접 선택하려면 다음 명령을 사용합니다.

```bash
npx -y skills add kargnas/skills
```

전역 설치가 필요하면 원하는 명령 끝에 `--global`을 붙입니다.

## 개별 스킬 설치

### `ai-ready`

프로젝트를 분석해 `AGENTS.md`, 디버깅·테스트 환경, CI, 문서를 정비합니다.

```bash
npx -y skills add kargnas/skills --skill ai-ready
```

### `vscode-ready`

프로젝트 기술 스택에 맞는 VS Code/Cursor 실행, 디버그, 작업, 설정 파일을 구성합니다.

```bash
npx -y skills add kargnas/skills --skill vscode-ready
```

### `skill-manager`

스킬의 생성, 수정, 병합, 분리, 구조 정리, 외부 스킬 가져오기를 관리합니다.

```bash
npx -y skills add kargnas/skills --skill skill-manager
```

### `skill-prompter`

스킬 단계가 누락되지 않도록 RFC 2119 표현, 명시적 도구, 검증 절차, 이름과 설명을 다듬습니다.

```bash
npx -y skills add kargnas/skills --skill skill-prompter
```

### `humanizer-kill-gpt`

영어와 한국어 글에서 반복되는 GPT·LLM 특유의 문장 구조, 번역체, 과잉 설명을 제거합니다.

```bash
npx -y skills add kargnas/skills --skill humanizer-kill-gpt
```

### `git-lore`

Git trailer로 커밋의 결정 배경을 기록하고 조회하며, 프로젝트 또는 전역 에이전트 지침에 Lore 형식을 설정합니다.

```bash
npx -y skills add kargnas/skills --skill git-lore
```

## Claude Code 플러그인으로 설치

Claude Code에서는 이 저장소를 플러그인 마켓플레이스로 추가할 수도 있습니다.

```text
/plugin marketplace add kargnas/skills
```

```text
/plugin install kargnas-skills@kargnas/skills
```

## 스킬 목록

| 스킬 | 용도 |
| --- | --- |
| [`ai-ready`](skills/ai-ready/) | 프로젝트를 AI 에이전트가 작업하기 쉬운 구조로 정비 |
| [`vscode-ready`](skills/vscode-ready/) | VS Code/Cursor의 실행·디버그·작업 설정 생성 |
| [`skill-manager`](skills/skill-manager/) | 스킬 구조와 전체 생명주기 관리 |
| [`skill-prompter`](skills/skill-prompter/) | 스킬 지시문의 실행 준수율과 트리거 문구 개선 |
| [`humanizer-kill-gpt`](skills/humanizer-kill-gpt/) | 영어·한국어 글의 GPT·LLM 문체 흔적 제거 |
| [`git-lore`](skills/git-lore/) | Captures, queries, and configures decision context in native Git trailers |

## 라이선스

[PolyForm Noncommercial 1.0.0](LICENSE)에 따라 개인, 연구 및 기타 비상업적
용도로 무료 사용할 수 있습니다. 상업적 이용에는 저자의 별도 허가가 필요합니다.
