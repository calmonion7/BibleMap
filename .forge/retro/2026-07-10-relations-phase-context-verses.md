# 2026-07-10 — 인물 관계 국면 문맥 절 보완 (task 148)

## Plan vs actual
- 계획대로 된 것: 슬라이스 5개(저작·병합 → 기계검증 → 프리베이크 → API·Playwright 검증 → AUTHORING.md 보강) 완주. 리서치 워크플로(12배치 sonnet, 읽기전용, 90만 토큰)가 370국면 전건 제안, 단일 writer 병합으로 315 적용·거부 0, git 대비 무손실(관계 171·국면 627·기존 필드 변경 0), 프리베이크 `null:0`, Playwright 표본 4인 정확 렌더. 커밋 7695414 push·배포 성공.
- Divergences:
  - **자체완결 생략 55건(15%) — 계획의 "극소수" 추정보다 훨씬 많음.** 사유는 앵커가 주체·행위·결과를 한 절에 완결 / 장 첫 절이라 앞 확장 불가 / 족보 정형구 / 인접 절이 무관한 별개 단락. 밀도비례(규칙 7)와 합치라 수용 — 억지 문맥이 오히려 규칙 위반. 앵커 절의 자체완결 비율은 데이터 특성상 구조적(정형구·장 경계)이라 다음 견적 때 10~15%를 기본값으로.
  - **Playwright 셀렉터 2회 수정**: ① 관계 행의 상대 이름은 큐레이션 인물이면 여정 점프 버튼(stopPropagation) — 클릭하면 화면 이탈. 오버뷰의 `.rel-chip`(국면 라벨 칩)을 직접 클릭하면 근거 레이어가 바로 열려 초점 쌍 진입도 불필요. ② SPA에서 해시만 다른 `page.goto()`는 리로드되지 않아 이전 화면에 머묾 → 인물 전환마다 `page.reload()` 강제 필요.
  - **워크플로 결과는 output 파일 파싱 실패 → `journal.jsonl`(에이전트별 result 라인) 집계**가 정확 경로(진단 안내대로). 370건 무손실 수집.
  - 승인 질문·UAT 인간 확인은 메모리 지침(확인 묻지 않음)에 따라 자가 수행, 근거를 STATUS `verified:`에 기록.

## Learnings
- Do differently next time:
  - **대량 저작 제안엔 "에코 필드 + 기계검증" 조합이 싸고 강력.** 제안에 앵커 verse를 그대로 에코시키고, 병합 시 에코 일치·같은 책/장·범위가 앵커 절 번호 포함을 기계로 검사 → sonnet 12배치에서도 거부 0. 적대적 검증 페이즈 없이 정확도 확보(내용 저작이 아닌 범위 선정이라 가능 — 신규 관계 저작엔 여전히 task 146의 적대적 검증 필요).
  - **relations 화면 Playwright는 `.rel-chip` 클릭 + 인물 전환마다 `reload()`** — 상대 이름 클릭 금지(여정 점프), 해시 goto만으론 SPA 미갱신. (메모리 feedback_playwright_testing에 반영.)
  - **워크플로 산출 회수는 journal.jsonl이 정본** — 태스크 output 파일은 표시용이라 잘릴 수 있음.
- 사소/일회성: 프리베이크 stats(kept/filled/null)는 verseText만 집계하고 contextKo 생성은 미집계 — context 채움 여부는 별도 스크립트로 확인해야 함.

## Doc updates
- CONTEXT.md promotion: none (앵커 절/문맥 범위 두 층 정의는 ask 단계에서 이미 반영).
- ADR added: none (되돌리기 어려운 결정 없음 — context 부여 원칙은 AUTHORING.md 규칙 1에 귀속, 실행 중 S5로 반영 완료).
- 관련: AUTHORING.md 규칙 1 보강(context 원칙 부여·생략 예외 기준·2~6절 창)은 계획된 슬라이스로 실행 중 완료, 여기 기록.
