# LIFE wiki 설치 안내

[처음 시작하기](../README.md) · [English](../README.en.md) · [검증 기록](VERIFICATION.md)

Codex에 설치를 맡기려면 [README의 설치 요청문](../README.md)을 복사해 보내세요. 직접 실행하려면 아래 다운로드 후 설치 명령을 사용합니다. 가상 메일 체험은 필요 없습니다.

## 공통 준비: 공개 파일 다운로드

1. [공개 저장소](https://github.com/JeonKH81/LIFE-wiki)를 브라우저에서 엽니다.
2. 파일 목록 위의 **Code** → **Download ZIP**을 누릅니다. GitHub 로그인·Fork는 필요 없습니다.
3. 내려받은 ZIP을 압축 해제합니다. 보통 `LIFE-wiki-main` 폴더가 생깁니다.
4. 폴더 안에 `README.md`, `requirements.txt`, `skills`, `examples`가 있는지 확인합니다. ZIP 자체를 열어 보는 것과 압축 해제는 다릅니다.

Git을 이미 사용하는 분은 대신 빈 작업 위치에서 아래 명령을 실행할 수 있습니다. ZIP과 둘 다 할 필요는 없습니다.

```sh
git clone https://github.com/JeonKH81/LIFE-wiki.git
cd LIFE-wiki
```

<a id="direct-install"></a>
## 한 번에 설치

**준비물:** Python 3.10 이상, 설치 때 인터넷 연결. 압축 해제한 저장소 폴더에서 실행하세요. Python은 [공식 다운로드](https://www.python.org/downloads/)를 사용합니다.

macOS 터미널에서는 `cd `를 입력하고 압축을 푼 폴더를 Finder에서 터미널로 끌어 놓은 뒤 Enter를 누릅니다. 이어서 한 줄을 실행합니다.

```sh
python3 scripts/install.py --dest ../my-life-wiki
```

Windows PowerShell 명령 (이 환경에서는 미실행):

```powershell
py -3 scripts/install.py --dest ..\my-life-wiki
```

`my-life-wiki`는 새로 만들 **설치 대상**입니다. 이미 존재하면 덮어쓰지 않고 중단합니다. 그때는 `my-life-wiki-2`처럼 새 이름을 사용하세요. 설치 대상의 상위 폴더는 존재해야 합니다. 가상환경 활성화나 전역 pip 설치는 필요 없습니다.

설치 스크립트는 전용 `.venv`를 만들고 의존성을 설치한 뒤 빈 위키를 검증하고 화면을 내보냅니다. macOS에서 실제 실행했습니다. 완료 시 `Installed:`와 프로젝트·화면·JSON의 경로를 출력합니다. 기록은 `Valid; revision 0; 0 cards.`이어야 합니다.

```text
my-life-wiki/
  .agents/skills/life-wiki/   # 스킬·도구·스키마·화면 파일
  .venv/                    # 설치한 의존성
  data/wiki.json            # 빈 위키, 이후 실제 자료 저장
  viewer/index.html         # 7개 메뉴와 연결지도 화면
  viewer/initial-data.js    # 자동으로 불러오는 내보낸 기록
  OPEN-ME.txt                # 여는 순서
```

설치한 같은 Codex 대화에 README의 실제 자료 정리 요청을 보냅니다. Codex가 설치된 지침 파일을 직접 읽고 작업합니다. 결과로 제공한 `index.html` 파일을 브라우저에서 열면 내보낸 기록을 자동으로 표시합니다. 프로젝트를 바꾸거나 JSON을 고르는 단계는 없습니다. 빈 위키에는 노드가 없으며 가상 예제 버튼은 설치하지 않습니다. README의 실제 자료 정리 요청을 보내면 자료에 근거한 카드와 관계를 저장할 수 있습니다. 화면은 읽기 전용이고, 실제 브라우저의 로컬 파일 렌더링은 미검증입니다.

실패하면 `INSTALL-INCOMPLETE.txt`가 남을 수 있습니다. 기존 폴더는 변경하지 않습니다. 오류와 새 폴더의 상태를 확인하고, 다시 설치할 때는 다른 새 경로를 사용하세요. 인터넷·Python 오류는 아래 표를 참고하세요. 실제 메일·개인 사이트 설정·자동 갱신·배포는 설치하지 않습니다.

<a id="codex"></a>
## 수동으로 스킬만 복사 (선택)

이미 별도의 Codex 프로젝트와 Python 환경을 준비했다면 공개 파일의 `skills/life-wiki` 전체를 프로젝트의 `.agents/skills/life-wiki`로 복사할 수 있습니다. 기존 스킬은 덮어쓰지 마세요. `SKILL.md` 한 파일만 복사하면 도구가 빠집니다. [공식 스킬 발견 방식](https://learn.chatgpt.com/docs/build-skills)에 따라 그 프로젝트를 Codex에서 열고 `$life-wiki`를 선택합니다.

<a id="local-demo"></a>
## 개발자용 가상 예제 검사 (설치와 무관, 선택)

**준비물:** Python 3.10 이상과 인터넷 연결(처음 의존성 설치 때만). Python은 [공식 다운로드](https://www.python.org/downloads/)를 사용하세요. Node.js는 **검사 전체를 실행할 때만** 필요하며 샘플 내보내기에는 필요 없습니다.

아래 명령은 **macOS 터미널에서 검증했습니다.** Linux와 Windows 전체 설치·화면 실행은 이번 검증에서 확인하지 않았습니다. Windows의 PowerShell 명령은 뒤에 별도로 제시합니다.

### macOS: 한 줄씩 실행

1. 터미널 앱을 엽니다. 아래 상자는 AI 대화창이 아니라 **터미널**에 입력합니다.
2. `cd `를 입력하고, 압축을 푼 `LIFE-wiki-main` 폴더를 Finder에서 터미널로 끌어 놓은 뒤 Enter를 누릅니다. 저장소 안에서 `requirements.txt`가 보이는 위치여야 합니다. Git으로 받았다면 `cd LIFE-wiki`를 사용합니다.
3. 아래 명령을 순서대로 한 줄씩 붙여 넣습니다. 오류가 나면 다음 줄로 넘어가지 말고 아래 오류 표를 확인하세요.

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python skills/life-wiki/scripts/wiki.py validate examples/expected/wiki.json
.venv/bin/python skills/life-wiki/scripts/wiki.py render examples/expected/wiki.json --out demo-work
```

`python3 --version`은 3.10 이상이어야 합니다. `.venv`는 이 작업용 Python 폴더이며 기존 Python 설정을 바꾸지 않습니다. 직접 의존성은 `jsonschema`이며 필요한 하위 의존성이 함께 설치됩니다. `validate`는 `Valid; revision 0; 4 cards.`를 출력합니다. `render`는 `Export created. Open index.html; the exported records load automatically.`를 출력합니다.

**기대 결과:** 저장소 아래 새 `demo-work/` 폴더에 아래 파일들이 생깁니다. 이미 있는 폴더는 덮어쓰지 않으므로 재실행 때는 `--out demo-work-2`처럼 새 이름을 쓰세요. 출력 폴더를 미리 만들지 않습니다.

```text
demo-work/
  index.html
  app.js
  demo-data.js
  graph.js
  style.css
  wiki.json
  cards/                 # 가상 업무 4개의 Markdown 파일
```

4. Finder에서 `demo-work/index.html`을 더블 클릭합니다. 업무 4개가 자동으로 표시됩니다. 다른 파일을 보려는 경우에만 **다른 기록 파일 열기**를 사용합니다. **가상 예제 보기**는 내보낸 파일 대신 업무 4개+일상 2개의 내장 예제를 보여 줍니다. 기본 표시 내용은 내보낼 때 저장된 기록입니다. 원본 JSON을 직접 바꿔도 화면에 실시간으로 반영되지 않으므로 다시 내보내세요.
5. **연결 지도** 메뉴에서 노드를 눌러 상세 기록을 봅니다. 드래그로 회전하고 스크롤 또는 +/−로 확대·축소합니다. 키보드는 방향키·+/−·Home을 사용할 수 있습니다. 캔버스를 쓰기 어려우면 **전체 기록 보기 · 연결 목록**의 기록 버튼을 사용합니다. 실선은 근거가 확인된 관계, 점선은 불확실한 관계이며 위치나 거리는 관계의 강도를 뜻하지 않습니다. 검색·상태 필터는 지도와 목록에 함께 적용됩니다. **내 기록**은 카드 상세, **운영 변경**은 불러온 JSON의 변경 이력을 보여 줍니다. 가상 샘플의 이력은 비어 있으므로 최초 기록이라고 나오는 것이 정상입니다. 나머지 **결정과 근거·주제별 기록·사람과 역할·참고 기록** 메뉴는 저장된 승인/실행 근거·카드별 주제·역할 확인용 원문·출처를 보여 줍니다. 공개 형식에는 구조화된 인물 필드가 없어 사람 목록을 추정하지 않습니다.
6. 검색에 `ISLET`을 입력하면 내장 예제에서 여행 예약 변경을 찾을 수 있습니다. 업무 JSON을 선택한 상태에서는 일상 카드가 없으므로 검색 결과가 없습니다.

**브라우저 한계:** 실제 브라우저의 `file://` 보안 정책과 화면 작동은 이번 환경에서 확인하지 못했습니다. 브라우저 도구가 해당 URL을 차단했고 우회하지 않았습니다. 빈 화면이나 버튼 오류가 있으면 보안 설정을 끄지 말고 `cards/*.md`를 텍스트 편집기로 읽으세요. 코드 검사는 실제 브라우저 테스트를 대신하지 않습니다.

일상 2개만 내보내려면 같은 터미널 위치에서 실행합니다.

```sh
.venv/bin/python skills/life-wiki/scripts/wiki.py validate examples/everyday/expected/wiki.json
.venv/bin/python skills/life-wiki/scripts/wiki.py render examples/everyday/expected/wiki.json --out demo-everyday
```

검증 결과는 `Valid; revision 0; 2 cards.`입니다. `demo-everyday/index.html`을 열면 해당 기록이 자동으로 표시됩니다.

### Windows PowerShell (명령 예시, 이 환경에서는 미실행)

압축 해제한 저장소 폴더에서 PowerShell을 엽니다. Python 런처 `py`가 설치돼 있어야 합니다. 가상환경 활성화 스크립트나 실행 정책 변경은 필요 없습니다.

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe skills/life-wiki/scripts/wiki.py validate examples/expected/wiki.json
.\.venv\Scripts\python.exe skills/life-wiki/scripts/wiki.py render examples/expected/wiki.json --out demo-work
```

버전·출력 파일·화면 여는 순서는 macOS 설명과 같습니다. Windows용 내보내기 코드가 있지만 실제 실행은 검증하지 않았습니다.

### 입력 메일 JSON과 결과 wiki JSON은 다릅니다

`examples/inbox.json`은 가상 메일 **9개**이고, 중복 1개가 있습니다. 아래 명령은 **출처 8개로 정리**할 뿐 카드나 그래프를 생성하지 않습니다.

```sh
.venv/bin/python skills/life-wiki/scripts/wiki.py normalize examples/inbox.json --out demo-sources.json
```

`demo-sources.json`은 화면에 넣는 `wiki.json`이 아닙니다. AI/사람이 메일의 의미와 카드 경계를 판단해 위키 형식으로 작성해야 합니다. `examples/expected/wiki.json`은 **미리 판단해 작성한 결과**입니다. 일반 `.eml`, `.mbox`, Outlook 파일을 이 명령에 바로 넣는 기능은 없습니다. [입력 형식](../skills/life-wiki/references/intake.md)과 [기록 형식](../skills/life-wiki/references/data-model.md)을 참고하세요.

### 개발자용 전체 검사

Node.js가 설치된 상태에서 같은 위치에서 실행합니다. 정상 설치 확인용 첫 단계와는 별개입니다.

```sh
.venv/bin/python -m unittest discover -s tests -v
node tests/viewer.test.js
node tests/graph.test.js
```

<a id="troubleshooting"></a>
## 오류 해결

| 메시지·증상 | 원인과 해결 |
|---|---|
| `python3: command not found` / `py`를 찾을 수 없음 | Python 설치와 버전을 확인하고 터미널을 다시 엽니다. macOS에 `py` 명령을 쓰지 않습니다. |
| `requirements.txt` / `wiki.py`를 찾을 수 없음 | 현재 폴더가 다릅니다. 압축 해제한 저장소 폴더로 이동합니다. `.venv` 안으로 이동하지 않습니다. |
| `No module named jsonschema` | `.venv`의 Python으로 의존성 설치와 도구 실행을 모두 했는지 확인합니다. |
| pip 연결·DNS·인증서 오류 | 인터넷·프록시·기관의 승인된 설치 방법을 확인합니다. 인증서 검사를 끄거나 `sudo pip`를 사용하지 않습니다. |
| `File operation failed; check existence, permissions, and destination locally.` | 입력 경로·쓰기 권한·출력 존재 여부를 확인합니다. 출력이 이미 있으면 새 이름을 사용하고, 상위 폴더는 존재해야 합니다. |
| JSON 형식·출처·상태 오류 | 메일 입력 파일과 위키 결과 파일을 구분합니다. `validate`의 오류를 수정한 뒤 내보냅니다. 실제 기록을 샘플로 대체하지 않습니다. |
| 화면에서 8MB 오류 | 화면 파일 크기 제한입니다. AI에게 필요한 기록만 별도의 유효한 위키로 내보내도록 요청하거나 Markdown을 읽습니다. |
| 스킬이 안 보임 | 프로젝트 위치와 `.agents/skills/life-wiki/SKILL.md`를 확인합니다. `life-wiki/life-wiki/SKILL.md`처럼 두 번 중첩하지 않습니다. Codex를 다시 시작합니다. |
| 화면에서 고쳤는데 저장이 안 됨 | 정적 화면은 읽기 전용입니다. 원본 `wiki.json`의 보호된 변경 절차를 사용하고 새 폴더로 다시 내보냅니다. |

실제 자료의 변경·합치기·나누기·되돌리기·민감정보 삭제는 [보호된 작업 절차](../skills/life-wiki/references/operations.md)를 따릅니다. 삭제는 되돌릴 수 없고 원본 메일·옛 출력·백업은 별도로 남습니다. 실제 기록은 공개 저장소 밖에 보관하세요.
