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
