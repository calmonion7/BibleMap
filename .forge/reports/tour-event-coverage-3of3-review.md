# 투어 사건 커버리지 검토 3/3 — 복음·초대교회 (task#235)

2026-07-22. 대상: 2개 투어 시대 범위 미커버 저작 사건 36건. 기준: 1부 계획 "배경" 절과 동일 — 신약은 장면 단위 클러스터링으로 중복 시점 식별이 핵심.

## 판정 요약
- 포함 24 (복음 14 · 초대교회 10)
- 제외 13 (전부 ① 동일 장면의 인물별 중복 시점)
- 부수 교정 7 (신규 포함 사건 sortKey — 연대계 충돌·동렬 불정 해소)

## 제외 목록과 사유 (전부 ①)

| 사건 | 기존/채택 대표 정차지 |
|---|---|
| `mary-bethlehem-nativity` | 기존 `jesus-bethlehem-birth` (탄생) |
| `mary-flight-to-egypt` | 기존 `jesus-flight-egypt` (애굽 피신) |
| `mary-return-nazareth` | 채택 `jesus-nazareth-childhood` (귀환·정착의 주인공 시점) |
| `jesus-cana-wedding` | 기존 `mary-cana-wedding` (가나 — 기존 시점 유지 규칙) |
| `john-baptist-lamb-of-god` | 채택 `john-first-disciple` (요단강 증거·첫 따름 동일 장면) |
| `john-call-zebedee` | 채택 `jesus-call-disciples` (갈릴리 부르심) |
| `peter-call-galilee` | 채택 `jesus-call-disciples` (부르심 장면 대표) |
| `john-apostle-boanerges` | 채택 `peter-apostle-named` (열두 사도 세움 — 반석 명명이 가이사랴 고백과 연결) |
| `john-last-supper` | 기존 `jesus-last-supper` (최후의 만찬) |
| `john-cross-mary` | 기존 `jesus-crucifixion`+`mary-jerusalem-cross` (십자가) |
| `john-empty-tomb` | 기존 `jesus-resurrection` (빈 무덤) |
| `john-tiberias` | 채택 `peter-restoration` (디베랴 현현 — "내 양을 먹이라"가 서사 기여 최대) |
| `john-sanhedrin-trial` | 기존 `peter-solomons-portico-trial` (공회 증언, 초대교회) |

## 부수 교정 (신규 포함 사건 sortKey)

**연대계 충돌**: 제자 인물 파일(john_the_apostle·peter)은 수난 주간을 30~30.3에 두는 연대계를 쓰고, 예수 파일은 33년설(만찬 32.8·십자가 33.2·부활 33.4)을 씀 — 그대로 넣으면 베드로 부인·회복이 나사로(31)보다 앞 정렬. 포함분을 예수 연대계로 이관:
- `peter-denial` 30.1 → **33.05** (겟세마네 33 뒤, 십자가 33.2 앞)
- `peter-restoration` 30.3 → **33.5** (부활 33.4 뒤, 승천 33.6 앞)

**동렬·역순 불정 해소**:
- `john-first-disciple` 27 → **26.5** (요1 순서: 세례 26 뒤, 가나 27 앞 — 원값은 "어린 양" 증거 27.5보다 앞이면서 가나와 동렬)
- `peter-apostle-named` 28.5 → **28.4** (산상수훈 28.5 동렬 해소, 세움→수훈 순)
- `john-baptist-prison-question` 28.5 → **28.6** (산상수훈 뒤 — 마 11장)
- `jesus-bethsaida-feeding` 29 → **29.05**, `peter-walks-on-water` 29 → **29.1** (요한 처형 29와 삼중 동렬 해소, 오병이어→물 위 순)

제외된 제자 시점 사건들(30~30.3 연대계 잔존)은 투어 밖이므로 이번에 건드리지 않음 — 인물 여정 연대계 정합은 별도 감사 태스크 후보(1·2부와 동일 계열).

## 포함 목록 (24)
복음(14): jesus-magi-visit, jesus-nazareth-childhood, john-first-disciple, jesus-call-disciples, jesus-capernaum-healing, john-baptist-machaerus-prison, john-baptist-prison-question, peter-apostle-named, jesus-bethsaida-feeding, peter-walks-on-water, jesus-transfiguration, peter-denial, peter-restoration, jesus-jericho-zacchaeus
초대교회(10): paul-cyprus-mission, paul-pisidian-antioch, paul-iconium-lystra-derbe, paul-thessalonica-berea, paul-jerusalem-arrest, paul-caesarea-imprisonment, paul-voyage-malta, paul-release-pastorals, peter-rome-martyrdom, paul-rome-martyrdom
(id는 `authored-` 접두 생략 표기)
