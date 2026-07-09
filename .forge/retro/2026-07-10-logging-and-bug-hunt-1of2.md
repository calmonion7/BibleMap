# 2026-07-10 — 로깅 방출 규약 정본화 + config 배선 + 침묵 지점 로그 보완 (task#149)

## Plan vs actual
- 계획대로: 4슬라이스 전부 완수 — CONVENTIONS §13 규약 정본화·CLAUDE.md 포인터, `_configure_logging()` 배선, root 직호출 3곳 정규화, 백엔드 침묵 except 4곳·프론트 빈값-폴백 catch 9곳 로그 보완(명시 목록 그대로, 확장 0). LOG-ONLY 유지, 커밋 `4a3d925` push·배포.
- Divergences:
  1. **계획의 "확정된 규약"이 틀렸음 — `uvicorn.error propagate=False`는 기동/에러 라인을 통째로 삼킨다.** PortfoliOn task#162에서 이식한 트리오 차단이 원인: `uvicorn.error`는 자체 핸들러가 없고 부모 `uvicorn` 로거(자체 핸들러·propagate=False 기본)로 전파해 출력하므로, 전파를 끊으면 갈 곳이 없다. uvicorn 기본 config는 이미 `uvicorn`/`uvicorn.access`에 propagate=False라 **root 중복 emit은 애초에 존재하지 않는 문제**였다. 수정: `uvicorn.error` 제외(코드 주석+CONVENTIONS §13에 이유 정본화). 1차 배포 후 `docker logs`가 access 2줄뿐인 것을 실측해서 발견 — DoD에 "기동 라인 확인"이 없었다면 조용히 넘어갔을 결함.
  2. `logger.info("[Startup] Neo4j 인덱스 준비 완료")` 1줄 계획 외 추가 — logger.info 0건이라 "INFO 가시" DoD를 관찰할 수단이 없었음. 규약의 "info=라이프사이클 마일스톤"에 부합.
  3. Playwright 관계 뷰 텍스트 검증 1회 False — 대기 1.5초 부족(타이밍), 2.5초에서 정상. 코드 무관.

## Learnings
- Do differently next time:
  - **타 프로젝트 선례 이식 시 "확정된 규약"도 메커니즘 단위로 실측 재검증할 것.** 선례가 검증됐다는 가정이 깨졌다(PortfoliOn도 같은 코드로 기동 라인이 소실되고 있을 것 — 타 프로젝트 자원이라 미수정, 사용자에게 보고 승계). 로깅 배선 검증 DoD에는 "우리 로그가 보인다"뿐 아니라 **"원래 있던 라인(uvicorn 기동)이 여전히 보인다"**를 반드시 포함.
  - uvicorn 로거 위상 상식: `uvicorn.error`는 핸들러 없음(부모 전파로 출력), `uvicorn`/`uvicorn.access`는 자체 핸들러+propagate=False 기본 → basicConfig root 핸들러와의 중복은 기본 구성에선 없다.
  - Playwright 텍스트 어서션은 wait 2.5초+ 또는 셀렉터 대기 사용(1.5초는 관계 뷰 API 왕복에 빠듯).
- 버그 헌트(part 2) 시드: 이번 스윕에서 본 `lru_cache(maxsize=None)` 2곳·stale 무효화 수동 패턴은 CONCERNS와 일치 — 헌트 렌즈에 이미 반영돼 있음.

## Doc updates
- CONTEXT.md promotion: none (도메인 용어 아님 — 구현 규약은 CONVENTIONS §13에 이미 정본화)
- ADR added: none (uvicorn.error 제외는 가역적 config + CONVENTIONS·코드 주석으로 충분 — 3조건 미충족)
