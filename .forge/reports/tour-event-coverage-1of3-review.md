# 투어 사건 커버리지 검토 1/3 — 원시사·족장·출애굽·정복 (task#233)

2026-07-22. 대상: 3개 투어 시대 범위의 미커버 저작 사건 42건(욥 7건은 계획 비목표로 대상 제외).
판정 기준: 계획 "배경" 절 — 원칙 전부 포함, 제외는 ①동일 장면의 인물별 중복 시점 ②서사 무기여 순수 연대기 기록만.

## 판정 요약
- 포함 34 (원시사 11 · 족장 17 · 출애굽·정복 6) — 전건 해설 저작 후 투어 JSON에 추가
- 제외 8 (① 4건 · ② 4건)
- 부수 교정 2 (sortKey 서사 충돌)

## 제외 목록과 사유

| 사건 | 사유 |
|---|---|
| `authored-abel-faith-witness` (-3899) | ① 아벨의 제사 장면(기존 `authored-abel-offering`, -3901)의 히브리서 11:4 재조명 — 동일 장면의 신학적 재진술 |
| `authored-enoch-methuselah-born` (-3313) | ② 동행 시작 계기가 `authored-enoch-walked-with-god`(-3312, 포함)의 서술에 내포 — 출생 연대기 |
| `authored-seth-death` (-2958) | ② 창세기 5장 "죽었더라" 후렴의 반복 — 아담의 죽음(포함)이 이미 대표 |
| `authored-noah-death-950` (-1998) | ② 투어 종결(무지개 언약)이 서사적 마침표 — 950세 연대기 기록 |
| `authored-jacob-beersheba-departure` (-1930) | ① 기존 `authored-isaac-blessing-jacob`(-1930, 축복과 밧단아람 파송)과 동일 장면의 야곱 시점 |
| `authored-jacob-egypt-migration` (-1876) | ① 기존 `authored-joseph-egypt-family-reunion`(-1876, 상봉 및 가족 이주)과 동일 장면의 야곱 시점 |
| `authored-jacob-hebron-return` (-1843) | ① 이삭 임종·장사 장면 — 주인공 시점 `authored-isaac-hebron-death`를 포함으로 채택, 야곱 시점 제외 |
| `authored-joseph-hebron-departure` (-1897) | ② 이동 연결 기록 — 도단 구덩이 정차지(기존)에 내포 |

## 부수 교정 (sortKey 서사 충돌 — 계획의 점검 항목)

이삭 임종 사건 쌍의 sortKey -1843이 애굽 이주(-1876)보다 **뒤**로 정렬됨 — 이삭 임종은 이주 전 가나안(헤브론)에서 일어나야 하므로 서사 붕괴(에브라임 축복 -1859 뒤에 임종이 오는 꼴). 연대 계산으로도 -1843은 이삭 출생(-2000)+180세와 불일치.
- `data/person_events/isaac.json` `authored-isaac-hebron-death`: sortKey -1843 → **-1878** (형들 첫 방문 -1877 직전)
- `data/person_events/jacob.json` `authored-jacob-hebron-return`: sortKey -1843 → **-1878.1** (동일 사건의 야곱 시점 — 투어 제외돼도 인물 여정 순서 일관 위해 함께 교정)
- startDate/yearLabel은 유지(연대 표기 자체가 아니라 정렬 충돌 해소가 목적이며, 근사 연대 표기는 별도 판단 사안)

## 포함 목록 (34)

원시사(11): adam-creation, adam-meets-eve, cain-offering-rejected, cain-cursed-and-marked, cain-builds-city-of-enoch, seth-birth, enoch-walked-with-god, adam-death, noah-ark-command, noah-leaves-ark-altar, noah-vineyard
족장(17): abraham-departs-haran, abraham-bethel-altar, abraham-egypt-famine, abraham-lot-separation, abraham-lot-rescue, abraham-hagar-wilderness, abraham-beersheba-well, isaac-gerar-sojourn, isaac-beersheba-covenant, jacob-shechem-settlement, isaac-hebron-death, joseph-two-dreams, joseph-egypt-slave, joseph-potiphar-wife-prison, joseph-egypt-prison-dreams, joseph-egypt-brothers-first, joseph-silver-cup-benjamin
출애굽·정복(6): moses-birth-egypt, moses-flees-midian, joshua-gibeon-alliance, joshua-shiloh-tabernacle, joshua-shechem-covenant, joshua-farewell-death
(id는 `authored-` 접두 생략 표기)
