# 2026-07-16 — 모션 개편 1/3: 파운데이션 (task#189, fg-next all 사후 일괄 승급)

## Plan vs actual

- 계획대로: S1 오디트(find-animation-opportunities 스킬 → 기회 7·기각 6 보고서) → S2 토큰 7종+reduced-motion 가드 → S3 스테이지 7곳 → S5 매트릭스 13/13. ADR-0024 실행 중 기록.
- 이탈: ① S4 범위 확장(+) — 오디트 최고 레버리지(전역 모달 8곳 overlay-in/modal-in, pressable)를 "전역 전환" goal에 부합해 포함. ② apple-design 미로드(emil-design-eng만 로드해 값 검수 — CSS 전환 범위와 제스처 중심 스킬의 겹침이 적다고 판단). ③ 여정 📖 모달 검증이 선재 크래시(2/3 회고 참조)에 걸려 지도 무관 경로(단어 분포 모달)로 대체.

## Learnings

- Do differently next time:
  - **디자인 태스크는 "오디트 스킬 → 산출 보고서가 이후 슬라이스의 정본" 구조가 유효** — 계획(fg-ask 시점 추정)이 가정한 세부는 오디트가 교정한다. 다음 디자인 계획엔 "오디트 산출과 계획 문구 충돌 시 오디트 우선" 조항을 슬라이스에 명시해 두면 이탈로 기록할 필요조차 없다(3/3에서 실제 충돌 발생).
  - **CSS `transition`은 프로퍼티 단위가 아니라 선언 통째로 승계된다** — 인라인 `style.transition`이 있으면 클래스의 `transition: transform`은 완전히 무시됨. `.pressable`류 클래스 모션을 인라인 스타일 코드베이스에 도입할 땐 인라인 transition 목록에 transform을 병기해야 한다(이번에 카드 3종 수정).
  - **reduced-motion 토큰 붕괴(1ms) 패턴의 함정 하나**: `animation-fill-mode: both` + 스태거 delay는 duration이 0이어도 delay 동안 from 상태(불가시)를 유지 → `animation-delay: 0 !important` 전역 무효화를 반드시 동반(ADR-0024 본문에 기록됨).
  - 대량 인라인 치환(sed/python)은 ① raw string 치환이 `\'`를 그대로 삽입, ② 주석 낀 JSX 정규식 미매치 — 두 사고 모두 직후 빌드가 잡았다. **치환 배치마다 즉시 빌드**가 회복 비용을 분 단위로 막는다.

## Doc updates

- ADR: 0024(무의존 CSS 토큰 모션 시스템 + reduced-motion 토큰 붕괴) — 실행 중 선기록, 회고 추가분 없음.
- CONTEXT.md: 없음(모션 어휘는 구현 세부 — 용어집 비대상).
- 메모리: project_biblemap_status에 모션 시스템·클래스 어휘·specificity 함정 갱신(드라이브 종료 시).
