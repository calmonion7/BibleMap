# CLAUDE.md

## Project note

- 로깅은 `.forge/codebase/CONVENTIONS.md`의 "로깅 방출 규약" 절 준수(절 번호는 재매핑마다 밀릴 수 있어 이름으로 참조) — 백엔드 모듈 logger 통일(`backend/app/`에 print·root 직호출 금지), `[Component]` prefix, 프론트 빈값-폴백 catch엔 `console.warn`.
