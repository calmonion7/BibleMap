# 2026-07-11 — 인물 소개 재설계 (2/2): PersonIntro 정체성+관문 프론트 (task#159)

## Plan vs actual
- What went as planned:
  - S1~S4 전 슬라이스 완료. `PersonIntro.jsx` 신규(정체성 헤더·소개문+근거칩·인물 성품·관문 요약), `App.jsx` intro 분기를 SidePanel→PersonIntro 교체. Part 1이 노드에 주입한 role/intro/verses/traits 소비.
  - DoD 전량 충족 — 큐레이션 인물 소개가 PersonIntro로 렌더, 모든 산문이 근거 구절과 연결, 관문 3탭 점프 동작, 함께등장/동시대/그래프이웃 리스트 부재. Playwright로 아담·요나·이사야 확인, 데스크톱·모바일(390) 정상.
  - 양피지 포털 모달·VerseLangTabs·테마 토큰·set-state-in-effect 규칙 모두 기존 패턴 답습. build✓ lint 무경고.
- Divergences:
  - **실행 형태 치환(주요, 의도적)**: 플랜은 fg-run 기본(Dynamic Workflow)을 함의했으나 슬라이스가 엄격 직렬(S1→S2→S4, S3는 S1 흡수)·단일 신규 컴포넌트라 "단일 에이전트로 충분하면 워크플로우 생략" 예외로 직접 실행. eco on → 메인 세션이 eco 출력 규율 채택.
  - **파생 메타 출처**: era·eventCount가 노드 속성에 없고 `/persons/curated`에만 존재 → PersonIntro가 curated fetch·id 조회. eventCount는 허브 표시값(아담 8)과 동일 출처 사용(event-ids 13 아님).
  - **발자취 카운트 정의**: 플랜 "정차 장소 수" 모호 → 단위 "곳"에 맞춰 고유 placeId 수(아담 2). UAT에서 사용자 확인 대상으로 남김.
  - **journeyStops prop 재사용**: App이 이미 fetch 중이라 중복 요청 회피 위해 prop 전달(플랜은 `/journey`를 출처로 나열).
  - App.jsx 시트 억제 가드(~412)는 무접촉(Non-goals·surgical), 낡은 주석 1줄만 갱신.

## Learnings
- Do differently next time:
  - **직렬 단일컴포넌트 프론트 작업은 fg-run 워크플로우 생략·직접 실행이 재사용 패턴.** Part 1의 "메커니즘 치환을 발산으로 명기" 교훈과 같은 결 — 형태 치환을 run.md에 명기하면 봉인 시 혼선 없음. 워크플로우는 병렬성·규모가 실재할 때만.
  - **Person 파생 메타(era·eventCount)의 단일 출처는 `/persons/curated`** — 노드(`/node/{id}`)엔 없다. 소개 헤더 era·관문 사건 카운트는 curated 조회 필수. **사용자에게 보이는 같은 성격의 카운트는 반드시 같은 출처로** — 허브 "사건 N"과 관문 "사건 N"이 어긋나지 않게 둘 다 curated eventCount(8), `/event-ids`(13, 더 넓음) 아님.
  - **상위(App)가 이미 fetch한 상태는 새 자식 컴포넌트에 prop으로 — 중복 요청 금지.** 플랜 Source of truth가 엔드포인트를 출처로 적었어도 상위가 이미 보유하면 prop이 eco 정답(journeyStops 사례).
  - **플랜의 모호한 카운트 정의는 단위(곳/건/명)로 해소하고 UAT에서 확인** — "정차 장소 수"→고유 placeId(곳). 저작·데이터 카운트 모호성은 저비용 UAT 확인으로 넘긴다.
  - **Playwright SPA 테스트 함정 2건**: ① `goto`가 동일 문서·해시만 변경이면 remount가 안 일어난다 — 마운트 시 1회만 해시를 복원하는 앱(useStageNavigation)은 인물 전환이 안 먹으므로 **인물당 신규 page/context**로 열 것. ② 오프스크린 상세 시트(transform 숨김, display 아님)가 body inner_text를 오염 → 부재 검증은 **intro 컨테이너(`div[style*="max-width: 560px"]`)로 스코프**. (첫 실행 실패 원인이 앱이 아니라 이 테스트 함정이었음.)

## Doc updates
- CONTEXT.md promotion: none — "인물 소개 (Person Context)" 용어가 fg-ask 그릴링 때 이미 **관문 역할까지 포함**해 신설·정확, 이번 실행은 그 정의를 그대로 구현. 실행 중 신규/변경 용어 없음.
- ADR added: none — 발산(실행 형태·메타 출처·카운트 정의)은 모두 가역·명료·경미한 구현 선택으로 ADR 3조건 미충족.
