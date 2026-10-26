# SPEC-JUDGE — 두 겹 판정 1/3: 명세 판정자 · 이상한 점 판정자 (task 378)

## 고정 절 (2026-10-20 — 두 판정자를 한 번도 돌리기 전에 적음)

task 376 회고: 품질의 천장은 명세다. 그림 판정자(J1)는 명세에 충실했고, 명세가 성경보다 빈약했다. 그래서 두 판정자를 만든다.

- **명세 판정자**(`batch/judge_spec.py`) — 그림 전에 명세를 성경 앞뒤 문맥에 비춘다.
  - 입력: 명세 JSON의 한국어 칸 전부(`stages`·`regions`·`judge` 제외) + `derive_scene.route_prompt`의 영문 파생 문구 + `data/bible/verses.json`에서 **순간 절이 든 장 전체**의 `textKo`. `verses.range`가 장을 넘으면 그 장들 전부를 넣는다. 평행 본문(역대기)은 넣지 않는다.
  - 모델: `claude -p --model opus`(구독). 사람 메모는 프롬프트에 넣지 않는다(블라인드).
  - 지적 형식: `{kind: 빠짐|축약|어긋남|순간, verse, quote, field, 제안}`.
    - 빠짐·축약·순간: `quote`가 그 절(`verse`, 범위면 이어 붙인 절) `textKo`의 부분 문자열이어야 한다(띄어쓰기 무시). 아니면 그 지적은 버리고 「지어낸 인용」으로 센다. 절이 입력 창(넣은 장) 밖이어도 지어낸 인용이다.
    - 어긋남(명세 칸끼리·파생 문구): `quote` 대신 `field`에 칸 두 개를 적는다. 칸이 둘 미만이면 지어낸 인용으로 센다.
- **이상한 점 판정자**(`batch/judge_items.py` 머리말 `o1`, 문항 `oddity`) — 그림을 명세 글 전체에 비춘다.
  - J1 문항·머리말·`SYSTEMS`는 그대로 둔다. 이상한 점은 **따로 부르는 새 호출**이다.
  - 입력: 그림 + 인물 몸 크롭 + 명세 한국어(순간·뜻·인물 역할·자세·몸짓·지물·무리·배경·관계).
  - 묻는 것: 신원(누가 누구인지 모호)·역할(행동 주체가 바뀜)·이물(시대에 없는 물건·건물·덧붙은 사람)·상태(명세의 상태와 어긋남, 예: 싸여야 할 것이 드러남) 어긋남과 가드 결함(손가락·두 겹·테두리·글자). 모호하면 「있음」.
  - 모델: Sonnet(J1과 같음). 답 「맞음」 = 이상한 점 없음, 「틀림」 = 있음(기존 채점 틀을 그대로 쓰려고).

### 정답·변이·라벨·규칙 (기계가 이 블록을 읽는다 — `judge_spec.fixed()`)

- 명세 판정자 정답 = 사람 메모의 명세 쪽 5항목. 기브온 차림은 성경에 없는 시대 고증이라 정답에서 빼고 S4에서 메모로 고친다.
- 맞춤 = 지적의 `kind`가 `kinds` 안 **그리고** (지적 `verse`가 `verses`와 겹침 **또는** `fields`가 있으면 지적 `field`에 두 칸 이름이 모두 들어 있음) **그리고** `words` 정규식이 지적의 `quote`와 `제안`을 이어 붙인 글에 맞음. 버려진 지적(지어낸 인용)은 맞춤에 쓰지 않는다.
- 측정만(규칙 아님): 길보아 병기 든 자 지물↔자세 어긋남, 놉 보자기 상태.
- 변이 대조 = 「쓸 만함」 5장면에서 순간 절에 근거한 요소 하나씩을 지운 사본(`samples/spec-judge/mutants/`, `scenes/`는 건드리지 않음). `forbid` 낱말이 사본의 어떤 칸(`verses.quotes`·`stages[].neg` 제외)에도 남지 않아야 한다(테스트가 단언).
- 이상한 점 정답 = 사람 라벨. 있음 = 376 블라인드 가드 「틀림」 10칸 + 놉 s202·s303(칼날 드러남 — 사람 지물 틀림·메모). 베들레헴 s11·s23(기름 붓는 이 모호)은 가드 틀림에 이미 들어 있다. 없음 = 368~376 사람 가드 「맞음」 칸 중 그 장면에 사람 메모가 없는 칸(368은 가드 문항 없음).
- `판정(명세 판정자):` — 정답 잡기 ≥ 4/5 **그리고** 변이 잡기 ≥ 4/5 **그리고** 지어낸 인용 ≤ 지적의 10%(14장면 + 변이 5) → 「채택」, 아니면 「미채택」. 미채택이면 S4는 사람 메모만으로 고치고, 재실행은 참고로만 적는다.
- `판정(이상한 점):` — 있음 잡기 ≥ 0.8 **그리고** 베들레헴·놉 각각 1시드 이상 잡음 **그리고** 없음 통과 ≥ 0.75 → 「채택」(후보 규칙 결합 켬), 아니면 「미채택」(끔). 같은 칸의 J1 가드 성적을 비교값으로 함께 적는다. 답 없음(실패 호출)은 라벨 반대로 센다.

```json fixed
{
  "truth": [
    {"id": "a", "scene": "authored-david-gibeon-battle", "what": "기브온 겨루기 — 열두 명씩 맞붙음", "kinds": ["순간", "빠짐"], "verses": ["2:14", "2:15", "2:16"], "words": "열두|겨루|싸우"},
    {"id": "c", "scene": "authored-david-mahanaim-exile", "what": "마하나임 — 함께한 백성", "kinds": ["빠짐", "축약"], "verses": ["17:22", "17:26", "17:27", "17:28", "17:29"], "words": "백성|무리|함께"},
    {"id": "d", "scene": "authored-david-returns-jerusalem", "what": "요단 귀환 — 유다 사람들이 왕을 건네려 맞음", "kinds": ["빠짐", "축약"], "verses": ["19:15", "19:16", "19:17", "19:18"], "words": "건네|나룻배|맞|도와"},
    {"id": "e", "scene": "authored-samuel-bethlehem-david-anointing", "what": "베들레헴 — 형제들 가운데", "kinds": ["빠짐", "어긋남"], "verses": ["16:10", "16:11", "16:13"], "fields": ["moment.why", "crowds"], "words": "형제"},
    {"id": "f", "scene": "authored-david-gath-achish", "what": "가드 — 침이 수염에", "kinds": ["축약", "어긋남"], "verses": ["21:13"], "fields": ["moment.why", "figures"], "words": "수염"}
  ],
  "measure": [
    {"id": "g", "scene": "authored-saul-gilboa-death", "what": "길보아 — 병기 든 자 지물↔자세", "kinds": ["어긋남"], "verses": ["31:4"], "fields": ["prop", "pose"], "words": "칼"},
    {"id": "n", "scene": "authored-david-nob-priests", "what": "놉 — 보자기 상태", "kinds": ["빠짐", "축약", "어긋남"], "verses": ["21:9"], "words": "보자기|싸"}
  ],
  "mutants": [
    {"id": "m1", "scene": "authored-david-ark-jerusalem", "what": "6:15 「나팔을 불고」 지움", "kinds": ["빠짐", "축약"], "verses": ["6:15"], "words": "나팔", "forbid": ["나팔", "trumpet"]},
    {"id": "m2", "scene": "authored-david-hebron-king-judah", "what": "2:4 「기름을 부어」 지움", "kinds": ["빠짐", "축약", "순간"], "verses": ["2:4"], "words": "기름", "forbid": ["기름", "oil"]},
    {"id": "m3", "scene": "authored-david-nathan-covenant", "what": "나단이 말씀을 전함(7:5·7:17) 지움", "kinds": ["빠짐", "축약", "순간"], "verses": ["7:4", "7:5", "7:8", "7:12", "7:13", "7:14", "7:15", "7:16", "7:17"], "words": "말|전하|전함|고하", "forbid": ["말한다", "speaking", "전하는", "전하다"]},
    {"id": "m4", "scene": "authored-david-ziklag-base", "what": "27:6 「시글락을 그에게 주었으므로」 지움", "kinds": ["빠짐", "축약", "순간"], "verses": ["27:6"], "words": "주었|주어|준|내어|가리", "forbid": ["내어 줌", "내어 주", "gesturing"]},
    {"id": "m5", "scene": "authored-david-ramah-samuel", "what": "19:18 「사울이 자기에게 행한 일을 다 고하였고」 지움", "kinds": ["빠짐", "축약", "순간"], "verses": ["19:18"], "words": "고하|행한 일|알리|말", "forbid": ["고하", "tells", "말을 듣"]}
  ],
  "oddity": {
    "pos": ["376:authored-david-gibeon-battle:7", "376:authored-david-gibeon-battle:5", "376:authored-david-hebron-king-judah:101", "376:authored-david-mahanaim-exile:11", "376:authored-david-mahanaim-exile:101", "376:authored-david-returns-jerusalem:7", "376:authored-david-returns-jerusalem:101", "376:authored-samuel-bethlehem-david-anointing:11", "376:authored-samuel-bethlehem-david-anointing:23", "376:authored-david-gath-achish:202", "376:authored-david-nob-priests:202", "376:authored-david-nob-priests:303"],
    "neg": ["369:authored-saul-gilgal-amalek:11", "369:authored-saul-gilgal-amalek:42", "369:authored-saul-gilgal-amalek:7", "369:authored-saul-gilgal-amalek:23", "369:authored-saul-gilgal-amalek:5", "369:authored-saul-gilgal-amalek:101", "369:authored-saul-gilgal-amalek:202", "369:authored-saul-gilgal-amalek:303", "370:authored-david-gibeah-harp:11", "370:authored-david-gibeah-harp:42", "370:authored-david-gibeah-harp:7", "370:authored-david-gibeah-harp:23", "370:authored-david-gibeah-harp:5", "370:authored-david-gibeah-harp:101", "370:authored-david-gibeah-harp:202", "370:authored-david-gibeah-harp:303", "370:authored-saul-nob-massacre:11", "370:authored-saul-nob-massacre:42", "370:authored-saul-nob-massacre:7", "370:authored-saul-nob-massacre:23", "370:authored-saul-nob-massacre:5", "370:authored-saul-nob-massacre:101", "370:authored-saul-nob-massacre:202", "370:authored-saul-nob-massacre:303", "376:authored-david-ark-jerusalem:5", "376:authored-david-ark-jerusalem:303", "376:authored-david-hebron-king-judah:5", "376:authored-david-nathan-covenant:11", "376:authored-david-nathan-covenant:303", "376:authored-david-ziklag-base:11", "376:authored-david-ziklag-base:5", "376:authored-david-ramah-samuel:11", "376:authored-david-ramah-samuel:303"],
    "must": ["authored-samuel-bethlehem-david-anointing", "authored-david-nob-priests"]
  },
  "rules": {
    "spec": {"truth_min": 4, "mutant_min": 4, "fabricated_max": 0.10},
    "oddity": {"catch_min": 0.8, "pass_min": 0.75}
  }
}
```

- 대상 14장면(블라인드 교정) = `params.VERSE_ELEMENT_SCENES`. 남은 23장면은 지적을 기록만 한다(다음 과제 거리).
- 고친 장면(S4) = 기브온·마하나임·요단 귀환·베들레헴·가드·놉·시온 산성·엔돌·길보아. 놉은 지적이 없으면 고치지 않는다. 고친 뒤 `judge_spec.py run --only <9장면> --key after<N>`(최대 2회)에서 빠짐·축약·어긋남 0을 본다(순간은 세지 않음).

## 결과

<!-- spec-judge:begin -->
### 명세 판정자 (14장면 블라인드 + 변이 5, Opus)

판정(명세 판정자): 미채택 — 정답 잡기 1/5 · 변이 잡기 5/5 · 지어낸 인용 0/78 (0.0%)

| 항목 | 내용 | 잡음 |
|---|---|---|
| a | 기브온 겨루기 — 열두 명씩 맞붙음 | 아니오 |
| c | 마하나임 — 함께한 백성 | 예 |
| d | 요단 귀환 — 유다 사람들이 왕을 건네려 맞음 | 아니오 |
| e | 베들레헴 — 형제들 가운데 | 아니오 |
| f | 가드 — 침이 수염에 | 아니오 |
| g (측정만) | 길보아 — 병기 든 자 지물↔자세 | 아니오 |
| n (측정만) | 놉 — 보자기 상태 | 아니오 |
| m1 (변이) | 6:15 「나팔을 불고」 지움 | 예 |
| m2 (변이) | 2:4 「기름을 부어」 지움 | 예 · 원본에서도 맞음 |
| m3 (변이) | 나단이 말씀을 전함(7:5·7:17) 지움 | 예 · 원본에서도 맞음 |
| m4 (변이) | 27:6 「시글락을 그에게 주었으므로」 지움 | 예 |
| m5 (변이) | 19:18 「사울이 자기에게 행한 일을 다 고하였고」 지움 | 예 · 원본에서도 맞음 |

지적 종류별: 빠짐 28 · 축약 22 · 어긋남 22 · 순간 6 · 답 없음 0

### 이상한 점 판정자 (라벨 있음 12 · 없음 33, Sonnet)

판정(이상한 점): 미채택 — 있음 잡기 12/12 (100.0%) · 없음 통과 11/33 (33.3%) · anointing 2시드 · priests 2시드

비교값 — 같은 칸의 J1 가드: 있음 잡기 9/12 · 없음 통과 27/33
놓친 있음: 없음
잘못 잡은 없음: 369:authored-saul-gilgal-amalek:7, 369:authored-saul-gilgal-amalek:5, 369:authored-saul-gilgal-amalek:101, 370:authored-david-gibeah-harp:11, 370:authored-david-gibeah-harp:42, 370:authored-david-gibeah-harp:23, 370:authored-david-gibeah-harp:5, 370:authored-david-gibeah-harp:101, 370:authored-david-gibeah-harp:202, 370:authored-david-gibeah-harp:303, 370:authored-saul-nob-massacre:11, 370:authored-saul-nob-massacre:42, 370:authored-saul-nob-massacre:7, 370:authored-saul-nob-massacre:23, 370:authored-saul-nob-massacre:101, 370:authored-saul-nob-massacre:202, 370:authored-saul-nob-massacre:303, 376:authored-david-ark-jerusalem:5, 376:authored-david-ark-jerusalem:303, 376:authored-david-nathan-covenant:303, 376:authored-david-ziklag-base:11, 376:authored-david-ramah-samuel:11
<!-- spec-judge:end -->

## 해설 · 고친 장면 (2026-10-20 — 위 결과 절은 `judge_spec.py score`가 쓴다)

### 명세 판정자 — 미채택의 내용
- 근거는 믿을 만하다: 지어낸 인용 0/78, 변이 5/5(그중 m2·m3·m5는 원본 답에서도 같은 조건이 맞아 분해능 증거로는 약함).
- 그러나 사람이 본 빈칸을 못 짚는다(정답 1/5 — 마하나임만). 놓친 쪽의 실제 지적: 기브온은 「소년들이 무리·영문에 없음」(2:14 빠짐)·「신복들이 능선이 아니라 못가」(2:13)를 짚었으나 순간을 2:15로 옮기자는 말은 없음, 요단 귀환은 나룻배를 `순간` 종류로만 냄(맞춤 종류 밖), 베들레헴은 형제들 대신 「사무엘 단계가 뿔을 들고만 있음」을 짚음, 가드는 수염 대신 방향·신하 시선을 짚음.
- 즉 판정자는 **명세 칸끼리·영문과의 어긋남과 근거 인용**에는 강하고, **사람이 그림을 보고 느낀 빈칸(동행·도움·겨루는 몸짓)을 순간 고르기 차원에서 찾는 일**에는 약하다. 고정 절대로 S4는 사람 메모(+그릴링에서 정한 되돌림 원인)만으로 고쳤다.
- 남은 23장면 지적 118건(빠짐·축약·어긋남·순간)은 `samples/spec-judge/metrics.json` `runs.rest`에 기록만 했다 — 다음 과제 거리. 반복해 나온 축: 다윗·솔로몬의 나이(「lean young man」 vs 본문 시점 — task 355 생애 단계 분할 거리), 왕의 표지 없음, 무리의 원경 배치.

### 고친 장면 (S4) — 2/3 재생성 집합
고친 8장면 중 **파생 프롬프트가 바뀐 7장면**이 재생성 대상이다. 가드는 한국어 자세 칸(「침을 수염에」)만 고쳐 파생 문구가 같다 — 같은 시드면 같은 그림이라 재생성에서 뺀다(376 s202 「쓸 만함」 그대로). 놉은 명세 판정자 보자기 지적도 사람 메모의 명세 쪽 결함도 없어 고치지 않았다(칼날이 드러난 것은 그림 쪽).

```json regen
["authored-david-gibeon-battle", "authored-david-mahanaim-exile", "authored-david-returns-jerusalem", "authored-samuel-bethlehem-david-anointing", "authored-david-jerusalem-conquest", "authored-saul-endor-medium", "authored-saul-gilboa-death"]
```

| 장면 | 고친 것 | 근거 |
|---|---|---|
| 기브온 | 순간 2:13-14 → 2:15-16 전반(소년 열둘씩 지휘관들 앞 가까이 맞서 머리를 잡음) · 양편 신복을 능선 원경 → 각 지휘관 뒤 못가 · 두 지휘관 차림(생양모 튜닉·가죽 비늘 갑옷·맨머리) | 메모 「12 vs 12인데 너무 멀리」「싸우려는 제스처 없음」「옷이 시대를 반영 못 함」, 2:13·2:15-16 |
| 마하나임 | 함께한 모든 백성 무리(지친 행렬)를 다윗 바로 뒤에 | 메모 「무리랑 같이」, 17:22·17:29 |
| 요단 귀환 | 유다 사람들을 원경 → 강가에서 왕을 가까이 맞음 · 나룻배가 건너옴 | 메모 「나룻배를 준비하거나 안내」, 19:15-16·19:18 |
| 베들레헴 | 형제 일곱을 `crowds`에 · 다윗 바로 뒤 한 줄 · 뿔은 사무엘만(사무엘 단계를 「들고 섬」→「기울여 부음」) · 이새는 떨어져 섬 | 메모 「사무엘 옆 사람은 누구며? 사람이 기름을 붓고 있음」, moment.why↔crowds 어긋남, 16:10·16:13 |
| 가드 | 인물 자세 칸 「침을 흘린다」→「침을 수염에 흘린다」 | moment.why↔figures 어긋남, 메모 「침을 수염까지」, 21:13 |
| 시온 산성 | 종자들을 「far away」 원경 → 다윗 바로 뒤 같은 언덕 | 되돌림 원인(J1 이유 8/8 「종자들이 멀리 성벽 쪽」) |
| 엔돌 | 동행 둘을 수염 없는 젊은 종으로(문 가) · 사무엘은 허리 위만 땅에서 올라옴 | 되돌림 원인(J1 「사울이 두 겹·누가 사울인지 모호」, 「사무엘이 그냥 서 있음」) |
| 길보아 | 두 사람 지물 `a sword` → `a sheathed sword` · 「칼날이 칼집에」 · 뽑은 칼 부정어 | 되돌림 원인(8/8 칼을 뽑음 — 지물 칸↔자세 칸 어긋남), 31:4 |

- `scripture-reviewer` 판정(읽기 전용): 맞음 2(가드·길보아) · 약함 5 · 어긋남 1(요단 귀환 — 나룻배를 붙잡는 일을 표시 없이 본문 근거 칸에, 「길갈로 오니라」 방향 뒤집힘). 어긋남은 고쳤고(19:16 인용 더함·19:17 순간 밖 칸·「배를 붙잡음 본문 밖 · 저작자 정함」·「길갈에 모였다가 강가로 내려옴」), 약함의 표시 누락(배치·몸짓의 「본문 밖 · 저작자 정함」)도 붙였다. 세 순간 고르기(기브온 2:15-16 전반·요단 19:18·마하나임 17:22)는 본문 흐름에 맞다는 판정.
- 고친 뒤 `check_scenes` 37/37 · 구절 요소 14/14 · 512토큰 넘침 0.

### DoD 6 재실행 — 참고(명세 판정자 미채택)
빠짐·축약·어긋남 수(순간 제외), 블라인드 → after1 → after2. 0이 되지 않았다 — 판정자는 고칠 때마다 새 세부(아비새·아사헬, 시므이·베냐민 일천, 왕의 나이·표지, 장로들)를 더 낸다. after1에서 나온 **내가 만든 자체 모순**(베들레헴 이새 「지팡이」↔「빈손」, 기브온 「나아감」↔「머리를 잡음」)과 메모에 이어지는 지적(사무엘 단계 「뿔을 들고만 섬」, 기브온 신복 원경)만 after2 전에 고쳤다. 나머지는 다음 과제 거리.

| 장면 | 블라인드 | after1 | after2 |
|---|---|---|---|
| 마하나임 | 4 | 1 | 0 |
| 기브온 | 5 | 4 | 6 |
| 요단 귀환 | 3 | 6 | 7 |
| 베들레헴 | 3 | 6 | 6 |
| 놉(안 고침) | 3 | 4 | 4 |
| 가드 | 4 | 4 | 4 |
| 엔돌 | 3 | 2 | 1 |
| 시온 산성 | 3 | 3 | 5 |
| 길보아 | 5 | 4 | 6 |

### 이상한 점 판정자 — 미채택의 내용 (S5)
- 「있음」은 다 잡는다(12/12, 베들레헴·놉 각 2시드) — J1 가드(9/12)보다 낫다. 이유도 사람 메모와 같은 곳을 짚는다: 베들레헴 s23 「사무엘은 뿔을 들고 서 있을 뿐, 뒤의 회색 옷 남자가 뿔을 다윗 머리 위로」, 놉 s202 「칼을 이미 반쯤 뽑아 칼날이 보임」, 엔돌 s11 「왼쪽 회색 수염 노인이 사무엘과 비슷해 누가 누구인지」, 법궤 s11 「고층 빌딩 스카이라인」.
- 그러나 「없음」 통과 11/33(J1 가드 27/33). 「모호하면 있음」이 명세의 세부(겉옷 걸침·눈 감음 정도·수금 크기)까지 이상한 점으로 끌어온다 — 요소 문항이 이미 묻는 것을 다시 묻는 셈.
- 사람이 놓쳤을 수 있는 것: 「없음」 라벨인 법궤 s5에 「현대식 고층 건물과 첨탑·노란 점선 차선」(376 「쓸 만함」으로 고른 장). 라벨을 바꾸지는 않는다(규칙 사후 변경 금지) — 3/3 이후 법궤 승인본 재확인 거리.
- 측정(규칙 아님): 결합했다면 376 14장면 중 11장면이 「이상한 점」 되돌림(장면 뜻 되돌림 3은 그대로) — 법궤·기브온·마하나임·나단·요단·베들레헴·가드·놉 등. 후보가 남는 곳은 헤브론 s5(그대로)·시글락 s5→s7·라마 s11→s202. 결합 기본값은 **끔**(`judge_learn.oddity_on()`이 이 판정을 읽음).
- 주의: 376 112장 측정 run(`t376/O1`)은 S4 명세 고침과 시간이 겹쳐 일부 장면은 고친 명세 글로 물었다. 판정 라벨 묶음(`oddity/O1`, 45장)은 고침 전에 끝났다.

### 후보 규칙 결합 (S6)
- `judge_learn.pick_candidates(answers, oddity)` — oddity를 주면 후보 = 장면 뜻 맞음 **그리고** 이상한 점 없음, 되돌림 사유(장면 뜻 | 이상한 점)를 `reason`에. `candidates()` 기본은 `oddity_on()`(지금 끔). `cand <과제> --oddity|--no-oddity`로 강제.
- 끔이면 376·370·372 후보 결과가 고치기 전 코드(HEAD)와 바이트 단위로 같음(JSON 비교).
- `make_cand_page`는 `reason`이 있을 때만 되돌림 화면 문구를 「장면 뜻이 맞은 장도 모두 이상한 점」으로 바꾼다. `judge_items.py predict`는 이제 J1·J1-prop와 함께 이상한 점(O1)도 기록한다(결합 끔이어도 기록 — 2/3 측정용).
