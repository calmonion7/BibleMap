# 2026-07-08 — 관계 뷰 가족 서열/속성 note 헤더 표시(task 138)

## Plan vs actual
- What went as planned: S1(JSON note 5개)·S2(백엔드 note 필드)·S3(개요+초점 헤더 렌더) 모두 계획대로. 워크플로우 없이 직접 실행(3 슬라이스 소규모라 단일 처리가 더 저렴·빠름). 가족 5개에 note, 그 외 관계 무변경, 엔드포인트가 note 전달, 데스크톱+모바일 렌더 확인.
- Divergences: 사실상 없음. 현장 결정 2건 — (1) note를 관계 객체 2번째 키(유형 뒤)에 넣기 위해 JSON 라운드트립이 기존 포맷 바이트 동일 보존함을 확인 후 스크립트로 삽입, (2) 초점 헤더는 가로 flex 행이라 "유형 아래"를 세로 컬럼 래핑으로 구현.

## Learnings
- Do differently next time:
  - **관계/커넥션 엔드포인트 로컬 검증 footgun**: `:8000`은 호스트 미노출이고 `/person/{node_id}/relations`의 `node_id`는 slug가 아님(예: david → `rec1ZMFtfbEvoGC73`). 검증은 `:8080/api` 프록시 + `/api/persons/curated`에서 node_id를 먼저 뽑아서. 다음에 곧장 이 경로로.
  - **미커밋 diff 위에서 JSON을 스크립트로 편집할 때**: `json.dumps(ensure_ascii=False, indent=2)` 라운드트립이 원본과 바이트 동일한지 먼저 확인하면, 기존 미커밋 변경에 포맷 노이즈를 얹지 않고 목표 필드만 추가할 수 있다. 이번엔 동일 확인 후 note 5줄만 깨끗이 추가됨.
  - **Playwright는 기본 브라우저 경로 사용**: `PLAYWRIGHT_BROWSERS_PATH=0` 오버라이드를 주면 패키지 디렉터리에서 브라우저를 못 찾아 실행 실패. env 오버라이드 없이 실행.
- 범위 밖 관찰: 작업 시작 시점부터 `relations.json`에 이 작업과 무관한 이벤트(phase) 데이터 622줄이 미커밋 상태로 존재. 내 note 5줄과 같은 파일이라 커밋 경계 이슈 발생 → 자동 커밋 보류하고 사용자에게 분리 여부 확인 넘김. (봉인은 forge 상태 정리일 뿐 코드 git 커밋과 별개이므로, 이 미커밋 상태는 별도 처리 필요.)

## Doc updates
- CONTEXT.md promotion: none (note는 표시 필드일 뿐 도메인 개념 아님)
- ADR added: none (되돌리기 어렵거나 트레이드오프 있는 결정 없음 — 소규모 표시 필드 추가)
