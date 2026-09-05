# 장면 승인 도구 — 단계마다 사람이 보고 승인한다

근거 ADR `260905-104910`. 코드는 `scripts/canon/`의 `attempt.py`(시도 실행기) · `approve.py`(승인 기록기) ·
`scene_state.py`(재검토 계산, 순수 함수) 셋. 1/2(task 338)이 만든 **화면 없는 밑판**이다.

한 장면은 여러 단계로 나뉘고, 각 단계는 앞 단계 그림 **위에** 그려진다. 사람이 단계마다 「이것으로 간다」를
정하면 그 승인이 명세에 남고, 다음 단계는 그 승인본 위에서 이어 그린다. 나중에 명세가 바뀌면 어떤 승인이
더 이상 맞지 않는지를 계산해 보여 준다 — 그것이 **재검토**다.

## 사다리 — 승인의 세 층

장면 하나를 완성하려면 아래에서 위로 세 층을 확인하고, 그 위에 단계별 승인을 얹는다.

| 층 | 무엇을 확인하나 | 해시에 들어가는 것 |
|---|---|---|
| ① `verses` | 이 장면이 어느 본문인가 | `spec.verses` 전체 |
| ② `description` | 무엇을 그릴 것인가 | `moment` + `background` + `figures` + `crowds` |
| ③ `split` | 어떤 단계로 나눌 것인가 | 단계의 (id, kind, region **이름**, skip, from) 순서 목록 + `regions`의 이름 집합 |

**구역 좌표와 단계 문구·부정어는 사다리에 넣지 않는다.** 그것은 각 단계의 입력이라 시도가 스냅샷으로 들고
있고, 바뀌면 **그 단계와 그 아래만** 재검토다. 사다리가 바뀌면 승인된 단계가 **전부** 재검토다.

해시는 `sha256(json.dumps(대상, ensure_ascii=False, sort_keys=True))`의 앞 12자다(`scene_state.ladder_hashes`).

## 곁파일 — `attempts/<scene-id>.json`

무엇을 어떤 입력으로 그렸는지의 이력. **`scenes/`에 두면 안 된다** — `check_scenes.py`가 `scenes/*.json`을
전부 장면 명세로 읽는다.

```json
{"scene": "authored-saul-gilgal-coronation", "sceneSeed": 11, "attempts": [
  {"id": "a004", "stage": "S4", "seeds": [11],
   "prompt": "<파생 **전** 명세 문구>", "neg": ["<명세 부정어 그대로>"],
   "region": [0.12, 0.37, 0.285, 0.92],
   "upstream": {"stage": "S3", "attempt": "a003", "seed": 11},
   "tokens": {"n": 63, "lim": 77}, "startedAt": "<ISO>", "seconds": 86.0, "by": "cli",
   "images": {"11": {"canvas": ".forge/reports/.../a004/t11-S4-s11.png",
                     "plate":  ".forge/reports/.../a004/t11-plate-S4-s11.png"}}}
]}
```

경로는 레포 뿌리 기준. `prompt`는 **파생 전** 명세 문구다 — 재검토 계산이 지금 명세와 직접 견줘야 하기 때문이다.
`upstream`이 `null`이면 빈 종이에서 시작했다는 뜻(첫 비건너뜀 단계).

화면의 「지우기」(`DELETE /api/scenes/<id>/attempts/<aid>/<seed>`)는 그 시드의 파일과 `images` 기록을 함께 지우고,
시드가 다 빠진 시도는 목록에서 빠진다. 승인이 가리키는 장과 도구 산출 폴더 밖 경로는 거절한다.

승인은 **명세 안에** 산다: 단계마다 `stages[i].approved = {attempt, seed, by, on}`,
장면 위에 `approved = {verses|description|split: {hash, by, on}, final: {attempt, seed, by, on}}`.

## 재검토 규칙

승인된 단계 N이 재검토인 조건(하나라도 참, `scene_state.stale`):

1. 승인이 가리키는 시도의 **문구·부정어·구역 좌표**가 지금 명세와 다르다
2. 그 시도의 `upstream`이 **직전 비건너뜀 단계의 지금 승인**과 다르다(첫 단계는 `null`)
3. 사다리 ①②③ 중 승인해 둔 해시가 지금 해시와 다르다
4. **앞 단계가 재검토다** — 그 캔버스 위에 그려졌으므로 함께 흔들린다

`final`은 마지막 단계의 지금 승인이 `approved.final`과 다르거나, 아래 어디든 재검토가 있으면 재검토다.

**4번(전파)은 계획의 예시 목록과 한 곳에서 갈렸다.** 계획은 「S1 구역 좌표 수정 → S1과 아래 전부」와
「S4 문구 수정 → S4·final만」을 함께 요구하는데 둘은 같이 설 수 없다. **과탐지 쪽(전파)을 택했다** —
안 잡으면 승인되지 않은 캔버스 위 그림이 최신으로 보이기 때문이다. 테스트는 `test_scene_state.py`.

**판의 독립**은 이 규칙 안에서 이렇게 나타난다: 배경을 바꾸면 판 단계는 `upstream`이 달라져 재검토지만,
판 시드·문구는 승인 기록에 그대로 있어 **같은 시드로 다시 얹는 시도**가 곧 확인이다.

## 명령

```
V=/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python
cd scripts/canon

# 한 단계를 한 번 그린다 (GPU · venv 파이썬)
$V attempt.py --scene authored-saul-gilgal-coronation --stage S1 --seeds 11

# 승인 (GPU 0 · host python3)
python3 approve.py --scene <id> --stage S4 --attempt a004 --seed 11
python3 approve.py --scene <id> --ladder verses|description|split
python3 approve.py --scene <id> --final --attempt a005 --seed 11

# 재검토·보드 확인
python3 -c "import json,scene_state as ss; \
  sp=json.load(open('scenes/<id>.json')); sd=json.load(open('attempts/<id>.json')); \
  print(ss.stale(sp,sd) or '재검토 없음')"

# 규칙 테스트 (GPU 0)
python3 -m unittest discover -s scripts/canon -p 'test_*.py'
```

`attempt.py`가 거절하는 것: `from`이 있는 단계(다듬기·지물 — 앞 단계 실루엣 기억에 기대서 재개가 못 잇는다) ·
앞 단계에 승인이 없는데 첫 단계가 아닌 경우 · 프롬프트 77토큰 초과(GPU를 쓰기 **전에** 막는다).

## 생성기에 더한 두 손잡이 (task 338)

| 플래그 | 뜻 |
|---|---|
| `--canvas <png>` | 빈 종이 대신 **이 그림 위에서** 이어 그린다. 크기가 캔버스와 다르면 거절한다. |
| `--out <dir>` | 산출 폴더를 바꾼다(기본 `.forge/reports/canon-pilot/scripture-scene`). |

둘 다 없으면 **지금까지와 똑같이** 돈다. 함께 `full` 단계의 캔버스도 저장하게 했다 — 저장하지 않으면 재개의
첫 입력이 파일로 없다. 파일이 하나 늘 뿐 픽셀은 바뀌지 않는다(봉인된 삼상17 v45 대 v41 픽셀 동일로 확인).

## 시드 규약 — 판 시드와 접지 시드는 다르다

- **배경·구역·능선 단계**: 시도 시드가 곧 장면 시드다. 생성기에 `--seeds <시드>`로 간다.
- **판 단계**: 장면 시드는 곁파일의 `sceneSeed`로 **고정**하고(접지 `_contact`가 그것을 쓴다), 시도 시드는
  판 시드로 `--plate-seeds <단계>=<시드>`에 들어간다.
- 한 시도에 여러 시드를 돌려도 파일이 겹치지 않게 라벨에 시도 시드를 싣는다(`t<시드>`).

## 재현 명령이 산출물을 대신한다

`.forge/reports/`는 gitignored다. 그림을 커밋하지 않는 대신 **시드를 포함한 재현 명령**을 노트에 적는다.
길갈 대관식 A1을 단계별 재개로 다시 만든 명령(1/2 DoD 2, 다섯 비교 전부 픽셀 동일):

```
V=/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python
cd scripts/canon
for S in S1 S2 S3 S4 S5; do
  $V attempt.py --scene authored-saul-gilgal-coronation --stage $S --seeds 11
  python3 approve.py --scene authored-saul-gilgal-coronation --stage $S \
    --attempt a00$(python3 -c "print(['S1','S2','S3','S4','S5'].index('$S')+1)") --seed 11
done
for L in verses description split; do python3 approve.py --scene authored-saul-gilgal-coronation --ladder $L; done
python3 approve.py --scene authored-saul-gilgal-coronation --final --attempt a005 --seed 11
```

## 용어집은 스스로 자란다

문구·부정어 아래의 한글은 `tool/glossary.json`에서 나온다. 그런데 그 파일은 **손으로 채운 것**이라
AI가 새 표현을 지을수록 뜻이 없는 조각이 늘어난다(실측 2026-09-05: 굴 문구를 고치니 열 개가
물음표로 떴다). 그래서 **지은 쪽이 뜻도 함께 내놓게** 했다.

- 문구를 지을 때 AI는 `gloss`를 함께 준다 — 자기가 쓴 **모든 조각과 모든 부정어**의 한글 뜻이다.
  서버가 그것을 용어집에 쌓으므로 다음부터는 물음표가 뜨지 않는다. **AI 호출은 늘지 않는다.**
- 그래도 빠진 것이 있으면 그것만 따로 번역해 채운다(`compose.translate`).
- **사람이 손으로 고쳐 넣은 표현**은 아무도 뜻을 모른다. 그때만 「모르는 낱말 번역」 버튼이 나타나고,
  누르면 모르는 조각만 번역해 용어집에 넣는다.
- **단계를 열 때 모르는 조각이 있으면 알아서 번역한다.** 버튼을 눌러야 한글이 붙는 것은 도구가 할 일을
  사람에게 미루는 것이다. 같은 문구로는 한 번만 시도한다(실패해도 되풀이하지 않게) — 버튼은 그때 재시도용이다.
- 번역이 도는 20~40초 사이에 사람이 **다른 단계로 옮기면** 그 폼은 화면에서 떨어져 나간다. 그대로 두면
  결과가 얹힐 자리가 없어 돌아와도 물음표가 남는다 — 지금 떠 있는 화면을 다시 그려 얹는다(실측 2026-09-05).
- 이미 있는 뜻은 **덮지 않는다** — 서버도 화면도 같은 규칙이라 보이는 한글과 저장된 한글이 어긋나지 않는다.
- 용어집 쓰기는 임시 파일에 쓰고 `os.replace`로 갈아끼운다. 반쯤 쓰인 파일이 남지 않는다.

`SCENE_TOOL_GLOSSARY`로 용어집 경로를 갈아끼운다. **스모크는 반드시 이것을 건다** — 가짜 뜻이 실제
용어집에 쌓이면 안 된다(같은 종류의 사고를 산출 경로에서 한 번 냈다).

## 문구는 AI가 짓는다 — 사람은 한국어로 시킨다

「손으로 프롬프트를 쓰지 않는다」(PROMPTING 7)는 규칙을, 사람이 영어를 타이핑하던 자리에도 적용한다.
폼의 **「AI에게 시키기」**에 한국어로 말하면 `claude -p`가 영문 단계 문구와 부정어를 지어 폼에 채운다.
**명세에는 쓰지 않는다** — 사람이 읽고 고친 뒤 「명세에 저장」이나 「그리기」를 눌러야 들어간다.

무엇을 함께 넘기나(`tool/compose.py`의 briefing):

- 실측 규칙 일곱 — 77토큰 하드 한계(화풍 머리 22가 이미 붙으므로 확장 후 55 이내) · 문장이 아니라
  쉼표로 끊은 명사구 · **인물 생김새를 직접 쓰지 말고 `{cast:<id>}`를 쓸 것** · 형용사보다 대상의
  색·매체 낱말 · 부정어는 짧게 · 배경 단계는 사람 없음 · **용어집에 이미 있는 조각을 재사용할 것**
- 그 장면의 한국어 근거 — 본문 인용 · 고정한 순간 · 배경 · 무리 · 인물의 역할과 자세
- 그 단계의 종류·구역 좌표·지금 문구와 부정어, 쓸 수 있는 자리표시자와 그 확장 영문
- 용어집의 조각 목록 전체(재사용하면 화면에 한글 뜻이 그대로 붙는다)

받은 문구는 **저장하기 전에** `tool/count_tokens.py`(venv)로 잰다. `{cast:...}` 확장까지 포함해 세므로
판 단계에서도 어긋나지 않는다. 넘치면 폼 옆에 주황색으로 알린다.

2026-09-05 실측: 「사무엘이 기름 뿔을 들어 올리게」라 시키니 용어집의 기존 조각만 골라 쓰고(한글 뜻이
전부 붙었다), 뿔이 나팔로 그려지는 것을 막으려 `trumpet`을 부정어에 더했으며, **기름 뿔이 삼상 11장
본문에 없는 요소임을 스스로 짚었다.** 72/77.

**요청을 붙잡지 않는다.** AI 호출이 20초~2분이라 응답을 기다리며 연결을 잡고 있으면 **폰 브라우저가
먼저 끊는다** — 서버는 멀쩡히 다 만들었는데 화면에는 `Failed to fetch`만 뜬다(실측 2026-09-05,
로그에 `BrokenPipeError`). GPU 큐와 같은 방식으로 `POST`는 일감 번호만 주고, 화면이
`GET /api/compose/<번호>`를 1.5초마다 물어본다. 버튼에 경과 초가 뜬다.

느린 쪽은 AI 호출 자체다 — 토큰 재기 2초, 지시문 만들기 0초, 나머지가 모델 시간이다(실측 72초·11KB 지시문).

`SCENE_TOOL_FAKE_AI=1`이면 AI를 부르지 않고 정해진 답을 준다(스모크 전용 — 느리고 값이 든다).

## 화면에서 구역 고르기

구역은 `[x0, y0, x1, y1]`의 캔버스 비율(0~1)인데, 그 숫자를 손으로 넣는 것은 사람이 할 수 있는 일이
아니다. 폼에 **그 단계가 얹힐 캔버스**를 띄우고 그 위에서 사각형을 끌면 좌표가 채워진다.

- 배경 그림 = **직전 비건너뜀 단계의 승인본**. 실제로 이 단계가 칠해질 바로 그 그림이다.
  첫 단계처럼 앞이 없으면 종이색 빈 판이 뜬다.
- 뒤집어 끌어도 `x0<x1`·`y0<y1`로 정규화한다. **2% 미만으로 살짝 누르면 없던 일이 된다** —
  구역을 보려고 탭했다가 상자가 사라지지 않게.
- 아래 숫자 칸은 미세 조정용이고 상자와 양방향으로 붙어 있다.
- 한 구역 이름을 여러 단계가 함께 쓰면 폼이 경고한다 — 고치면 함께 움직인다.

캔버스 규격은 `params.SCENE_SIZE`(1216×640)이고 서버가 `/api/scenes/<id>`의 `canvas`로 알려 준다.

## 서버 띄우기

```
SCENE_TOOL_USERS=thkim@anchors-biz.com python3 scripts/canon/tool/server.py
# → http://127.0.0.1:8100
```

기본은 `127.0.0.1`에만 붙는다. 표준 라이브러리만 쓰고(백엔드 requirements 불변), GPU 작업은 `attempt.py`를
venv 파이썬 서브프로세스로 부른다. **워커 스레드 하나·큐 하나** — 「재시도」를 연달아 눌러도 줄을 선다
(생성 프로세스가 겹치면 처리량이 20배 떨어진다).

로컬에서 브라우저로 그냥 볼 때는 헤더가 없으므로 `SCENE_TOOL_DEV=1`을 함께 준다(승인의 `by`가 `dev`).

| 환경변수 | 뜻 |
|---|---|
| `SCENE_TOOL_USERS` | 쉼표로 허용 이메일. `Cf-Access-Authenticated-User-Email`이 목록에 없으면 **403** |
| `SCENE_TOOL_DEV=1` | 헤더 없이 통과, `by=dev` (로컬 전용) |
| `SCENE_TOOL_FAKE_GEN=1` | GPU 대신 자리표시 PNG (스모크 전용) |
| `SCENE_TOOL_SCENES_DIR` · `SCENE_TOOL_ATTEMPTS_DIR` | 명세·곁파일 폴더 교체 (스모크가 실제 명세를 안 건드리게) |
| `SCENE_TOOL_TOKEN` | 토큰 자물쇠. `?t=<토큰>` 또는 `X-Scene-Token` 헤더가 맞으면 통과 (같은 망의 폰) |
| `SCENE_TOOL_BIND` | 기본 `127.0.0.1`. 같은 망에 내놓으려면 `0.0.0.0` |
| `SCENE_TOOL_PORT` | 기본 8100 |

**자물쇠 없이는 망에 안 나간다.** `SCENE_TOOL_BIND`가 루프백 밖인데 토큰도 허용목록도 없으면 서버가
기동을 거부한다. `SCENE_TOOL_DEV=1`은 루프백에서만 받는다 — 망에 내놓은 채로 켜면 아무나 들어온다.

**껍데기 한 장(`GET /`)만 자물쇠 밖이다.** 데이터가 한 줄도 없고, 화면이 저장해 둔 토큰을 실어 보내려면
먼저 화면이 떠야 한다. `/api`와 `/img`는 전부 자물쇠 안이다(토큰 없으면 403).

**헤더 안전핀이 왜 있나**: 터널 뒤의 유일한 입구가 Cloudflare Access이므로, 서버는 Access가 넣어 주는
이메일 헤더가 허용 목록에 있는지만 본다. JWT 서명 검증은 하지 않는다 — 첫 판의 안전핀으로 충분하고,
검증을 넣으면 표준 라이브러리 밖으로 나가야 한다.

## 대기열 — 한 번에 하나, 취소할 수 있다

화면 아래 검은 띠가 GPU 작업 대기열이다.

| 값 | 뜻 |
|---|---|
| **그리는 중** | 지금 GPU가 돌리는 작업 하나. 워커가 하나라 언제나 하나만 돈다 |
| 장면 id · 단계 · 시드 | 그 작업이 무엇을 그리는가 (`authored-` 접두는 떼고 보인다) |
| **대기 N** | 뒤에 줄 선 작업 수. 앞의 것이 끝나면 하나씩 꺼낸다 |
| **멈추기** · **대기 비우기** | 도는 것은 프로세스를 죽여 멈추고, 줄에 선 것은 빼낸다 |

**같은 단계·같은 시드는 두 번 줄 서지 못한다.** 생성은 결정적이라 같은 캔버스에 같은 시드면 몇 번을
돌려도 **같은 그림**이다. 2026-09-05 실측: 버튼이 안 눌린 줄 알고 연달아 눌러 1초 안에 넉 장이 줄을
섰고, 끝난 둘을 픽셀로 견주니 차이가 `None`이었다(각 45~49초). 이제 두 번째 요청은 거절하고
「시드를 바꿔라」고 답한다. 다른 그림을 보려면 시드를 바꾸는 것이 유일한 길이고, 「3장 그리기」가
11·42·7을 쓰는 이유가 그것이다.

누른 즉시 띠가 「줄에 넣는 중…」으로 바뀌고, 동작이 끝나면 곧바로 큐를 다시 읽는다 — 3초 폴링만
믿으면 그 사이에 「안 눌렸나」 싶어 또 누르게 된다.

## 같은 와이파이에서 폰으로 보기 (터널 없이, 지금 바로)

터널·DNS·Access를 건드리지 않는 길이다. 맥과 폰이 **같은 망**에 있어야 한다.

```
TOK=$(cat ~/.biblemap-scene-tool-token)
cd /Users/calmonion/Project/BibleMap
SCENE_TOOL_BIND=0.0.0.0 SCENE_TOOL_TOKEN="$TOK" python3 scripts/canon/tool/server.py
echo "http://$(ipconfig getifaddr en0):8100/?t=$TOK"      # 이 주소를 폰에서 연다
```

토큰은 `~/.biblemap-scene-tool-token`에 있다(레포 밖 · `chmod 600`). 폰에서 `?t=`가 붙은 주소를 **한 번만**
열면 브라우저가 토큰을 저장하고 주소창에서 지운다 — 그 뒤로는 `http://<맥 주소>:8100/`만으로 들어간다.
홈 화면에 추가해 두면 편하다.

⚠ 맥의 LAN 주소는 공유기가 바꿀 수 있다. 안 열리면 `ipconfig getifaddr en0`으로 다시 확인한다.
⚠ 맥이 잠들면 끊긴다. 오래 쓸 것이면 「바깥에서 열기」의 터널 쪽이 낫다.

## 바깥에서 열기 (폰에서 보기 — **사람 손**)

터널 설정은 여러 프로젝트가 함께 쓰는 자원이라 **실행하지 않는다.** 아래는 사람이 직접 하는 다섯 단계다.

**① `~/.cloudflared/config.yml`에 두 줄을 넣는다** — 맨 끝 `- service: http_status:404` **앞**에.
`# >>> fitcheck-managed` ~ `# <<< fitcheck-managed` 구간은 다른 레포가 생성하므로 **그 밖에** 넣는다.

```yaml
  - hostname: scene.taebro.com
    service: http://localhost:8100
```

**② DNS 라우트를 만든다**

```
cloudflared tunnel route dns portfolion scene.taebro.com
```

**③ 터널을 재시작한다.** plist가 둘 보이는데 **실제로 `tunnel run portfolion`을 띄우는 쪽**만 재시작한다.
2026-09-05 실측: `com.cloudflare.cloudflared`가 PID를 물고 있고 `homebrew.mxcl.cloudflared`는 놀고 있었다.
매번 확인하고 고른다.

```
launchctl list | grep cloudflared          # PID가 붙은 라벨이 실제로 도는 쪽이다
ps aux | grep 'cloudflared tunnel'         # 교차 확인
launchctl kickstart -k gui/$(id -u)/com.cloudflare.cloudflared
```

⚠ **재시작하는 동안 이 터널을 지나는 사이트가 전부 잠깐 끊긴다** — 2026-09-05 기준
`biblemap` · `portfolion` · `lab` · `fitcheck` · `dev-fitcheck` **다섯**이다.

**④ Cloudflare Zero Trust에서 Access 앱을 만든다**: Access → Applications → Add an application →
Self-hosted · 도메인 `scene.taebro.com` · 정책 Allow · Emails = 본인 이메일.
이 정책이 `SCENE_TOOL_USERS`와 **같은 이메일**이어야 통과한다.

**⑤ 확인한다**

```
curl -sI https://scene.taebro.com | head -1     # → HTTP/2 302 (Access 로그인으로 보낸다)
```

폰 브라우저로 `https://scene.taebro.com`을 열어 이메일 코드로 로그인하면 장면 목록이 나온다.
