---
author: calmonion
decided: 2026-08-19 20:52
---
# 시대 경계(ERA_BANDS)는 `frontend/src/eraBands.js`와 `backend/app/routes/stats.py` 두 곳에만 선언한다

통사 연표(task#271)가 기존 인물 연표와 같은 시대 경계를 써야 했다. 상수는 원래 `TimelineView.jsx` 안에 있었는데, 컴포넌트 파일에서 export하면 ESLint `react-refresh/only-export-components`가 막고, 새 화면에서 재선언하면 **세 번째 복제**가 된다. 그래서 전용 모듈 `frontend/src/eraBands.js`로 승급하고, 배포 게이트 `validate_era_bands_consistency.py`가 스크래핑하는 대상 경로를 그 파일로 옮겼다. **선언 위치는 정확히 두 곳(프론트 `eraBands.js` · 백엔드 `stats.py`)이며, 세 번째 복제를 만들지 않는다.**

공유 설정 파일이나 생성 스크립트로 한 곳에 모으는 방법도 있었지만, 상수 8개를 위해 빌드 단계를 늘리는 값이 이 규모에 맞지 않는다고 봤다. 대신 두 곳을 두되 **정규식 스크래핑 검증기를 하드 게이트로** 두어 어긋남을 배포 전에 잡는 기존 구조(task#255)를 유지했다.

## Consequences

- `eraBands.js`의 `const ERA_BANDS = [` 리터럴 모양은 **검증기의 파싱 계약**이다. 포매팅을 바꾸거나 값을 변수로 빼면 배포 게이트가 깨진다 — 이 취약성은 승급 전에도 있었고 그대로 남는다.
- 다만 스크래핑 대상이 200줄 넘는 컴포넌트에서 25줄 전용 모듈로 좁아져, 무관한 편집이 게이트를 깨뜨릴 확률은 줄었다.
- 새 화면이 시대 밴드를 그릴 때는 반드시 `eraBands.js`를 import한다. 재선언은 검증기가 잡지 못하는 종류의 드리프트(3곳 중 2곳만 일치)를 만든다.
- 시대 이름·순서는 `persons.py`의 `_ERA_ORDER`와도 일치해야 하며 검증기가 함께 단언한다(경계값은 두 곳, 이름·순서는 세 곳).
