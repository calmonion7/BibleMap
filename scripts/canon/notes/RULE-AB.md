# 규칙 후보 다른 장면 A/B (task 423, 후속 fu-1592d4713d06)

PROMPTING 30의 두 결과(솔로몬 출생 한 장면 8시드 근거)가 다른 장면에서도 나오는지, 같은 시드로 **한 낱말만 바꾼 두 장**으로 본다.
A = 지금 파생 그대로 · B = 규칙을 적용한 문구. 판정은 4장을 **한 묶음**으로, 장면마다 **전 문항**(바뀐 낱말 문항만이 아니라), 장마다 **5표**
(원장 judge.single-image-reps). 본문 밖 [저작] 세부 문항은 `record`(답만 적고 통과 셈 밖 — judge.authored-detail-record).

- **royal** — 나단 언약(삼하 7:1-17, 판 경로 명세). 판 문구의 다윗(「an ancient Israelite lean young man」 — 생애 단계 나눔 전 낡은 말)을
  한 장 모드와 같은 카드 서술(`derive_scene.cast_describe(david-prime)` — 카드 차림 「royal robe」 포함)로 바꾼 것이 A, 거기서 「royal 」만 뺀 것이 B.
  나머지 판 문구는 파생 그대로 · 가이드 없음(이 명세에 guide 칸이 없음).
- **back-wall** — 두 여인의 재판(왕상 3:16-28, 한 장 모드 · 방 바탕 가이드 `backdrop: room` · 스텝별). A = route_prompt 그대로,
  B = 벽 문구 뒤에 출생 곁 장면과 같은 「the back wall drawn block by block like the side walls」.

도구: `batch/rule_ab.py gen|judge|report` — 고정 절을 읽는다(손으로 옮기지 않음).

```json fixed 423
{"dir": "rule-ab", "seed": 11, "reps": 5,
 "cases": [
  {"id": "royal", "scene": "authored-david-nathan-covenant", "guide": false,
   "a_from": ["an ancient Israelite lean young man", "{cast:david-prime},"],
   "b_from": [" royal robe", " robe"],
   "axis": ["n.david-bare"],
   "qs": [
    {"id": "s.style", "q": "화풍", "what": "미색 종이에 연필로 그리고 색연필로 칠한 동화 그림 화풍인가?"},
    {"id": "s.no-blob", "q": "덩어리", "what": "얼굴·옷 없이 평평한 회색 덩어리나 미완성 실루엣으로 남은 사람·물건이 없나?"},
    {"id": "n.moment", "q": "순간", "what": "선지자 나단이 다윗 앞에서 말씀을 전하고, 다윗이 나단 쪽을 보며 듣는 모습인가?", "verse": "삼하 7:12-16"},
    {"id": "n.two-people", "q": "두 사람", "what": "사람이 화면 왼쪽 다윗과 화면 오른쪽 나단 두 사람뿐인가?"},
    {"id": "n.facing", "q": "마주 봄", "what": "다윗(왼쪽)은 화면 오른쪽 나단을, 나단(오른쪽)은 화면 왼쪽 다윗을 향해 얼굴과 몸을 돌리고 있나?"},
    {"id": "n.nathan-arm", "q": "나단 팔", "what": "나단이 서서 한 팔을 들어 말을 전하는 몸짓을 하나?", "verse": "삼하 7:5"},
    {"id": "n.nathan-staff", "q": "나단 지팡이", "what": "나단이 나무 지팡이를 쥐고 있나?", "record": true},
    {"id": "n.david-sit", "q": "다윗 앉음", "what": "다윗이 앉아 있나?", "record": true},
    {"id": "n.david-robe", "q": "다윗 겉옷 자락", "what": "다윗이 한 손으로 자기 겉옷 자락을 쥐고 있나?", "record": true},
    {"id": "n.david-bare", "q": "다윗 맨머리", "what": "다윗이 관·금띠·머리띠·두건 등 아무것도 쓰지 않은 맨 곱슬머리인가?", "record": true},
    {"id": "n.david", "q": "다윗 모습", "what": "다윗이 짙은 붉은 긴 겉옷을 입은, 다듬은 짙은 수염의 40대 남자인가?", "record": true},
    {"id": "n.nathan", "q": "나단 모습", "what": "나단이 긴 겉옷을 입은 중년 남자인가?", "record": true},
    {"id": "n.place", "q": "백향목 궁", "what": "나무(백향목)로 지은 큰 집 앞의 뜰인가?", "verse": "삼하 7:2"},
    {"id": "n.guard", "q": "가드", "what": "손가락 수 이상, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자 같은 결함이 하나도 없나?"}
   ]},
  {"id": "back-wall", "scene": "authored-solomon-jerusalem-two-mothers", "guide": true,
   "a_from": null,
   "b_from": ["walls of rough stone blocks,", "walls of rough stone blocks, the back wall drawn block by block like the side walls,"],
   "axis": ["t.back-wall", "t.no-halo"],
   "qs": [
    {"id": "s.style", "q": "화풍", "what": "미색 종이에 연필로 그리고 색연필로 칠한 동화 그림 화풍인가?"},
    {"id": "s.no-blob", "q": "덩어리", "what": "얼굴·옷 없이 평평한 회색 덩어리나 미완성 실루엣으로 남은 사람·물건이 없나?"},
    {"id": "t.moment", "q": "순간", "what": "한 여인이 앉은 왕 앞에 서서 애원하고, 다른 여인은 아기를 안고 서 있으며, 왕은 앉아 애원하는 여인을 지켜보는 모습인가?", "verse": "왕상 3:26"},
    {"id": "t.three-people", "q": "세 사람", "what": "사람이 두 여인과 왕 셋뿐인가(안긴 아기는 셈에서 뺌)?"},
    {"id": "t.king-seated", "q": "왕 앉음", "what": "왕(화면 오른쪽)이 나무 자리에 앉아 있나?", "verse": "왕상 2:19 [추론]"},
    {"id": "t.plead", "q": "애원", "what": "가운데 여인이 왕을 향해 애원하는 몸짓인가?", "verse": "왕상 3:26"},
    {"id": "t.plead-hands", "q": "내민 두 손", "what": "가운데 여인이 빈 두 손을 왕 쪽으로 내밀었나?", "record": true},
    {"id": "t.infant", "q": "안은 아기", "what": "화면 왼쪽 여인이 천에 싸인 갓난 아기를 두 팔로 가슴에 안고 있나?", "verse": "왕상 3:20·3:27 [추론]"},
    {"id": "t.facing", "q": "방향", "what": "두 여인은 화면 오른쪽 왕 쪽을, 왕은 화면 왼쪽 여인들 쪽을 향하나?"},
    {"id": "t.sword", "q": "칼", "what": "왕 앞(바닥)에 곧은 칼 한 자루가 있나?", "verse": "왕상 3:24"},
    {"id": "t.king", "q": "왕 모습", "what": "왕이 짙은 푸른 긴 겉옷을 입은 20대 젊은 남자이고 머리에 아무것도 쓰지 않았나?", "record": true},
    {"id": "t.back-wall", "q": "뒷벽 재질", "what": "인물들 뒤 넓은 뒷벽이 옆벽처럼 돌 블록으로 그려졌나(매끈한 회벽이나 빈 면이 아님)?", "record": true},
    {"id": "t.no-halo", "q": "후광 없음", "what": "인물 뒤 벽에 둥근 빛 번짐이나 후광이 없나?"},
    {"id": "t.no-church", "q": "교회 도상 없음", "what": "벽에 스테인드글라스 창이나 성상을 모신 아치 벽감 같은 교회 도상이 없나(드나드는 문·평범한 창은 괜찮음)?"},
    {"id": "t.guard", "q": "가드", "what": "손가락 수 이상, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자 같은 결함이 하나도 없나?"}
   ]}
 ]}
```

**재현 판정**: royal은 A의 `n.david-bare` 다수결 틀림 + B 맞음 · back-wall은 A가 `t.back-wall`·`t.no-halo` 중 하나라도 다수결 틀림 + B 둘 다 맞음.
그리고 B가 A보다 다른 거르기 문항을 둘 넘게 잃지 않음(바꾼 낱말이 다른 것을 무너뜨리지 않음). 눈 확인을 함께 적는다.

## 결과 (2026-10-26, 시드 11 · 4장 한 묶음 · 장마다 5표 · `python3 batch/rule_ab.py report`)

그림: `samples/rule-ab/{royal,back-wall}-{A,B}-s11.png` · 가이드 `guide-back-wall-{1,2}.png` · 답 `samples/rule-ab/metrics.json`(1차 `metrics-v1.json`).

| 사례 | 축 문항 | A(지금) | B(규칙) | 거르기 맞음 A · B | 재현 |
|---|---|---|---|---|---|
| royal (나단 언약) | 다윗 맨머리 | 5/5 | 5/5 | 7/8 · 7/8 | **아니오** |
| back-wall (두 여인) | 뒷벽 재질 · 후광 없음 | 5/5 · 5/5 | 5/5 · 5/5 | 9/12 · 12/12 | **아니오** |

- **royal — 안 나옴**: 「a king … in a long deep red royal robe」 그대로인 A도 맨 곱슬머리(눈 · 5/5). royal은 겉옷에 금 가장자리·무늬만 더함.
  출생의 금띠(PROMPTING 30)는 궁 안에 선 왕 장면에서 나온 것 — 앞뜰에 앉은 왕에선 그 낱말만으로 머리쓰개가 불리지 않았다(한 시드). 원장에 올리지 않고 카드 david-prime 차림도 그대로 둔다.
- **back-wall — 결함 조건이 안 생김**: 방 바탕 가이드(뒷벽 평평한 면)인데도 A의 뒷벽이 이미 돌 블록(5/5)이고 둥근 빛 번짐 없음(5/5).
  B가 칼 자리(1→5)·교회 도상(0→5 — A 오른쪽 창이 스테인드글라스)·가드(0→5 — A 아기 안은 여인 몸 앞 칼집 같은 막대)에서 나았지만, 문구 하나에 구도 전체가 바뀐 한 시드의 흔들림이지 뒷벽이 비어서 생긴 결함이 아니다.
  출생 후광은 아기를 안은 어머니 도상 쪽이었다(PROMPTING 31 — 비킨 구도로 풀림). 원장 derive.wall-material은 넓히지 않는다.
- **1차 판정에서 문항을 나눔**: 처음 「후광 없음」 문항이 「둥근 빛 번짐·후광·아치 벽감」을 한 문항에 묶어 A 1/5 → 기준표대로면 「재현 예」로 나왔으나,
  이유 5개 중 4개가 왼쪽 벽 **아치 문(출입구)**·오른쪽 아치 창이었다(뒷벽 빛 번짐 아님). 원장 judge.authored-detail-record의 「섞였으면 나눔」대로
  후광(빛 번짐)·교회 도상(스테인드글라스·성상 벽감)으로 나눠 4장 전부를 같은 묶음·전 문항으로 다시 물음(위 표가 그 결과).
- **요단(david-elder) 본문 확인**: 삼하 19장 43절에 관 낱말 없음. 다만 12:30 「그 왕의 머리에서 보석 있는 면류관을 취하니 … 다윗이 머리에 쓰니라」가 귀환보다 앞서
  [추론] 근거가 되고, 장면이 `cast_override` headOutline crown(얇은 금관)을 명시 — 「royal」이 원치 않는 머리쓰개를 부르는 경우가 아니라 요단 승인 그림 r6 s101은 그대로.
  override 근거 글은 삼하 1:10(사울의 면류관)만 들고 12:30을 들지 않음 → 후속 후보.
