# 2026-06-28 — 바울 큐레이션 인물 추가 (파일럿): 여정 18정차지 authored

## 계획 vs 실제
- 계획대로:
  - S1~S4 4슬라이스 직렬 실행 — `data/person_events/paul.json`(18정차지: 16신규 authored + 기존 tail 2개 재사용 release-pastorals·rome-martyrdom), `persons.py` 등록(신약/바울), 구절 생성 + Neo4j 적재, 빌드·검증. 기존 13명과 동일 품질/구조.
  - 검증: `/persons/curated` 바울(eventCount 18) · `/journey` 18 stops 전원 좌표 · `/event/authored-paul-*/verses` 사도행전 본문. Playwright 데스크톱·모바일 PASS(여정 트리→사건 펼침→구절 ko/en), 콘솔0.
- 발산 / 현장 결정(필드 수준 단순화 — 설계 재그릴링 불필요):
  - **구절은 context 괄호 참조에서 자동 파싱**: `generate_person_event_verses.py`가 `context`의 한글 참조(예 `(행 9:1–19)`, 교차장 `(행 27:13–28:10)`)를 읽어 `books`+본문 생성 → S1에서 `books` 필드를 손으로 안 쓰고 context에 참조만 기입(계획보다 단순).
  - **장소 id는 바울의 실제 Theographic 사건 occursAt에서 추출**: 큐레이션은 authored 관례지만 occursAt 좌표 정확성을 위해 실재 사건에서 가져옴.
  - **사건 수 18**(16신규+2재사용) — "~16-18" 추정 상단, 1·2·3차 선교 핵심 정차지로 압축.
  - **보너스**: 바울은 이미 character_traits(열정·지혜·인내·겸손·담대함) 보유 → SidePanel 자동 표시(추가 작업 0).

## Learnings
- Do differently next time(베드로·요한 등 인물 확장 시 그대로 재사용):
  - **인물 확장 표준 절차** = ① `data/person_events/<slug>.json` authored 큐레이션(각 사건 `id`=authored-<slug>, sortKey 오름차순, participants=[theographic_id], context에 한글 구절 참조만 기입) → ② `persons.py` `_ERA`/`_NAME_KO` 2줄 등록 → ③ `generate_person_event_verses.py`(context→books+본문) + `load_person_events.py`(authored=true·OCCURS_AT·HAS_PARTICIPANT·CONTAINS_BOOK) → ④ build·api 재빌드·Playwright. 프론트 무변경(데이터만 추가하면 기존 UI 렌더).
  - **occursAt 장소 id는 그 인물의 Theographic 사건에서 추출**하면 좌표 정확성 보장(임의 좌표 X).
  - **Neo4j 적재는 수동**: `deploy.sh`는 `inject_ko_names.py`만 돌리고 `load_person_events.py`는 안 돌림(기존 13명과 동일 패턴, neo4j 볼륨 영속). 공유 neo4j(=프로덕션)에 직접 적재해 반영. **볼륨 리셋 시 전 인물 재적재 필요**(기존 제약).
  - **재사용 생성 스크립트는 여전히 불필요**(YAGNI): 인물당 16~18 사건 수작업 큐레이션이 품질 우위. 파일럿 결과가 이를 재확인.

## Doc updates
- CONTEXT.md promotion: none (여정·저작 사건·사건의 근거 용어 모두 기존재, 새 용어 없음)
- ADR added: none (authored 사건→Neo4j Event authored:true 결정은 ADR-0005가 이미 커버. 이번 학습은 절차 지식이라 회고 로그에 보존 — hard-to-reverse·puzzling·trade-off 3조건 미충족)
