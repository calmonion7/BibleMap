---
author: calmonion
decided: 2026-08-01 19:50
---
# 테스트 러너는 프론트 순수 함수에만 도입한다 — 백엔드 유닛 테스트·React 렌더 테스트·PR CI는 의도적 미도입

이 리포지토리에는 pytest·vitest가 없고 `*_test.py`·`*.test.jsx`가 한 건도 없다. "정식 테스트 프레임워크 도입"을 검토한 결과, **프론트 순수 함수 모듈(`urlState.js`·`mapGeo.js`·`mapRingController.js`)에 vitest만 도입하고 나머지는 도입하지 않기로** 한다. vite가 이미 있어 vitest는 devDependency 한 줄이고, `encodeHash`/`parseHash`는 왕복 대칭이, `mapGeo`의 11개 export는 입력→GeoJSON 순수 변환이라 인프라 없이 값이 바로 나온다.

의도적으로 뺀 것들과 사유:

- **백엔드 라우트 계약(pytest + TestClient)** — Neo4j 없이 테스트 가능한 라우트가 `tours.py`·`words.py` 둘뿐이다. 나머지 9개 라우트는 전부 DB를 타서, 유닛 테스트로 만들려면 드라이버 목킹이 필요하거나 라이브 DB에 결합된다(후자는 이미 게이트에서 겪는 문제다). 3줄짜리 `requirements.txt`에 러너를 얹는 값보다 회수가 적다.
- **Cypher 결과** — 라이브 DB가 필요하고, `validate_event_chronology.py`가 이미 그 층을 검증한다.
- **React 렌더/상호작용** — jsdom + testing-library 인프라가 크고, Playwright 화면 검증이 이미 이 영역을 덮는다.
- **PR 시점 CI** — 이 프로젝트는 PR을 쓰지 않는다(415커밋 중 머지 커밋 1건, 열린 PR 0건, 사실상 `main` 단일 브랜치). 안 쓰는 워크플로에 게이트를 다는 셈이다.

근거는 회귀의 실제 분포다 — 이 프로젝트에서 난 회귀는 대부분 **데이터 정합**이었고 거기엔 `validate_*.py` 13종이 이미 돌고 있다. 회고 이력에 "유닛 테스트가 있었으면 잡았을 회귀"가 보이지 않는다. 커버리지 숫자를 위한 테스트는 유지비만 남긴다.

## Consequences

- FastAPI 라우트의 응답 계약은 계속 무방비다. 회귀는 Playwright 검증과 사용자 피드백에 의존한다. 라우트 계약 회귀가 **실제로** 발생하면 그때 이 결정을 다시 연다 — 이 ADR은 "영원히 안 한다"가 아니라 "지금은 값이 없다"이다.
- PR 워크플로를 도입하게 되면 PR CI 항목은 즉시 재검토 대상이 된다.
