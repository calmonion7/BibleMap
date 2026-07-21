# 투어 사건 커버리지 검토 2/3 — 사사·왕국·선지자·포로 (task#234)

2026-07-22. 대상: 4개 투어 시대 범위 미커버 저작 사건 55건. 기준: 1부 계획 "배경" 절과 동일.

## 판정 요약
- 포함 52 (사사 18 · 왕국 19 · 선지자 14 · 포로 1)
- 제외 3 (① 2건 · ② 1건)
- 부수 교정 5 (신규 포함 사건의 sortKey 서사 역전)

## 제외 목록과 사유

| 사건 | 사유 |
|---|---|
| `authored-samuel-gilgal-saul-anointing` (-1050) | ① 기존 `authored-saul-gilgal-coronation`(-1049, 길갈 왕위 확정)과 동일 장면(삼상 11:14–15)의 사무엘 시점 |
| `authored-elisha-mantle-jordan` (-850) | ① 기존 `authored-elijah-jordan-ascension`(-852, 승천·겉옷 계승)과 동일 장면의 엘리사 시점 |
| `authored-david-birth-bethlehem` (-1040) | ② 출생 연대기 — 동년·동소의 기존 기름부음 정차지가 다윗 도입을 대표 |

## 시대 배정 판정 (계획 특이점)
- 사무엘 사사기 5건(성전 봉헌·부르심·미스바 대승·순회 재판·라마 선지학교) → **사사 투어** (마지막 사사).
- 사무엘의 죽음(라마) → **왕국 투어** (다윗 도피기 서사의 전환 표지).
- 이사야 히스기야 시대 6건(-734~-700) → **선지자 투어 꼬리** (기존에 요나·이사야 소명 포함, "선지자 시대" 폭 운영 확인).
- 에스더 모르드개 역모 고발 → 포로 투어 (간택과 하만 조서 사이 복선).

## 부수 교정 (신규 포함 사건 sortKey — 성경 서사 순서 역전 해소)

삼상 후반 도피 서사의 정경 순서(라마 피신 19장 → 놉 21:1 → 가드 21:10 → 아둘람 22:1 → 놉 학살 22:9 → 엔게디 24장 → 사무엘 죽음 25장 → 시글락 27장 → 엔돌 28장 → 길보아 31장) 및 수금 입문(삼상 16장, 골리앗 17장 전) 기준:
- `david-gibeah-harp` -1023 → **-1026** (골리앗 -1025 앞으로)
- `david-gath-achish` -1013.5 → **-1012.8** (놉 떡 -1013 뒤로)
- `saul-nob-massacre` -1020 → **-1011.8** (아둘람 -1012 뒤, 엔게디 -1011 앞)
- `samuel-ramah-death` -1020 → **-1010.95** (엔게디 뒤, 시글락 앞)
- `david-ziklag-base` -1008 → **-1010.93** (길보아 -1010 앞으로 — 원값은 전사 후 정렬되는 역전)

## 포함 목록 (52)
사사(18): deborah-bethel-judging, deborah-kedesh-summons, deborah-kedesh-jael, deborah-song, gideon-ophrah-fleece, gideon-succoth-pursuit, gideon-penuel-pursuit, ruth-bethlehem-threshing, jephthah-gilead-exile, jephthah-jordan-shibboleth, samson-timnah-riddle, samson-lehi-jawbone, samson-gaza-gate, samuel-shiloh-dedication, samuel-shiloh-calling, samuel-mizpah-victory, samuel-circuit-judge, samuel-ramah-school
왕국(19): david-gibeah-harp, david-ramah-samuel, david-nob-priests, david-gath-achish, david-adullam-cave, saul-nob-massacre, samuel-ramah-death, david-ziklag-base, david-gibeon-battle, solomon-jerusalem-birth, david-mahanaim-exile, david-returns-jerusalem, solomon-gihon-anointing, solomon-jerusalem-david-charge, solomon-jerusalem-two-mothers, solomon-jerusalem-palace, solomon-ezion-geber-fleet, solomon-jerusalem-sheba, solomon-jerusalem-apostasy
선지자(14): elijah-cherith-ravens, elijah-kishon-slaughter, elijah-jezreel-rain-run, elijah-ahaziah-fire, elisha-gilgal-stew-bread, jonah-storm-sea, jonah-fish-prayer, jonah-gourd-lesson, isaiah-jerusalem-ahaz, isaiah-jerusalem-naked-sign, isaiah-jerusalem-hezekiah-illness, isaiah-jerusalem-hezekiah, isaiah-jerusalem-babylon-envoys, isaiah-jerusalem-cyrus-prophecy
포로(1): esther-mordecai-plot
(id는 `authored-` 접두 생략 표기)
