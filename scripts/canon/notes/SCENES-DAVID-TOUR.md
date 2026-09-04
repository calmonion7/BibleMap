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

## 규칙 실측

(4/7부터 채움)
