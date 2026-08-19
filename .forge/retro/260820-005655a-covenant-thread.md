# 2026-08-20 — 언약 스레드 (task#247)

> fg-loop 자동 주행으로 미뤄졌던 회고. 2026-08-20 일괄 승급 중 승급 기준을 넘어 뒤늦게 기록한다.

## 계획 대비 실제
- 계획대로 된 것: 언약 5건 저작, `overlays.covenants()` + `GET /covenants`, `validate_covenants.py` PASS, TimelineView 언약 리본.
- 이탈:
  - **계획의 "`restart`만" 가정이 틀렸다.** 신규 라우트를 추가했으므로 `docker compose restart api`로는 반영되지 않고 `up -d --build api`가 필요했다. backend는 볼륨 마운트가 아니라 이미지 COPY이기 때문.
  - 언약 리본이 필터로 그 시대 사건이 전부 걸러지면 함께 숨겨짐(미해결, 잔여 개선 여지).
  - keyVerses에 장:절 뱃지 없음 — `/covenants`가 `{verseId,textKo,textEn}`만 주고 장/절 분리 필드가 없어서(미해결, 경미).

## 배움
- 다음에 다르게 할 것:
  - **"데이터만 바꿨으니 restart"는 절반의 진실이다 — 반영 방법은 *무엇을 바꿨나*가 아니라 *그것이 이미지 안인가 볼륨 안인가*로 갈린다.** 정확한 3분기: ① `data/` 오버레이만 변경 → `docker compose restart api`(볼륨 마운트라 파일은 이미 최신, `lru_cache`만 비우면 됨) ② 백엔드 파이썬 코드·신규 라우트 변경 → `docker compose up -d --build api`(이미지 COPY라 재빌드 필수) ③ 프론트 변경 → `cd frontend && npm run build`(`:8080`이 `dist`를 마운트, HMR 아님). task#132가 ①을, 이 태스크가 ②를 각각 비싸게 배웠다 — 한쪽만 기억하면 반대 방향에서 다시 걸린다.
- 확인된 것(유지):
  - **오버레이 startDate는 새로 산정하지 않고 기존 Neo4j 사건 startDate를 재사용**한다. 언약 오버레이와 정본 사건이 같은 연대계를 공유해야 타임라인에서 어긋나지 않는다.

## 문서 반영
- CONTEXT.md 승급: none(운영 절차라 용어집 대상 아님) · ADR 추가: none
- 별도 승급 없음. (3분기 규칙은 프로젝트 메모리에 이미 정확히 기록돼 있음 — 이 회고는 ②를 비싸게 배운 사례를 남긴다.)
