# deckgen

양식을 고르고 값만 채워 PPT(.pptx)를 만드는 도구입니다. 같은 기능을 세 가지로 씁니다.

- **명령줄(CLI)**: JSON 스펙 파일을 읽어 pptx 를 만듭니다. AI 가 쓰기 좋게 스키마·예제·검증 명령이 있습니다.
- **웹 화면(GUI)**: 로컬에서 양식을 고르고 입력란을 채운 뒤 내려받습니다.
- **파이썬 라이브러리**: `deckgen.spec`, `deckgen.render` 를 직접 호출할 수 있습니다.

## 설치

파이썬 3.12 이상이 필요합니다.

```
pipenv install            # 개발 환경
pip install .             # 또는 일반 설치 (deckgen 명령이 생깁니다)
```

설치하지 않고 `python -m deckgen ...` 으로도 실행됩니다.

## 빠른 시작

```
deckgen layouts                       # 양식 목록
deckgen example > deck.json           # 모든 양식을 한 장씩 담은 예제
deckgen build deck.json -o deck.pptx  # pptx 생성
deckgen gui                           # 웹 화면 (http://127.0.0.1:8765)
```

실제 예제는 `examples/gitea-repair.json`(15장짜리 조치 가이드)입니다.

```
deckgen build examples/gitea-repair.json -o guide.pptx --strict
```

## 스펙 형식

```json
{
  "theme": { "font": "Malgun Gothic", "palette": { "accent": "0F7B8A" } },
  "slides": [
    { "layout": "title", "title": "제목", "subtitle": "부제" },
    { "layout": "step", "badge": "1", "title": "STEP 1  재시작", "lead": "서비스를 다시 시작합니다.",
      "code": ["Restart-Service <서비스이름>"], "ok": "정상이면 끝.", "ng": "아니면 다음 단계로." }
  ]
}
```

- `theme` 은 선택입니다. 적은 항목만 바뀌고 나머지는 기본값입니다.
- 슬라이드마다 `layout` 에 양식 이름을 쓰고, 그 양식의 필드를 채웁니다.
- 모든 양식에 선택 필드 `notes`(발표자 노트)가 있습니다.
- 코드 줄 안의 `<바꿀곳>` 은 붉은 굵은 글씨로 표시됩니다. 본문 문구에서도 같습니다(보조 문구 등).
- 알 수 없는 키, 빠진 필수 값, 길이 초과는 모두 오류입니다. 한 번에 전부 알려 줍니다.

## 양식

| 이름 | 용도 |
|---|---|
| `title` | 표지 (어두운 배경) |
| `intro_cards` | 번호 카드 2~4장 + 보조 문구 |
| `flow` | 단계 상자를 화살표로 잇는 순서도 |
| `step` | 단계 하나: 안내, 명령 상자, 성공/실패 상자 |
| `procedure` | 화면에서 누르는 절차(번호 목록), 성공/실패 상자 |
| `checklist` | 확인 항목 카드(두 열) + 주의 문구 |
| `numbered_list` | 번호 카드 목록(두 열), 경고 문구 |
| `prohibitions` | 하지 말 것 카드(두 열) |
| `closing` | 마무리 (어두운 배경, 번호 항목, 하단 명령) |

필드 이름, 제약, 예제는 `deckgen schema [양식]` 과 `deckgen example [양식]` 이 알려 줍니다.

## CLI 명령

| 명령 | 설명 |
|---|---|
| `deckgen layouts [--json]` | 양식 목록 |
| `deckgen schema [양식]` | 필드 스키마(JSON): 타입, 필수 여부, 글자 수·항목 수 제한, 선택지 |
| `deckgen example [양식]` | 예제 스펙(JSON). 양식을 생략하면 모든 양식을 담은 덱 |
| `deckgen validate 스펙 [--strict] [--json]` | 검증과 그리기 경고 확인 (파일을 만들지 않음) |
| `deckgen build 스펙 [-o 파일] [--strict] [--json]` | pptx 생성. 스펙 경로 `-` 는 표준입력 |
| `deckgen gui [--port 8765] [--no-open]` | 웹 화면 |

종료 코드: `0` 성공, `1` 스펙 오류 또는 `--strict` 에서 경고 발생, `2` 파일 읽기 실패 등 사용 오류.
오류와 경고는 표준 오류(stderr)로 나옵니다. `--json` 이면 `build` 는 `{"output", "slides", "warnings"}` 를 표준 출력에 냅니다.

### 경고

그리기 단계에서 글이 상자를 넘칠 것 같거나, 코드 줄이 길어 줄바꿈되거나, 본문이 성공/실패 상자와 겹치면 경고가 나옵니다.
글자 폭은 렌더링 없이 근사한 값이라 실제와 조금 다를 수 있습니다. `--strict` 를 쓰면 경고가 있을 때 파일을 만들지 않습니다.

## AI 에게 쓰게 하기

AI 에이전트는 이 순서로 쓰면 됩니다.

1. `deckgen schema` 를 읽어 양식과 제약을 파악합니다.
2. 필요한 양식의 `deckgen example <양식>` 을 보고 스펙 JSON 을 작성합니다.
3. `deckgen validate spec.json --json` 으로 오류와 경고를 확인하고 고칩니다.
4. `deckgen build spec.json -o out.pptx --strict` 로 만듭니다.

스펙은 표준입력으로도 받습니다: `cat spec.json | deckgen build - -o out.pptx`.

## 웹 화면

`deckgen gui` 는 `127.0.0.1` 에만 열립니다. 왼쪽에서 슬라이드를 고르거나 추가·복제·이동·삭제하고, 오른쪽에서 양식과 값을 채웁니다.
입력할 때마다 서버가 검증해서 아래에 오류와 경고를 보여 줍니다. 색과 글꼴은 "색과 글꼴", 스펙 전체는 "JSON 직접 편집"에서 바꿉니다.
"PPT 만들기" 가 pptx 를 내려받게 합니다. JSON 저장·열기로 작업을 이어 갈 수 있습니다.

## 개발

```
pipenv run python -m unittest discover -s tests -t .
```

구조:

- `deckgen/fields.py` 필드 종류(검증, 스키마 설명, 예제를 한곳에서 정의)
- `deckgen/layouts/` 양식. `Layout` 을 상속해 필드와 그리는 방법을 정의하고 `layouts/__init__.py` 에 등록
- `deckgen/painter.py` 도형·글 그리기 도구
- `deckgen/metrics.py` 글자 폭 추정
- `deckgen/spec.py`, `deckgen/render.py` 스펙 해석과 pptx 생성
- `deckgen/cli.py`, `deckgen/gui.py`, `deckgen/web/index.html`

새 양식은 `Layout` 하위 클래스를 만들고 `_ALL` 에 추가하면 CLI 스키마와 웹 화면에 자동으로 나타납니다.

## 라이선스

`LICENSE` 를 따릅니다. MIT-0 에 가까운 허용 라이선스로, 사용·수정·배포·판매가 자유롭고 출처표시나 고지문 포함 의무가 없습니다.
조건은 하나입니다. 원본의 출처를 속이지 말 것(원저자라고 주장하지 말 것). 보증은 없습니다.
표준 SPDX 식별자가 없는 맞춤 라이선스입니다.

## 알아 둘 점

- 글꼴 기본값은 `Malgun Gothic`(Windows 기본)입니다. 다른 글꼴은 `theme.font` 로 바꿉니다.
- 화면 미리보기는 없습니다. 만든 pptx 를 PowerPoint 등에서 열어 확인하세요.
