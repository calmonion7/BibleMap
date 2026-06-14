# 회고 — Phase 0 Neo4j 적재
날짜: 2026-06-08
슬러그: phase-0-neo4j-load

## 계획 vs 실제

계획대로 진행됐고, 검증 3쿼리 모두 PASS. 발산은 버그 수정 2건과 인프라 경로 문제 1건.

## 발산 및 학습

**1. Theographic status 필터 — Event·PeopleGroup은 status 필드 없음**
- 계획은 "publish만 적재"였지만, Event·PeopleGroup에 `status` 필드 자체가 없어 0개 적재됨
- `fields.get("status", "publish") == "publish"` 패턴으로 수정
- → CONTEXT.md "publish 레코드" 항목에 반영

**2. Dynamic Workflow 에이전트가 워크트리에 파일을 씀**
- 절대 경로(`${ROOT}`)를 지정했음에도 Write 도구가 워크트리로 리다이렉트
- 수동 복사로 해결했지만, 파일이 많아질수록 누락·불일치 위험
- → BibleMap 프로젝트 `.claude/settings.json`에 `bgIsolation: "none"` 설정 추가 예정

**3. Moses 부모(Amram, Jochebed)가 wip — PARENT_OF/CHILD_OF 없음**
- 예상 가능한 publish 필터 결과. 설계 결정 유지(wip 품질 불확실).
- Q1 검증은 SIBLING_OF(Aaron)로 통과.

## 다음에 다르게 할 것

- fg-run 실행 전 `.claude/settings.json`에 `bgIsolation: "none"` 확인
- 새 엔티티 적재 전 JSON 샘플로 `status` 필드 유무 먼저 확인

## 문서 업데이트

- `CONTEXT.md` "publish 레코드" 항목: 엔티티별 status 필드 유무 추가
- 피드백 메모리: bgIsolation 설정 관련
