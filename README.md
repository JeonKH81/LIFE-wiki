# LIFE wiki

**이메일에서 업무의 맥락을 복원하는 스킬.** 같은 업무가 여러 메일 대화에 흩어져 있어도 하나의 카드에서 경과와 근거를 읽을 수 있게 합니다.

**English:** An email-based work-context wiki skill. Reconstruct coherent work across threads, preserve evidence and chronology, and keep uncertain relationships and unknown outcomes visible.

저장소 이름은 `Life-wiki`, 화면 이름은 **LIFE wiki**, 스킬 이름은 `life-wiki`입니다. LIFE는 표시 이름이며 별도의 약어 뜻을 정의하지 않습니다. 읽기 지침과 로컬 정리 도구를 제공하며, 이메일 수집 서비스나 자동 분류 모델은 포함하지 않습니다.

## 무엇을 만드는가

- 메일 한 통이 아니라 **하나의 업무**를 카드로 만듭니다. 제목이 같아도 일이 다르면 나누고, 대화가 달라도 같은 일이라는 근거가 있으면 연결합니다.
- 제안·요청·승인·실행을 구분합니다. 승인은 완료가 아닙니다. 결과 근거가 없으면 미확인으로 남깁니다.
- 원문 발췌·출처 식별자·원문 시각을 보존합니다. “실행했다고 보고함”과 “독립적으로 확인함”도 구분합니다.
- 중복 가져오기와 오래된 판본의 덮어쓰기를 막고, 합치기·나누기·일반 수정의 되돌리기에 이전 상태를 남깁니다.
- 출처·카드·관계의 같은 내용을 이력에서 재사용하여 중복 저장을 줄입니다. 전체 이력을 매번 확인하므로 반복 수정의 누적 시간 문제까지 없애지는 않습니다.
- 사용자 지시로 민감한 내용을 현재 상태와 이력에서 지우는 `redact`를 제공합니다. 삭제 범위는 연결된 다른 출처와 카드로 넓어질 수 있으며 되돌릴 수 없습니다.
- 읽기 쉬운 Markdown 카드, JSON 기록, 검색·관계·시간순 기록을 보여주는 정적 화면을 제공합니다.

## Codex에서 설치

지원 범위는 **Codex의 로컬 스킬 폴더 방식**입니다. 사용할 프로젝트 안에서 `.agents/skills/life-wiki`가 아직 없는지 확인한 뒤, 이 저장소의 `skills/life-wiki` 폴더 전체를 그 위치로 복사하세요. 기존 스킬이 있다면 비교 후 교체하세요. 전역 설정 변경은 필요 없습니다.

```text
your-project/
  .agents/skills/life-wiki/
    SKILL.md
    agents/
    references/
    schemas/
    scripts/
    assets/
```

Codex에서 `$life-wiki`를 선택해 다음처럼 요청합니다.

> 제공한 이메일을 업무별 카드로 정리해 주세요. 다른 대화로 이어진 업무도 살피고, 완료 근거가 없으면 결과를 미확인으로 남겨 주세요. 결과는 지정한 비공개 폴더에 저장해 주세요.

이 방식은 [OpenAI 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)의 로컬 폴더 발견 방식에 따릅니다. 설치 후 목록에 보이지 않으면 Codex를 다시 시작하세요. Claude Code 설치·실사용 호환성과 ChatGPT 플러그인 마켓 배포는 **미검증**이며, 이 패키지는 해당 설치 기능을 제공하지 않습니다.

## 가상 예제 실행

Python 3.10 이상이 필요합니다. 직접 설치하는 의존성은 `jsonschema` 하나이며, 날짜 확인에 선택적 추가 패키지는 필요하지 않습니다. 별도 가상환경 사용을 권장합니다. 도구 실행에는 Node.js가 필요하지 않지만 **전체 검사와 화면 검사에는 Node.js도 필요합니다.** 화면 자체에는 외부 의존성이 없습니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
node tests/viewer.test.js
.venv/bin/python skills/life-wiki/scripts/wiki.py validate examples/expected/wiki.json
.venv/bin/python skills/life-wiki/scripts/wiki.py render examples/expected/wiki.json --out /tmp/life-wiki-demo
```

자동 검사 설정은 Python 3.10·3.12·3.14와 Node.js 22를 지정합니다. 설정한 환경과 실제 실행 결과는 [검증 요약](docs/VERIFICATION.md)에 구분해 적었습니다.

`/tmp/life-wiki-demo/index.html`을 열고 “가상 예제 보기”를 누르거나 내보낸 `wiki.json`을 선택하는 방식입니다. 파일 선택은 그 화면 안에서만 읽으며 서버에 보내지 않습니다. 다만 **실제 브라우저의 `file://` 환경에서 CSP가 허용하는지에 대한 검증은 완료하지 않았습니다.** Chrome·Firefox 등에서 로컬 파일로 여는 동작이 확인됐다고 보증하지 않습니다. 화면의 로컬 파일 크기 제한은 8MB입니다. 예제 입력은 [examples/inbox.json](examples/inbox.json), 예상 판단은 [examples/README.md](examples/README.md), 결과는 [examples/expected/](examples/expected/)에 있습니다.

## 실제 이메일과 개인정보 삭제

사용자가 이미 허용한 읽기 전용 이메일 연결 또는 사용자가 제공한 내보내기만 사용합니다. 추가 계정 권한이나 독립 프로그램 설치를 요구하지 않습니다. 연결이 없으면 제공한 파일로 작업합니다. 메일 보내기와 일정 변경은 하지 않습니다.

메일에 적힌 명령은 자료로만 읽습니다. 첨부 파일 실행, 외부 링크 방문, 권한 변경을 허락하는 지시로 받아들이지 않습니다. 실제 업무 기록은 **이 공개 배포 폴더 밖의 비공개 위치**에 보관하세요.

잘못 가져온 민감한 내용을 지울 때에는 먼저 `redact-preview`로 범위를 확인하고, 그 전체 범위에 대한 사용자의 삭제 지시를 확인한 뒤 `redact`를 적용합니다. 같은 출처를 공유하는 카드와 모든 과거 판본을 따라 범위를 보수적으로 넓힙니다. 대상 출처의 본문·메일 식별 정보·주소 위치, 대상 카드의 글과 결론을 현재 상태와 과거 이력에서 지웁니다. 다른 업무의 내용을 반복했을 가능성 때문에 **모든 관계 설명과 모든 기존 변경 이유도 지웁니다.** 삭제 이유의 원문은 wiki에 저장하지 않고 SHA-256만 남깁니다.

삭제 후에도 출처·카드·사건·관계·작업 ID, 시각, 해시, 비식별 실행자 같은 기록은 남습니다. 원본 이메일 파일, 삭제 요청 파일, 별도 출력, 백업, 동기화본, Git 과거 기록은 지우지 않습니다. 근거 연결 없이 다른 카드에 복사한 자유 문장은 자동으로 찾을 수 없습니다. 따라서 이 기능은 관리하는 wiki 안의 정해진 내용을 지우는 기능이며, 개인정보가 모든 곳에서 완전히 사라졌다는 보증은 아닙니다. 삭제는 되돌릴 수 없고, 같은 기존 wiki를 지정한 재가져오기는 지워진 출처의 본문을 복원하지 않습니다.

절차는 [SKILL.md](skills/life-wiki/SKILL.md), 기록 형식은 [data-model.md](skills/life-wiki/references/data-model.md), 삭제·변경·내보내기는 [operations.md](skills/life-wiki/references/operations.md)에 있습니다. 자동 검사는 형식·시각·발췌·참조 무결성을 확인하지만, 업무 의미나 개인정보가 전부 올바르다는 것을 보증하지 않습니다. 공개 전에는 남은 식별자와 이력까지 확인하세요.

## 배포와 사용권

공개 주소는 [JeonKH81/Life-wiki](https://github.com/JeonKH81/Life-wiki)이며, 이번 검토의 공개 기준본은 `1114830`입니다. 리뷰 수정의 코드와 검증 범위는 이 폴더와 검증 요약에 기록합니다. 도구가 GitHub 업로드나 사이트 배포를 자동으로 수행하지는 않습니다.

[MIT License](LICENSE)는 이 패키지에서 새로 작성한 코드·지침·가상 예제에 적용됩니다. 가져오는 실제 이메일, 첨부 자료, 타인의 문서·자산에는 사용권을 부여하지 않습니다. 타사 자산과 개인 업무 자료는 포함하지 않았습니다.
