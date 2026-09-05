# 다윗 투어 36장면 — 명세 검토 표와 규칙 실측

장면 명세는 `scripts/canon/scenes/<id>.json`(한국어가 정본, 영문 프롬프트는 `derive_scene.py`가 파생). 이 표는 사람 관문 —
**GPU 전에 순간·인물·지물·배경을 한 번 훑는 가장 싼 관문**(PROCESS.md 「내용이 틀리면 그림 전체가 다른 장면」). 검토 열은 사람이 적는다.

## 검토 표 (3/7 · 2026-09-04) — 사용자 검토 완료 2026-09-04: 36/36 ✅, 수정 요청 0(폰 검토 페이지, 원본 `.forge/scratch/scene-review-user.json`)

<!-- scene-table:begin -->
| # | 장면 | 순간(절) | 인물(지물) | 배경 한 줄 | 검토 |
|---|---|---|---|---|---|
| 1 | `authored-saul-mizpah-chosen` 사울 — 미스바에서 뽑히다 | 10:23-24 — 뽑힌 사울이 백성 중에 서니 다른 사람보다 어깨 위나 더 크던 순간과 사무엘의 선포를 고정한다(10:23-24) | samuel(a robe corner) · saul(a plain traveling cloak) | 미스바의 넓은 야외 집회 자리, 마른 땅 | ✅ |
| 2 | `authored-saul-jabesh-rescue` 사울 — 야베스 구원 | 11:11 — 새벽에 사울이 삼 대로 나눈 백성을 이끌고 암몬 진영으로 들어서니 나하스의 무리가 무너져 흩어지는 순간을 고정한다 | saul(a sword) · nahash(a siege spear) | 새벽 여명의 들판, 무너지는 진영 천막 | ✅ |
| 3 | `authored-saul-gilgal-coronation` 사울 — 길갈에서 왕이 되다 | 11:15 — 길갈에서 백성이 사울을 왕으로 세우고 화목제단 곁에서 크게 기뻐하는 순간을 고정한다 | samuel(a robe corner) · saul(a plain traveling cloak) | 화목제를 위해 쌓은 돌 제단 · 길갈의 넓은 들 | ✅ |
| 4 | `authored-saul-michmash-battle` 사울 — 길갈에서 사무엘을 기다리지 못하다 | 13:10 — 사울이 번제를 드린 직후 사무엘이 이르러 나가 맞는 순간을 고정한다 | saul(a plain traveling cloak) · samuel(a robe corner) | 미리 쌓은 돌 제단과 피어오르는 번제 연기 · 길갈의 넓은 들 | ✅ |
| 5 | `authored-saul-gilgal-amalek` 사울 — 길갈에서 겉옷자락이 찢어지다 | 15:27 — 사무엘이 돌이켜 떠나려 할 때 사울이 그의 겉옷자락을 붙잡아 찢어진 순간을 고정한다 | saul(a torn robe corner) · samuel(a wooden staff) | 길갈의 넓은 들 | ✅ |
| 6 | `authored-samuel-bethlehem-david-anointing` 사무엘 — 베들레헴에서 다윗에게 기름 붓다 | 16:13 — 사무엘이 기름 뿔로 다윗에게 기름을 붓는 순간을 고정한다 | samuel(a horn of oil) · david-boy(a shepherd's staff) · jesse(a wooden staff) | 베들레헴 마을의 소박한 제사 자리 | ✅ |
| 7 | `authored-david-gibeah-harp` 다윗 — 기브아에서 수금을 타다 | 16:23 — 다윗이 수금을 손으로 타서 사울이 상쾌해지는 순간을 고정한다 | david-boy(a small harp) · saul(a plain traveling cloak) | 사울의 처소, 소박한 실내 자리 | ✅ |
| 8 | `authored-saul-gibeah-spear` 사울 — 기브아에서 창을 들다 | 18:10 후반 — 다윗이 수금을 타는 곁에서 사울의 손에 창이 들린 순간을 고정한다 | saul(a spear) · david(a small harp) | 사울의 처소 벽, 소박한 실내 | ✅ |
| 9 | `authored-david-ramah-samuel` 다윗 — 라마의 사무엘에게로 도피하다 | 19:18 — 다윗이 라마의 사무엘에게 이르러 사울이 행한 일을 고하는 순간을 고정한다 | david(a sword) · samuel(a robe corner) | 라마의 소박한 뜰 | ✅ |
| 10 | `authored-david-nob-priests` 다윗과 아히멜렉 — 놉 | 21:9 전반 — 제사장 아히멜렉이 보자기에 싼 칼을 에봇 뒤에서 꺼내 두 손으로 내밀고, 다윗이 두 손을 뻗어 받으려는 순간 | ahimelech(a cloth-wrapped sword) · david(a sword) | 놉 성막 앞뜰, 마른 흙바닥 · 성막 휘장과 낮은 떡상 — 배경 뒤편 | ✅ |
| 11 | `authored-david-gath-achish` 다윗의 미친 체함 — 가드 | 21:13 후반 — 다윗이 성문 기둥에 몸을 기대고 침을 흘리는 순간 | david(a wooden gate post) · achish(a fold of his robe) | 가드 성문과 성벽 | ✅ |
| 12 | `authored-david-adullam-cave` 다윗과 무리 — 아둘람 굴 | 22:2 전반 — 다윗이 굴 어귀에 서서 모여드는 무리를 손을 들어 맞아들이는 순간 | david(a sword) | 아둘람 굴 어귀 큰 바위 · 굴 위 마른 언덕 비탈 | ✅ |
| 13 | `authored-saul-nob-massacre` 사울과 도엑 — 놉의 심판 | 22:18 전반 — 사울의 명을 받은 도엑이 칼을 뽑아 쥐고 제사장들 쪽으로 돌아서는 순간 | saul(a spear) · doeg(a sword) · ahimelech(the hem of his ephod) | 놉 성막 앞뜰 | ✅ |
| 14 | `authored-david-en-gedi-saul` 다윗과 사울 — 엔게디 굴 | 24:8 후반 — 다윗이 땅에 엎드려 절하고 벤 옷자락을 들어 보이며, 사울이 돌아보는 순간 | david(a robe corner) · saul(a sword) | 엔게디 황무지 바위 절벽, 들염소 바위 · 양의 우리 곁 굴 어귀 | ✅ |
| 15 | `authored-samuel-ramah-death` 사무엘의 죽음 — 라마 | 25:1 후반 — 다윗이 애곡하는 무리를 뒤로하고 바란 광야로 내려가는 순간 | david(a sword) | 라마의 낮은 무덤 봉분 · 무덤 뒤 마른 언덕 | ✅ |
| 16 | `authored-david-ziklag-base` 다윗과 아기스 — 시글락 | 27:6 — 아기스가 손을 들어 성읍을 다윗에게 내어 주고, 다윗이 그 성읍을 마주 보고 서는 순간 | achish(a fold of his robe) · david(a sword) | 시글락 성읍 성벽과 성문 · 네게브 마른 벌판 | ✅ |
| 17 | `authored-saul-endor-medium` 사울과 엔돌의 신접한 여인 | 28:14 후반 — 사울이 사무엘의 영을 알아보고 얼굴을 땅에 대고 절하는 순간 | saul-old(a disguise cloak) · samuel(a robe corner) · endor-medium(a shawl fold) | 엔돌의 어두운 방, 밤 · 희미한 등불 하나 | ✅ |
| 18 | `authored-saul-gilboa-death` 사울의 마지막 — 길보아 산 | 31:4 전반 — 중상한 사울이 자기 칼을 세워 쥐고 선 채로 병기 든 자에게 명하는 순간 | saul-old(a sword) · saul-armor-bearer(a sword) | 길보아 산 마른 비탈 · 뒤쫓는 블레셋 군대 — 능선 원경 | ✅ |
| 19 | `authored-david-hebron-king-judah` 다윗 — 헤브론에서 유다 왕이 되다 | 2:4 전반 — 유다 사람들이 다윗에게 기름을 부어 왕을 삼는 순간 자체를 고정한다 | david(a robe corner) | 헤브론 성문 앞 넓은 뜰, 마른 흙바닥 · 성문 구조물 | ✅ |
| 20 | `authored-david-gibeon-battle` 아브넬과 요압 — 기브온 못가 | 2:13-14 — 두 지휘관이 못가에서 마주 앉았다가 소년들의 겨루기를 제안하는 순간을 고정한다 | abner(a spear) · joab(a sword) | 기브온의 못 · 마른 풀밭 둔덕 | ✅ |
| 21 | `authored-david-jerusalem-conquest` 다윗 — 시온 산성을 빼앗다 | 5:7 — 다윗이 시온 산성을 빼앗아 그 앞에 선 순간을 고정한다 | david(a sword) | 시온 산성 성벽 · 예루살렘을 둘러싼 산지 | ✅ |
| 22 | `authored-david-ark-jerusalem` 다윗 — 법궤를 다윗 성으로 메어 올리다 | 6:15 — 다윗이 법궤 앞에서 두 손을 들고 걷는 순간을 고정한다 | david(a sword) | 법궤를 멘 자들 — 다윗 앞에서 궤를 나른다 · 다윗 성으로 오르는 길 | ✅ |
| 23 | `authored-david-nathan-covenant` 나단 — 다윗에게 언약을 전하다 | 7:12-16 — 나단이 한 팔을 들어 다윗에게 언약의 말씀을 전하는 순간을 고정한다 | nathan(a wooden staff) · david(a robe corner) | 다윗의 처소 앞뜰 | ✅ |
| 24 | `authored-solomon-jerusalem-birth` 밧세바 — 솔로몬을 낳다 | 12:24 후반 — 밧세바가 갓난 아기를 품에 안은 순간을 고정한다 | bathsheba(an infant) | 처소의 방 | ✅ |
| 25 | `authored-david-mahanaim-exile` 다윗 — 마하나임으로 피신하다 | 17:24 전반 — 다윗이 마하나임에 이르러 걷는 순간을 고정한다 | david(a robe corner) | 마하나임 성읍으로 오르는 마른 길 | ✅ |
| 26 | `authored-david-returns-jerusalem` 다윗 — 요단을 건너 돌아오다 | 19:15 — 다윗이 요단에 이르러 걷는 순간을 고정한다 | david(a sword) | 요단 강가 | ✅ |
| 27 | `authored-solomon-gihon-anointing` 솔로몬 — 기혼에서 기름부음을 받다 | 1:39 — 기름 붓는 자는 왕상 1:39 「제사장 사독이 | zadok(a horn of oil) · solomon(a robe corner) | 기혼의 샘가 | ✅ |
| 28 | `authored-solomon-jerusalem-david-charge` 다윗의 유언 — 예루살렘 | 2:1-3 — 다윗이 침상에 누운 채 아들에게 명하고, 솔로몬이 그 곁에 서서 듣는 순간 | david-old(이불) · solomon(허리띠) | 왕궁 침소 — 소박한 침상과 돌벽 | ✅ |
| 29 | `authored-solomon-gibeon-dream` 솔로몬의 꿈 — 기브온 | 3:5 후반-3:9 — 솔로몬이 잠든 채 꿈속에서 구하는 순간 | solomon(겉옷자락) | 기브온 산당의 돌 제단 — 밤하늘 | ✅ |
| 30 | `authored-solomon-jerusalem-two-mothers` 두 여인의 재판 — 예루살렘 | 3:16-3:22 — 두 여인이 왕 앞에 서서 다투는 순간 | solomon(왕홀) · mother-a(아기) · mother-b(겉옷자락) | 왕궁 알현실 — 돌바닥과 기둥 | ✅ |
| 31 | `authored-solomon-jerusalem-temple-build` 성전 건축 — 예루살렘 | 6:2 · 6:38 — 건축이 진행 중인 성전 건물 앞에 솔로몬이 서서 바라보는 순간 | solomon(전 모형) | 다듬은 돌과 백향목 널판으로 세워지는 성전 건물 · 건물 앞뜰의 다듬은 돌더미 | ✅ |
| 32 | `authored-solomon-jerusalem-palace` 왕궁 건축 — 예루살렘 | 7:1-2 — 레바논 나무 궁, 백향목 기둥이 늘어선 건물 앞에 솔로몬이 서 있는 순간 | solomon(겉옷자락) | 레바논 나무 궁 — 백향목 기둥 네 줄과 들보 · 다듬은 돌 기초와 벽 | ✅ |
| 33 | `authored-solomon-jerusalem-temple-dedication` 성전 봉헌 — 예루살렘 | 8:54 — 솔로몬이 단 앞에서 무릎 꿇고 하늘을 향해 손을 편 순간(기도를 마치고 일어나기 직전) | solomon(겉옷자락) | 성전 앞뜰의 놋단 | ✅ |
| 34 | `authored-solomon-ezion-geber-fleet` 에시온게벨 함대 — 홍해 | 9:26-27 — 홍해 물가에 지어진 배들 앞에 솔로몬이 서 있는 순간(9:26 「솔로몬 왕이 | solomon(겉옷자락) | 홍해 물가에 지어진 배들 · 물가와 바다 | ✅ |
| 35 | `authored-solomon-jerusalem-sheba` 스바 여왕의 방문 — 예루살렘 | 10:2 후반-10:10 — 스바 여왕이 예물을 왕께 드리는 순간(10:10) | solomon(왕홀) · sheba-queen(향품 상자) | 왕궁 알현실 — 돌바닥과 기둥 | ✅ |
| 36 | `authored-solomon-jerusalem-apostasy` 솔로몬의 배교 — 예루살렘 | 11:7-8 — 늙은 솔로몬이 산당의 우상 앞에 선 순간 | solomon-old(겉옷자락) | 예루살렘 앞 산의 이방 산당과 우상 | ✅ |
<!-- scene-table:end -->

## 묶음 A 그림 판정 (4/7 · 2026-09-04) — 라벨 A1 · 장면 시드 11

몽타주 `.forge/reports/canon-pilot/scripture-scene/montage-A.png`(3x3, 칸 번호는 아래 「몽타주칸」).
`.forge/reports/`는 gitignored — 산출물이 아니라 아래 재현 명령이 정본이다.

```
cd scripts/canon
for s in $(cat ../../.forge/scratch/bundle-A.txt); do \
  /Users/calmonion/.local/biblemap-imggen/.venv314/bin/python \
  gen_scripture_scene.py --scene $s --seeds 11 --label "A1-${s#authored-}"; done
python3 make_scene_montage.py A $(cat ../../.forge/scratch/bundle-A.txt) --label A1
```

**사용자 판정 열은 사람이 적는다** — 드라이브는 비워 둔다.
판정 페이지(장면 9칸 + 결정 4건): https://claude.ai/code/artifact/1a33c6ab-87b7-4605-b262-c135b8468bcb · 결과 원본은 그 아티팩트 db의 `review/bundleA`. 기계 판정 열은 `judge_scene.py`의 값 그대로다.
**단, 아래 「규칙 실측」 1번이 말하듯 이 묶음에서 C4 열은 인물이 아니라 구역 상자의 배경 어둡기를 재고 있다** —
낙제 C4 다섯 건은 그림의 결함이 아니다. 오른쪽 「인물 잉크(붙임 마스크)」가 같은 산식을 붙인 인물에게만
적용한 값이고, 9장면 14인물 전부가 임계 0.055를 넘는다.

<!-- bundle-a:begin -->
| 표# | 몽타주칸 | 장면 | 기계 판정 | C3 이음매 | C4 잉크(상자) | 인물 잉크(붙임 마스크) | 사용자 판정 |
|---|---|---|---|---|---|---|---|
| 1 | 9 | `authored-saul-mizpah-chosen` 사울 — 미스바에서 뽑히다 | 낙제 C4 | 0.00 | 0.046(최소) · 비 1.29 | 0.101(samuel, 최소) |  |
| 2 | 7 | `authored-saul-jabesh-rescue` 사울 — 야베스 구원 | 통과 | 0.37 | 0.058(최소) · 비 1.35 | 0.152(nahash, 최소) |  |
| 3 | 6 | `authored-saul-gilgal-coronation` 사울 — 길갈에서 왕이 되다 | 낙제 C4 | 0.00 | 0.039(최소) · 비 1.58 | 0.094(samuel, 최소) |  |
| 4 | 8 | `authored-saul-michmash-battle` 사울 — 길갈에서 사무엘을 기다리지 못하다 | 낙제 C4 | 0.00 | 0.041(최소) · 비 1.52 | 0.092(samuel, 최소) |  |
| 5 | 5 | `authored-saul-gilgal-amalek` 사울 — 길갈에서 겉옷자락이 찢어지다 | 통과 | 0.00 | 0.059(최소) · 비 1.03 | 0.186(samuel, 최소) |  |
| 6 | 3 | `authored-samuel-bethlehem-david-anointing` 사무엘 — 베들레헴에서 다윗에게 기름 붓다 | 낙제 C3 | 0.46 | 0.113(최소) · 비 1.04 | 0.204(jesse, 최소) |  |
| 7 | 1 | `authored-david-gibeah-harp` 다윗 — 기브아에서 수금을 타다 | 낙제 C4 | 0.00 | 0.052(최소) · 비 3.93 | 0.124(saul, 최소) |  |
| 8 | 4 | `authored-saul-gibeah-spear` 사울 — 기브아에서 창을 들다 | 낙제 C3 | 0.48 | 0.081(최소) · 비 1.01 | 0.094(david, 최소) |  |
| 9 | 2 | `authored-david-ramah-samuel` 다윗 — 라마의 사무엘에게로 도피하다 | 낙제 C4 | 0.00 | 0.040(최소) · 비 3.84 | 0.089(samuel, 최소) |  |
<!-- bundle-a:end -->

## 규칙 실측

4/7 묶음 A(9장면, 라벨 A1, 시드 11)에서 실측한 것. 1~4번이 이번 묶음에서 새로 잡혔고, 5~8번은
생성 도중 잡아 이미 반영했거나 다음 묶음에 남긴 것이다.

### 1. C4 잉크 축은 인물이 하늘을 등지지 않으면 무너진다 (측정 축의 결함 — 그림의 결함이 아니다)

`judge_scene._sil_bbox`는 구역 상자 안에서 `obj_mask`(하늘이 아닌 것)의 bbox를 잡는다. 삼상17은 인물이
**하늘을 등지고** 서서 이 마스크가 인물만 남겼다. 묶음 A는 인물이 풀·언덕·실내 벽 앞에 선다 → 상자 전체가
「하늘 아닌 것」이라 **실루엣 bbox = 구역 상자**가 된다(표본 8/8에서 정확히 일치). 그래서 C4가 재는 값은
인물의 잉크가 아니라 **상자 안 배경의 어둡기**다.

| 측정 | 값 |
|---|---|
| 실루엣 bbox = 구역 상자인 표본 | 8/8 |
| 상자를 인물에 바짝 좁혔을 때 잉크 상승 | +0.003 ~ +0.006 (0.046 → 0.049 등, 임계 0.055에 못 미침) |
| 보고된 「인물 잉크」 중 배경 기여분 | 34% ~ 96% (붙이기 **전** 상자의 잉크 / 붙인 **뒤** 상자의 잉크) |
| **붙임 마스크 안에서만 잰 인물 잉크** | 14인물 전부 0.089 ~ 0.260 — **전원 임계 0.055 통과** |

대표 예: `authored-saul-gibeah-spear`의 david는 상자 잉크 0.081인데 붙이기 전 배경만으로 이미 0.077이다
(배경 기여 96%, 인물 본인 기여 0.004). `authored-david-ramah-samuel`의 samuel은 0.040 중 배경이 0.034(85%) —
인물 본인은 0.006이다. 반대로 붙임 마스크로 재면 각각 0.094 · 0.089로 넉넉히 통과한다.

**결론**: 이 묶음의 「낙제 C4」 다섯 건(미스바·길갈 대관·믹마스·라마·기브아 수금)은 그림을 고쳐야 할 신호가 아니다.
계획이 허용한 손잡이(명세 문구·시드·구역 상자)로는 지배항인 배경 기여를 걷어낼 수 없다 — 상자를 조여도 +0.006이다.
**바른 수정은 `judge_scene.c4_style`이 `_sil_bbox` 대신 붙임 마스크(생성기가 이미 아는 `_place`의 `bb`와 알파)
안에서 재는 것**인데, 이는 계획의 「하지 않을 것」(judge_scene 산식 변경 = 회귀 가드)에 걸린다 → **별건으로 올린다.**

### 2. C3 밑변 이음매는 접지선이다

낙제 2건 모두 위치가 `<인물>.bottom`이다 — `authored-samuel-bethlehem-david-anointing` S3/david-boy.bottom 0.46,
`authored-saul-gibeah-spear` S3/david.bottom 0.48(임계 0.40). 그 자리를 잘라 보면 접지 단계가 그린
**발밑 지면선**이고, **통과한** `authored-saul-jabesh-rescue`(S4/nahash.bottom 0.37)도 같은 구조다.
즉 통과·낙제를 가른 것은 아티팩트의 유무가 아니라 그 지면선이 상자 밑변에 얼마나 걸쳤는가다.
1번과 달리 **축이 무너졌다고 단정할 근거는 없다** — 사람 눈 판정과 함께 봐야 한다.

### 3. 능선(ridge) 군중 단계가 풀·언덕 배경에서 아무것도 그리지 않는다

`authored-saul-gilgal-coronation` · `authored-saul-michmash-battle` · `authored-saul-mizpah-chosen` 세 장면에서
`crowd_back` 능선 단계가 25~29초를 돌고 전폭 상자((12, ~290)-(1203, ~610))를 받았는데도 완성본에 군중이 없다.
로그에 오류·건너뜀 표시는 없다. 삼상17의 군대 단계는 하늘선 띠에서 성립했다 — 하늘선이 낮은 언덕 풍경에서는
띠 마스크가 풀밭 위에 얹히는 듯하다(가설, 미검증).

### 4. 세 장면이 육안으로 같은 그림이 됐다

위 세 장면(대관식·믹마스·미스바)은 「두 인물이 금빛 언덕 앞에 마주 섬」으로 수렴했다. 순간을 가르는 것
(대관식의 백성과 화목제단 · 믹마스의 번제 연기 · 미스바의 제비 뽑힌 무리)이 화면에 서지 않았다. 제단 단계는
작게 그려지긴 했다(상자 486,460-668,588 → 화면 아래쪽 작은 덩어리). **명세는 3/7에서 36/36 승인을 받았으므로,
이것은 명세의 문제가 아니라 「배경 한 줄 + 능선 + 작은 지물 상자」로는 순간이 서지 않는다는 생성 쪽 실측이다.**

### 5. 판 경로에서 무릎 꿇기는 도달하지 않는다

문구 2종(자세 뒤 / 자세 앞) x 시드 11에서 0/2 직립. 부정어 `standing`·`upright`도 무효.
→ 명세의 순간은 서 있음/걷기로 잡아야 한다. 영향받는 장면: 성전 낙성식·기혼 기름부음(무릎), 다윗 유언(누움),
기브온 꿈(잠), 엔돌(엎드림), 밧세바(아기 안기) — 각 묶음에서 사람 결정이 필요하다.

### 6. 「village courtyard」는 중세 교회를 부른다

시험 1장에서 중세 교회 첨탑이 나왔다. 36장면 전부의 배경 단계 부정어에 교회족
(church · steeple · cathedral · chapel · cross · bell tower · spire)을 추가했다 — **반영 완료**.

### 7. 같은 시대·같은 직분 노인은 어휘만으로 안 갈라진다

사무엘과 이새가 같은 실루엣으로 나왔다. `cast/jesse.json`을 두건·짧은 수염·stocky로 분화 — **반영 완료**.

### 8. 소요 실측

| 단위 | 시간 |
|---|---|
| 배경 1장 | 39초 |
| 인물 판 + 접지 | 90~150초 |
| 3인물 장면 1장 | 약 6분 |
| 9장면 묶음 1회 | 약 50분 |
| 몽타주 + 9장면 기계 판정 | 1분 미만 (GPU 0) |

## 장면 안 인페인팅 3판 대조 (4/7 뒤 · task 337 · 2026-09-05)

라벨 A1(판 합성, 4/7 기존) · IN1(장면 안, 앵커 끔, strength 0.85) · IS1(장면 안, 앵커 켬, 0.85) ·
IH1(장면 안, 앵커 켬, 0.95). 모두 장면 시드 11. 몽타주는
`.forge/reports/canon-pilot/scripture-scene/montage-inscene.png`(gitignored — 아래가 재현 명령이다).

```
cd scripts/canon
V=~/.local/biblemap-imggen/.venv314/bin/python
for s in authored-saul-gilgal-amalek authored-samuel-bethlehem-david-anointing; do n=${s#authored-}
  $V gen_scripture_scene.py --scene $s --seeds 11 --label "IN1-$n" --figures inscene --no-anchor
  $V gen_scripture_scene.py --scene $s --seeds 11 --label "IS1-$n" --figures inscene
  $V gen_scripture_scene.py --scene $s --seeds 11 --label "IH1-$n" --figures inscene --fig-strength 0.95
done
python3 make_inscene_montage.py authored-saul-gilgal-amalek authored-samuel-bethlehem-david-anointing
```

**사용자 판정 열은 사람이 적는다** — 드라이브는 비워 둔다.

<!-- inscene-ab:begin -->
| 장면 | 판 | 이음매(C3) | 인물이 그려졌는가(기계 밖·눈) | 사용자 판정 |
|---|---|---|---|---|
| `authored-saul-gilgal-amalek` | A1 판 합성 | 0.00 통과 | 둘 다 섰다. **닿지는 않는다** |  |
| | IN1 장면 안 s0.85 | 0.00 통과 | **하나만 나왔다** |  |
| | IS1 장면 안+앵커 s0.85 | 0.00 통과 | **하나만 나왔다**(앵커 차이 안 보임) |  |
| | IH1 장면 안+앵커 s0.95 | 0.00 통과 | 하나만, 형태가 일그러졌다 |  |
| `authored-samuel-bethlehem-david-anointing` | A1 판 합성 | 0.46 낙제 | 셋 다 섰다. **붓지는 않는다** |  |
| | IN1 장면 안 s0.85 | 0.00 통과 | 머리 없는 옷 형태 · 이새가 덤불에 녹음 |  |
| | IS1 장면 안+앵커 s0.85 | 0.00 통과 | 작은 형체 하나 · 이새 덤불에 녹음 |  |
| | IH1 장면 안+앵커 s0.95 | **0.74 낙제** | 셋이 보이나 화풍·형태가 무너짐 |  |
<!-- inscene-ab:end -->

### 13. 장면 안 인페인팅은 이번 판에서 판 합성을 못 이겼다 (2026-09-05, task 337)

**측정 축은 좋아졌는데 그림이 나빠졌다.** 이음매는 타원 마스크로 없앴지만(실측 10), 정작 **인물이 안 그려진다** —
길갈은 두 사람이 서야 하는데 세 판 모두 하나만 나왔고, 베들레헴은 형태가 무너졌다. ADR `260902-193724`이
구역 인페인팅을 버린 두 이유 중 ②(자세가 지형에 끌려간다)가 **더 나쁜 형태로 재현됐다**: 지금은 자세가 끌려가는 게
아니라 **인물 자체가 지형에 먹힌다.**

**strength는 두 결함을 맞바꾼다.** 0.85는 이음매 0.00인데 인물이 안 서고, 0.95는 인물이 서기 시작하는 대신
이음매가 **0.74**로 튄다(임계 0.40). 칠하는 면적이 넓어져 붙임이 마스크 경계에 닿기 때문이다.
**둘을 동시에 만족하는 값이 이 구간에 없다.**

**앵커는 육안 차이를 만들지 못했다.** 지역 IP 마스크로 두 얼굴이 각자 구역에 제대로 걸렸는데도(실측 11)
IN1과 IS1이 눈으로 구분되지 않는다. 인물 자체가 안 그려지는 상태에서는 얼굴 앵커가 실릴 자리가 없다.
**앵커의 값어치는 인물이 제대로 서는 경로에서 다시 재야 한다** — 이번 판정은 앵커에 대한 판정이 아니다.

**다음에 시험할 것(가설, 미검증).** 판 합성은 인물을 **확실히** 그리고, 장면 안 인페인팅은 접지·조명·접촉을
공짜로 얻는다. 둘을 순서로 붙이는 길이 남아 있다 — 판을 먼저 얹어 **인물이 이미 있는 캔버스**를 만들고,
그 위에 **인물 모양 마스크**로 낮은 strength 다듬기를 걸어 장면에 녹이는 것. 접촉은 두 판을 얹은 뒤
합집합을 한 번 다듬으면 손이 만날 자리가 생긴다. 이번 실패의 원인이 「빈 지형에서 인물을 세우지 못한다」이므로,
**인물을 세우는 일을 판에게 맡기고 녹이는 일만 장면에 맡기는** 분업이다.

### 9. 삼상17 재현에는 **판 시드**를 함께 줘야 한다 (2026-09-05, task 337)

`--plate-seeds`를 빼고 `--seeds 11`만 주면 v41이 재현되지 않는다. v41은 골리앗(S3)·다윗(S5) 판에 **시드 42**를 쓰고
방패든자(S4)만 11이다. 빼고 돌린 v43은 배경 네 단계(S1b·S1c·S2a·S2b)가 **픽셀까지 동일**한데 인물 판부터 갈렸고,
**같은 시드 11을 쓴 S4 판만 동일**했다 — 이 비대칭이 「파이프라인은 결정적이고 시드만 틀렸다」의 증거다.
정본 명령은 `SCENE-1SAM17.md` §0. 정본 시드로 돌린 v44는 v41과 픽셀 동일(`getbbox() → None`).
**회귀 가드를 쓰는 계획은 명령에 판 시드를 반드시 적을 것** — 빼면 코드가 멀쩡해도 반드시 실패한다.

### 10. 타원 마스크는 상자 이음매를 없앤다 (2026-09-05, task 337)

구역 마스크를 사각형에서 **내접 타원 합집합**으로 바꾸자 C3 이음매가 사라졌다.

| 장면 | 판 합성(사각) | 장면 안(타원) |
|---|---|---|
| `authored-samuel-bethlehem-david-anointing` | 0.46 낙제 @S3/david-boy.bottom | **0.00 통과** |
| `authored-saul-gilgal-amalek` | 0.00 통과 | 0.00 통과 |

붙임은 원래도 변화 마스크(실루엣)로 하는데, 그 실루엣이 **구역 마스크에서 잘리는** 것이 이음매의 기전이었다.
곡선 경계에는 잘릴 직선 변이 없다. ADR `260902-193724`이 실패로 기록한 손잡이 넷(닫기 반지름·맥락 창·경계 램프·
strength)은 **전부 사각형을 유지한 채** 주변을 손본 것이었다 — 기전을 직접 친 것은 이번이 처음이다.

### 11. 지역 IP 마스크는 **어댑터 수만큼 항목**이어야 한다 (2026-09-05, task 337)

한 프롬프트에 두 인물을 넣고 각자 얼굴을 물리려면 IP-Adapter를 둘 로드하고 `ip_adapter_masks`를 준다.
`IPAdapterMaskProcessor.preprocess`는 `(N, 1, h, w)`를 돌려주는데 이것을 **한 항목으로 뭉쳐 주면 거절당한다** —
`Length of ip_adapter_masks array (1) must match length of self.scale array (2)`. 어댑터마다 한 항목
(`[pm[i:i+1] for i in ...]`)으로 쪼개야 한다. diffusers 0.40.0 실측.

### 12. 두 인물을 한 프롬프트에 넣으면 짧은 서술이 강제된다 (2026-09-05, task 337)

CLIP 77토큰 예산의 내역: 화풍 머리 22 · 인물 전체 서술 30~31(사람당) · 남는 것이 상호작용 문구다.
두 사람을 온전한 서술로 넣으면 81·87로 **넘친다**(`derive_scene --check`가 잡았다). 머리·수염·머리쓰개·체격을 뺀
짧은 서술(`{castc:<id>}`, 18~23)로 73·74에 맞췄다. **얼굴을 앵커가 지므로 뺄 수 있는 것**이고,
앵커가 없는 인물에게 쓰면 정체를 지탱할 것이 사라진다 — 그룹 단계 전용이다.


