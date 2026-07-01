# 2026-07-02 — 얇은 인물 3인 사건 보강 (이사야·요셉·마리아)

## Plan vs actual
- What went as planned:
  - 이사야 4→7, 요셉 5→8, 마리아 5→8. 기존 사건 검토 후 중복 없이 authored Event 3건씩 추가. 실재 rec 노드라 authored Person 불요. API eventCount·journey 좌표·구절 null 0·Playwright 전부 통과.
- Divergences (다음 루프가 읽을 연료):
  - **실재-노드 보강은 가장 가벼운 레인**: authored Person 추가(사사·사울·엘리야)와 달리 authored_persons 로더 불요 + 신규 장소 0(기존 큐레이션 인물은 활동 장소가 이미 그래프에 있음) + persons.py 무변경 → `docker compose restart api`만(재빌드·프론트빌드 불요). 얇은 기존 인물 보강 시 이 경로가 최저비용.
  - **occursAt 근접지 proxy**: 마리아 엘리사벳 방문(유대 산골 엔 케렘, 예루살렘 ~7km)을 별도 장소 신설 대신 예루살렘 노드로 근사. 지도상 예루살렘에 찍힘. 근접·저빈도 지점은 새 authored-place 만들지 않고 proxy가 eco.

## Learnings
- Do differently next time:
  - **구절 약어는 파서 약어맵에 있는 것만** — `generate_person_event_verses.py`는 context 괄호의 EN(`Gen`/`Luke`/`Isa`) 또는 개역 KO(`창`/`눅`/`사`) 약어만 인식한다. "이사야"·"창세기" 같은 **풀네임은 매칭 실패 → books 빈 채로 저장**(📖 근거 칩 없음, 조용한 실패). 신규 사건 context 작성 시 반드시 약어 사용, 한 파일 안에서 기존 스타일(이 프로젝트는 EN Gen/Luke) 따를 것.
  - **얇은 인물 보강 순서**: 파일 먼저 읽어 기존 사건 확인(중복 방지) → 빠진 핵심 장면만 추가 → 장소는 기존 우선 재사용 → restart. "검토 후 추가"가 실제로 중복을 막았다.
  - sortKey 소수점으로 동년/기존 사이에 삽입(마리아 -4.9/-3.9, 이사야 -700.5) — 파일 append여도 journey가 sortKey로 정렬하므로 순서 OK.

## Doc updates
- CONTEXT.md promotion: none (여정·저작 사건 기존)
- ADR added: none (실재 노드 보강은 ADR-0005 authored Event가 커버; 위는 절차 지식이라 회고 로그 보존)
