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
