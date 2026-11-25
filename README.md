# AI Commit & PR Generator

Git 변경 사항(`git status`, `git diff`)을 AI API에 전달해서 **커밋 메시지**와 **Pull Request 제목/본문 초안**을 자동으로 만들어 주는 Python CLI 도구입니다.

- 커밋/PR 생성은 **초안 텍스트를 터미널에 출력**하는 것까지만 합니다. (`git push`, GitHub PR 자동 생성은 하지 않습니다.)
- 생성된 결과는 최종 정답이 아니므로 **반드시 검토 후 적용**하세요.

## 주요 기능

- `commit`: 커밋 제목 1줄 + 핵심 변경 불릿 본문 생성
- `pr`: PR 제목 1줄 + `Why` / `What` / `How to Test` 본문 생성
- 출력 검증/후처리: 커밋 제목 50자 권장(최대 72자), PR 제목 최대 80자, PR 섹션/불릿 확인
- `--safe-mode`: API Key·이메일 등 민감정보 마스킹 + diff 분량 제한(최대 10개 파일, 200줄)
- `--model`, `--temperature`, `--max-tokens` 옵션으로 API 파라미터 변경

## 요구 사항

- Python 3.10 이상
- Git
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com)에서 발급)
- 외부 패키지 설치 불필요 (Python 기본 라이브러리만 사용)

## 설치

```bash
git clone https://github.com/eldbsop/CodeExplainer.git
cd CodeExplainer
python3 -m venv .venv
source .venv/bin/activate
```

## 환경변수(API Key) 설정

API Key는 코드에 넣지 않고 **환경변수 `AI_API_KEY`** 로만 설정합니다.

```bash
export AI_API_KEY="YOUR_KEY"
```

터미널을 닫아도 유지하려면 `~/.zshrc`(macOS 기본 셸) 맨 아래에 위 줄을 추가하고 `source ~/.zshrc`를 실행하세요.

> API Key를 코드, README, 커밋에 절대 포함하지 마세요.

## 사용법

Git 저장소의 **프로젝트 루트 디렉토리**에서 실행합니다.

```bash
# 커밋 메시지 생성
python main.py commit

# PR 제목/본문 생성
python main.py pr

# 민감정보 마스킹 + 분량 제한 후 전송
python main.py commit --safe-mode

# 파라미터 변경
python main.py commit --model gemini-3.1-flash-lite --temperature 0.2 --max-tokens 800
```

### 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--model` | `gemini-3.1-flash-lite` | 사용할 모델 |
| `--temperature` | `0.3` | 0에 가까울수록 일관적, 1에 가까울수록 다양한 결과 |
| `--max-tokens` | `1000` | 응답 최대 토큰 수 (너무 작으면 답이 중간에 끊김) |
| `--safe-mode` | 꺼짐 | 민감정보 마스킹 + diff 일부만 전송 |

## 출력 예시

### 커밋 메시지

```text
[INFO] Git status 수집 완료: 5개 파일 변경 감지
[INFO] Git diff 수집 완료: 136줄
[INFO] AI API 요청 중... (호출 횟수: 1회)
[DONE] 커밋 메시지 생성 완료

--- Commit Message ---
feat: 커밋 및 PR 생성 로직 고도화 및 안전 모드 추가

- main.py: AI 프롬프트 분리 및 커밋/PR 생성 흐름 개선
- safety.py: 민감정보 마스킹 및 diff 분량 제한 기능 구현
- formatter.py: AI 응답 파싱 및 경고 메시지 출력 기능 추가
----------------------
```

### PR 제목/본문

```text
--- PR Title ---
feat: AI 커밋 및 PR 생성 기능 고도화 및 안전 모드 추가

--- PR Body ---
## Why
- 구조화된 프롬프트와 응답 포맷팅으로 더 신뢰성 있는 결과가 필요했습니다.
- AI 전송 시 민감 정보 노출을 막기 위한 안전 장치가 필요했습니다.

## What
- prompts.py, formatter.py, safety.py 모듈을 추가했습니다.
- --safe-mode 옵션으로 민감정보 마스킹 및 diff 분량 제한을 구현했습니다.

## How to Test
- python main.py commit --safe-mode 를 실행해 마스킹 건수가 출력되는지 확인합니다.
- python main.py pr 를 실행해 Why/What/How to Test 구조를 확인합니다.
----------------
```

### 오류 예시

```text
[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
## 예) export AI_API_KEY="YOUR_KEY"
```

```text
[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.
```

## 동작 방식

1. `git status`, `git diff` 실행 결과를 수집합니다.
2. (`--safe-mode`) 민감정보를 마스킹하고 분량을 제한합니다.
3. 역할/형식/금지 사항이 담긴 프롬프트와 함께 AI API를 **1회** 호출합니다.
4. 응답에서 마크다운·군더더기를 제거하고 길이/형식 규칙을 검증합니다.
5. 구분선으로 나뉜 결과를 터미널에 출력합니다.

## 주의사항

### 민감정보
`git diff`에는 API Key, 비밀번호, 개인정보가 포함될 수 있고, 이 내용은 **외부 AI 서버로 전송**됩니다.
- 민감한 변경이 있을 때는 `--safe-mode`를 사용하세요.
- 마스킹은 일부 패턴(API Key 형태, 이메일, `password=` 등)만 처리하므로 완벽하지 않습니다. 회사 코드나 비공개 코드는 전송 전에 직접 확인하세요.
- 무료 API 티어는 입력 내용이 모델 개선에 사용될 수 있습니다.

### 비용 및 요청 횟수
- `commit`/`pr` 명령은 1회 실행당 AI API를 **1회만** 호출하며, 호출 횟수를 로그로 출력합니다.
- 무료 한도를 넘으면 429, 서버가 붐비면 503 오류가 날 수 있습니다. 잠시 후 다시 실행하세요.
- 모델 이름은 자주 바뀝니다. 404 오류가 나면 `--model`로 다른 모델을 지정하세요.

## 프로젝트 구조

```text
├── main.py        # CLI 진입점 (commit / pr 명령)
├── git_utils.py   # git status / diff 수집
├── ai_client.py   # AI API 호출 (REST, 오류 처리)
├── prompts.py     # 커밋/PR 프롬프트
├── formatter.py   # 출력 검증 및 후처리
└── safety.py      # safe-mode (마스킹, 분량 제한)

