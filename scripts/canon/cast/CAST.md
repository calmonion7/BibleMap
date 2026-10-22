# 다윗 투어 36정차지 — 등장인물 명단(S1) · 어휘 정본(S2)

근거: `.forge/scratch/david-tour-verses.md`(36정차지 절 범위·개역한글 본문 전부, 유일한 진리 근거).

## 명단 도출 규칙

- **인물** = 고정한 순간에 판(plate)으로 단독으로 그릴 개체. 이름 있는 개인뿐 아니라, 이름 없어도 장면의 핵심 개체(엔돌의 신접한 여인, 두 여인, 스바 여왕)를 포함한다.
- **군중은 인물이 아니다**: 백성·군대·제사장들·왕비들·창기의 배경 등은 역표의 「군중/무리」 열로 뺐다. 예: 미스바의 「모든 백성」, 놉 학살의 「남녀와 아이들」, 성전 낙성식의 「온 이스라엘 회중」.
- **생애 단계가 크게 갈리는 인물은 id를 나눈다**: 사울(청년~장년 재위, mizpah~en-gedi)과 사울(노년, 엔돌·길보아 — 삼상28:20 「기력이 진하였으니」)을 나눴다. 다윗도 소년(david-boy, 수금·기름부음·골리앗)·청년(david-youth, 골리앗 뒤 군대의 장 — 삼상18:5·13·27, 15~20세, task 399)·도망자(david, 즉위 전 20대)·장년 왕(david-prime, 헤브론~솔로몬 출생 — 삼하5:4-5)·노년 직전 왕(david-elder, 압살롬 반란·귀환 60세 전후)·노년(david-old, 왕상2:1 임종 유언)으로 나눴다. 솔로몬은 청년 왕(solomon, 왕상9:10 「이십 년」 이전)·장년 왕(solomon-prime, 궁전·에시온게벨·스바)·노년(solomon-old, 왕상11:4 「나이 늙을 때에」)으로 나눴다(task 355). id 이름은 카드 층 `ageBand` 사다리(youth < young < prime < elder)를 따른다. 새로 나눈 id는 얼굴 층을 원래 id와 같게 둔다(같은 사람).
- **본문에 등장만 하고 직접 행동하지 않는 이름**(엘리압 등 이새의 아들들, 사독·브나야, 바로의 딸, 이스보셋)은 인물로 세우지 않고 군중/배경으로 처리했다 — 근거가 이름 언급 1회뿐이고 반복 등장이 없어 별도 판이 불필요하다고 판단.
- 하나님/천사/여호와의 영은 인물로 세우지 않는다(그리지 않음). 사무엘의 영은 엔돌 정차지에서 「영으로 등장」으로 표시했다.
- 골리앗은 36정차지 본문 범위 밖(삼상17장)이지만 사용자 지시로 명단에 포함 — 정차지 없음(v41 기존 자산 이관, 재저작 대상).
- 두 여인은 한 인물 한 판 원칙으로 mother-a/mother-b로 나눴다(사용자 판정 2026-09-04).

## 명단 표 (정차지 수 내림차순)

| id | 이름(한글·별칭) | 등장 정차지(id 목록) | 정차지 수 | 비고 |
|---|---|---|---|---|
| david | 다윗, 이새의 아들 다윗 | ramah-samuel, ramah-death, nob-priests, gath-achish, adullam-cave, en-gedi-saul, ziklag-base | 7 | 즉위 전 도망자(20대) 구간 |
| saul | 사울, 기스의 아들 사울 | mizpah-chosen, jabesh-rescue, gilgal-coronation, michmash-battle, gilgal-amalek, gibeah-harp, gibeah-spear, nob-massacre, en-gedi-saul | 9 | 청년 선택~재위 구간 |
| solomon | 솔로몬 | gihon-anointing, solomon-jerusalem-david-charge, gibeon-dream, two-mothers, temple-build, temple-dedication | 6 | 청년 왕 구간(왕상9:10 「이십 년」 이전) |
| samuel | 사무엘 | mizpah-chosen, gilgal-coronation, michmash-battle, gilgal-amalek, bethlehem-david-anointing, ramah-samuel, endor-medium | 7 | 엔돌은 영으로 등장 |
| david-boy | 다윗(소년) | bethlehem-david-anointing, gibeah-harp | 2 | 기존 v41 정본 이관 출발점 · 골리앗 장면(정차지 아님)도 이 id(삼상17:33·42 「소년」) |
| david-youth | 다윗(청년) | gibeah-spear | 1 | 생애 단계 분할(task 399, 사용자 「청소년기 15~20 · 유추 가능」), 삼상18:5 군대의 장·18:13 천부장·18:27 혼인 · 정본 그림 없음 |
| ahimelech | 아히멜렉, 제사장 아히멜렉 | nob-priests, nob-massacre | 2 | 놉 학살에서 사망 |
| doeg | 도엑, 에돔 사람 도엑 | nob-priests, nob-massacre | 2 | |
| achish | 아기스, 가드 왕 아기스 | gath-achish, ziklag-base | 2 | |
| saul-old | 사울(노년) | endor-medium, gilboa-death | 2 | 생애 단계 분할 |
| nathan | 나단, 선지자 나단 | nathan-covenant, solomon-jerusalem-birth, gihon-anointing | 3 | |
| nahash | 나하스, 암몬 사람 나하스 | jabesh-rescue | 1 | |
| jesse | 이새 | bethlehem-david-anointing | 1 | |
| david-old | 다윗(노년) | solomon-jerusalem-david-charge | 1 | 생애 단계 분할, 왕상2:1 임종 유언 |
| david-prime | 다윗(장년 왕) | hebron-king-judah, jerusalem-conquest, ark-jerusalem, nathan-covenant, solomon-jerusalem-birth | 5 | 생애 단계 분할(task 355), 삼하5:4-5 재위 전반 30~40대 · 정본 그림 없음 |
| david-elder | 다윗(노년 직전 왕) | mahanaim-exile, returns-jerusalem | 2 | 생애 단계 분할(task 355), 압살롬 반란 60세 전후 · 정본 그림 없음 |
| zadok | 제사장 사독 | gihon-anointing | 1 | 왕상1:39 기름 뿔로 솔로몬에게 기름 부음 |
| agag | 아각, 아말렉 왕 아각 | gilgal-amalek | 1 | |
| endor-medium | 엔돌의 신접한 여인 | endor-medium | 1 | 이름 없는 핵심 개체 |
| saul-armor-bearer | 병기 든 자 | gilboa-death | 1 | 이름 없는 핵심 개체 |
| jonathan | 요나단, 사울의 아들 요나단 | gilboa-death | 1 | |
| joab | 요압, 스루야의 아들 요압 | gibeon-battle | 1 | 2026-09-04 사용자 보류 → 문구 개정(b) |
| abner | 아브넬, 넬의 아들 아브넬 | gibeon-battle | 1 | |
| bathsheba | 밧세바, 다윗의 처 밧세바 | solomon-jerusalem-birth | 1 | |
| absalom | 압살롬 | mahanaim-exile | 1 | |
| mother-a | 참 어머니(두 여인 중 산 아이의 어머니) | mother-a | 1 | 이름 없는 핵심 개체 |
| mother-b | 다른 어머니(두 여인 중 죽은 아이의 어머니) | mother-b | 1 | 이름 없는 핵심 개체 |
| solomon-old | 솔로몬(노년) | apostasy | 1 | 생애 단계 분할 |
| solomon-prime | 솔로몬(장년 왕) | palace, ezion-geber-fleet, sheba | 3 | 생애 단계 분할(task 355), 왕상7:1·9:10 이후 40대 · 정본 그림 없음 |
| hiram | 히람 | ezion-geber-fleet | 1 | |
| sheba-queen | 스바 여왕 | sheba | 1 | 이름 없는 핵심 개체, 2026-09-04 사용자 보류 → 문구 개정(b) |
| shimei | 시므이, 게라의 아들 시므이, 바후림의 베냐민 사람 | returns-jerusalem | 1 | 2026-10-21 추가 — 삼하 19:18 왕 앞에 엎드림(사울의 집 족속, 삼하 16:5) |
| goliath | 골리앗, 블레셋 사람 골리앗 | (없음) | 0 | 삼상17 전용, v41 기존 정본 이관·재저작 대상 |

## 정차지별 역표(36건 전부)

| stop-id | 등장 인물 id | 군중/무리(인물 아님) |
|---|---|---|
| authored-saul-mizpah-chosen | samuel, saul | 이스라엘 모든 백성, 지파들 |
| authored-saul-jabesh-rescue | saul, nahash | 야베스 사람들, 이스라엘 삼십만·유다 삼만 |
| authored-saul-gilgal-coronation | samuel, saul | 모든 백성 |
| authored-saul-michmash-battle | samuel, saul | 백성(흩어짐) |
| authored-saul-gilgal-amalek | samuel, saul, agag | 아말렉 백성(진멸당함) |
| authored-samuel-bethlehem-david-anointing | samuel, jesse, david-boy | 성읍 장로들, 이새의 다른 아들들(엘리압 등) |
| authored-david-gibeah-harp | saul, david-boy | (없음) |
| authored-saul-gibeah-spear | saul, david-youth | (없음 — 18:6-7 여인들은 전날 일, task 394) |
| authored-david-ramah-samuel | david, samuel | (없음) |
| authored-david-nob-priests | david, ahimelech, doeg | 다윗의 소년들 |
| authored-david-gath-achish | david, achish | 아기스의 신하들 |
| authored-david-adullam-cave | david | 환난 당한 자·빚진 자·마음 원통한 자(약 400명) |
| authored-saul-nob-massacre | saul, ahimelech, doeg | 놉의 제사장들(85인), 놉의 남녀와 아이들 |
| authored-david-en-gedi-saul | david, saul | 사울의 택한 사람 삼천, 다윗의 사람들 |
| authored-samuel-ramah-death | david | 온 이스라엘 무리(애곡) · 사무엘은 죽어 장사됨(25:1) — 장면 인물은 바란 광야로 떠나는 다윗(명세 figures) |
| authored-david-ziklag-base | david, achish | (없음) |
| authored-saul-endor-medium | saul-old, endor-medium, samuel(영으로 등장) | 사울의 두 신하 |
| authored-saul-gilboa-death | saul-old, jonathan, saul-armor-bearer | 블레셋 사람들, 길르앗 야베스 장사들 |
| authored-david-hebron-king-judah | david-prime | 유다 사람들 |
| authored-david-gibeon-battle | joab, abner | 다윗의 신복들, 이스보셋의 신복들, 소년 24인 |
| authored-david-jerusalem-conquest | david-prime | 여부스 사람들 |
| authored-david-ark-jerusalem | david-prime | 온 이스라엘 족속 |
| authored-david-nathan-covenant | david-prime, nathan | (없음) |
| authored-solomon-jerusalem-birth | david-prime, bathsheba, nathan | (없음) |
| authored-david-mahanaim-exile | david-elder, absalom | 모든 이스라엘 사람(압살롬 편) |
| authored-david-returns-jerusalem | david-elder, shimei | 유다 족속 |
| authored-solomon-gihon-anointing | solomon, nathan, zadok | 브나야, 그렛·블렛 사람, 모든 백성 |
| authored-solomon-jerusalem-david-charge | david-old, solomon | (없음) |
| authored-solomon-gibeon-dream | solomon | (없음) |
| authored-solomon-jerusalem-two-mothers | solomon, mother-a, mother-b | (없음) |
| authored-solomon-jerusalem-temple-build | solomon | 석수·목수 등 일군들(직접 묘사 없음) |
| authored-solomon-jerusalem-palace | solomon-prime | 바로의 딸(언급만, 미행동) |
| authored-solomon-jerusalem-temple-dedication | solomon | 온 이스라엘의 온 회중 |
| authored-solomon-ezion-geber-fleet | solomon-prime, hiram | 히람의 사공들 |
| authored-solomon-jerusalem-sheba | solomon-prime, sheba-queen | 스바 여왕의 신복들 |
| authored-solomon-jerusalem-apostasy | solomon-old | 이방 여인들(왕비 700·빈장 300) |

## 재현 명령

    VENV=/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python
    cd scripts/canon
    $VENV gen_cast_plate.py <id>                       # 얼굴 후보 4장(시드 11·42·23·5, 7 제외) + A/B(자세 2 × 끔/켬 IP 0.25, 얼굴 = seed 11)
    $VENV gen_cast_plate.py <id> --face-seed 42 --ab-only   # 사용자가 다른 얼굴을 고르면 A/B 3장만 다시
    $VENV gen_cast_plate.py <id> --label b            # 문구를 고친 뒤 재시도(라벨로 구분, 상한 문구 3종 × 시드 4)
    python3 approve_cast.py <id> --seed 11 --anchor off --why "…"   # 사람 판정을 정본에 기록(plate·frozen·FROZEN.md) · 보류는 --hold "사유"

산출물(`.forge/reports/canon-pilot/cast/`): `<id>-faces.png`(후보 4 + 우상단 머리 크롭) · `<id>-ab.png`(위 끔 / 아래 켬) ·
`<id>/<label>-*.png`(판 원본·얼굴 크롭) · `<id>/<label>-meta.json`(문구·토큰·잉크·몸 상자·얼굴 상자).

판정은 **사람 육안**(정체성은 기계가 못 잰다). 잉크(lum<0.55 비율, judge_scene C4 산식)는 참고치. 사람이 고른 결과는
`cast/<id>.json`의 `plate`(`seed`·`anchor`·`ipScale`·`approved`·`approvedOn`)에 적고, 얼굴 크롭을 `frozen/<id>.png`로 복사하며
`frozen/FROZEN.md`에 선택 근거 행을 남긴다. 켬/끔 차이가 없으면 앵커는 뺀다(ADR `260825-013557` — 대조군이 통과하면 무정보).

실측(2026-09-04, 다윗 소년): 판 1장 54~94초(스왑 5GB 사용 상태) · 인물당 7장 ≈ 9분 · 26명 ≈ 3~4시간.

## 3/7 추가 인물 (2026-09-04)

- `zadok` 제사장 사독 — `authored-solomon-gihon-anointing`(왕상 1:39 「제사장 사독이 … 기름 뿔을 가져다가 솔로몬에게 기름을 부으니」). 저작자가 나단으로 대체했던 것을 scripture-reviewer가 잡아 정본 추가. seed 11 · 앵커 켬(사용자).
- `shieldman` 방패 든 자 — 삼상17 명세의 cast 존재 검사용. v41 봉인본 문구·시드 고정, 36장면 미등장 → 보류 기록.

## 판정 결과 (2026-09-04, 폰 판정 페이지 3회)

- **승인 26 / 보류 1(골리앗)**. 승인 전원 **앵커 켬**(IP 0.25) — 사용자 결정. ADR `260904-055320` 「되돌리기 조건」(켬/끔 차이 0이면 절차 단순화)의 반대 방향이라,
  장면 4~7/7에서 앵커가 톤·지물을 깨는 사례가 쌓이면 인물별로 끔으로 되돌린다(`plate.anchor`).
- 문구 개정: 요압(b, 아브넬과 동일 문구였음) · 스바 여왕(b, 오타+시대 복식) · 골리앗(b·c, 중세 느낌 → 보류) · 요나단(b, 요압과 동일 얼굴). 두 여인 → `mother-a`/`mother-b`.
- 얼굴 시드: 11이 19명, 42가 5명(다윗·다윗 노년·솔로몬·밧세바·히람), 5가 2명(아기스·아히멜렉), 23이 1명(요압).
- 골리앗 보류 사유는 `cast/goliath.json` `plate.approved`. 삼상17 전용 인물이라 36장면 미사용.
- 판정 페이지 결정 원본: `.forge/scratch/cast-review-pass{1,2,3}.json`.

## cast-vocab-2 필드 표 (task 352, 2026-10-15)

cast-vocab-1 필드(`age`·`hair`·`beard`·`headwear`·`build`·`costume` 등)는 **값을 그대로 둔다** — 장면 파생이 읽는 필드라서다.
vocab-2는 두 층을 **더한다**. 값은 프롬프트에 바로 쓰는 영문, 근거는 `_why`의 한국어(정본). 근거 키는 `card.<필드>`·`face.<필드>`.
기존 필드와 **모순되는 값은 넣지 않는다**(더 구체화만). 기존 값 자체를 바꿔야 하면 `cast/APPEARANCE-VERSES.md` 「2/2로 미룰 값」 절에 적는다.

### 카드 층 `card` — 투어 카드(머리 ≈ 30px)에서도 보이는 특징

| 필드 | 모양 | `class` 허용값 | `text` 예 |
|---|---|---|---|
| `heightRel` | 문자열(허용값 중 하나) | `child` · `short` · `average` · `tall` · `towering` | — |
| `ageBand` | `{class, text}` | `child` · `youth`(10대) · `young`(20대) · `prime`(30대) · `middle`(40~50대) · `elder`(60대~) | `in his 40s, deep forehead lines` |
| `beardVolume` | `{class, text}` | `none` · `stubble` · `trimmed` · `full` · `long` | `close-trimmed dark beard, jawline visible` / `thick beard reaching the chest` |
| `silhouette` | `{class, text}` | `slight` · `lean` · `average` · `broad` · `heavy` · `giant` | `broad shoulders, thick barrel torso` |
| `headOutline` | `{class, text}` | `bare` · `headwrap` · `turban` · `veil` · `shawl` · `diadem` · `helmet` | `bare head, tight dark curls close to the skull` |
| `costumeColor` | `{class, text}` | `red` · `brown` · `white` · `blue` · `purple` · `black` · `gold` · `undyed` | `deep red wool tunic, dark brown belt` |

- **구별 규칙**: `cast/CAST.md` 역표의 한 정차지에 함께 나오는 두 인물은 위 6필드 중 **2개 이상에서 `class`가 다르다**(`heightRel`은 값 자체).
- **값 규칙(정도만 말하는 낱말 금지)**: `ageBand`·`beardVolume`·`silhouette`의 `text`는 그림을 강제하는 모양을 말한다. 아래 금지 낱말과 관사·전치사만으로 된 `text`는 받지 않으며, 금지 낱말을 빼고도 내용어가 **2개 이상** 남아야 한다.
  금지 낱말: `short` `tall` `long` `big` `small` `large` `little` `old` `young` `thick` `thin` `very` `quite` `average` `normal` `medium` `some` `slightly` `rather` `fairly`
- 수염이 없는 인물(여성·소년·수염 없는 청년)은 `beardVolume` = `{"class": "none", "text": "없음"}`. 이때만 `text` 「없음」을 허용한다.

### 얼굴 층 `face` — 정본 초상·확대 장면용

| 필드 | 내용 |
|---|---|
| `faceShape` | 얼굴형(긴·네모·둥근·달걀, 광대·턱선) |
| `eyes` | 눈 모양·크기·색·눈매 |
| `nose` | 코 모양 |
| `mouth` | 입·입술 |
| `skin` | 피부 빛·결(본문 「붉다」 등 근거가 있으면 근거로) |
| `brows` | 눈썹 |
| `marks` | 흉터·주름·표식 — 없으면 `none` |

### 근거 규칙 (task 353에서 단계 표시로 바꿈)

- 위 13필드, 기존 외모 필드(`age`·`hair`·`beard`·`headwear`·`build`·`costume`), 신분 `role`은 모두 `_why`를 갖는다.
- **`_why`는 근거 단계 표시로 시작한다(사용자 2026-10-15).** 표시는 *그 값을 무엇이 받치느냐*로 정한다.
  - `[직접] 구절 「인용」` — 본문이 그 인물의 그 외모·신분을 직접 말한다.
  - `[추론] 구절 「인용」 — 추론 한 줄` — 본문의 다른 사실(즉위 나이·재위 연수 → 나이, 신분·민족·직업 → 복식·체격)에서 끌어낸다.
  - `[저작](이유)` — 위 둘이 없을 때 시대·지역 고증이나 구분 목적으로 정한다. 괄호 안 이유는 4자 이상이고 「본문 밖」「저작자 정함」만으로 쓰지 않는다. 구절이 일부만 받치면(「아름답다」만 말하고 얼굴형은 정함) `[저작]`이다.
- 구절 표기(`삼상 16:12 「…」`)는 `data/bible/verses.json`에 있는 절로 풀려야 하고, 인용은 그 절 원문에서 **글자 그대로 복사**한다(c2).
- **성품 낱말은 정의에 넣지 않는다.** 행적·성품에서 유추한 인상은 장면 `figures[].expression`이 그 순간에만 맡는다 — 삼상 16:7 「사람은 외모를 보거니와 나 여호와는 중심을 보느니라」. 얼굴 층 값과 카드 층 `text`에 금지: `cold` `cruel` `hard` `harsh` `wicked` `evil` `sly` `cunning` `menacing` `sinister` `kind` `gentle` `wise` `noble` `arrogant` `proud` `haughty` `shifty` `pleading` `trembling` `tense` `anxious` `fierce` `stern` `serene` `innocent` `calm` `steady` `composed`.
- **신분 `role`**: 영어 신분 명사 하나(`king` `queen` `prince` `priest` `prophet` `commander` `soldier` `warrior` `shepherd` `servant` `medium` `mother` 등). 성별은 넣지 않는다 — 장면 문구 파생(`derive_scene.cast_describe`)이 `sex`와 카드 `ageBand`로 성별 명사(man·woman·boy·girl)를 맨 앞에 붙인다.
- **전체 구별 규칙**: 동석 인물끼리(위 구별 규칙)뿐 아니라 **29명 전체 쌍**에서 카드 층 `class`가 2개 이상 다르다. 같은 사람의 생애 단계 쌍(david-boy·david·david-prime·david-elder·david-old, saul·saul-old, solomon·solomon-prime·solomon-old)은 일부러 닮게 하므로 뺀다. 가를 때는 `[저작]` 필드만 바꾸고 `[직접]`·`[추론]` 값은 근거가 있으므로 그대로 둔다.
- 얼굴 층의 의미 유사(글자는 달라도 같은 얼굴로 그려질 쌍)는 기계로 못 잰다 — 검토 에이전트가 29명을 나란히 놓고 판정한다(353: 1회차 2쌍 → 3회차 0쌍).
- **정본 그림 없는 id**(task 355에서 나눈 david-prime·david-elder·solomon-prime): `frozen/<id>.png`가 없다. 지금 주 경로(한 장 프롬프트 `derive_scene.whole_prompt`)는 글만 써서 돌지만, 얼굴 그림을 넣는 옛 IP 경로(`gen_staged.py`·`gen_combined.py` 등)는 정본을 그려 승인(`approve_cast.py`)하기 전까지 이 id를 못 쓴다.
- 구절 수집 원천은 `cast/APPEARANCE-VERSES.md`(인물 · 구절 · 개역한글 원문 · 말하는 특징).
- 검사: `cd scripts/canon && python3 check_cast_v2.py` (정의를 고칠 때마다 돌린다). (f) 단계 표시·`role` · (g) 성품 낱말 · (h) 전체 구별이 353에서 더해졌다.
