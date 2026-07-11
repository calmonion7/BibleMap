# 2026-07-11 — 인물 소개 재설계 (1/2): 구절 근간 person_context 저작·주입 (task#159)

## Plan vs actual
- What went as planned:
  - S1~S4 전 슬라이스 완료. `data/person_context/AUTHORING.md`, `people.json`(35인·125절), `validate_person_context.py`(위반 0), `inject_person_context.py`(35노드 SET), `nodes.py` verses 파싱 추가, api 리빌드 후 `/node/{id}`가 role·intro·verses(프리베이크 본문) 반환.
  - book_context/character_traits 파이프라인(생성→JSON→inject SET→노드 속성)을 그대로 답습. 프리베이크는 `generate_verse_text.py`에 `bake_person_context()` 추가로 재사용(250필드, null 0).
  - CONTEXT.md 용어 "인물 소개 (Person Context)"는 fg-ask 그릴링 때 이미 신설·정확 → 회고에서 손댈 것 없음.
- Divergences:
  - **생성 메커니즘 치환(주요, 의도적)**: 플랜 S2는 선례 `generate_person_traits.py`(haiku API 스크립트) 답습으로 데이터 생성이었으나, 실행 환경에 `ANTHROPIC_API_KEY`가 없었고 소개 산문 품질 기준(각 진술 구절 근거·교리 중립)이 추론 모델 저작에 더 맞아, 35인 role/intro/verses를 **워크플로우 서브에이전트(sonnet, eco)가 직접 저작**(7배치 구조화 출력→JS 병합→단일 writer 기록). `generate_person_context.py`는 재생성 경로 아티팩트로 작성(미실행). DoD는 전량 충족.
  - 노드 속성명: 플랜 DoD의 `verses`를 그대로 사용(기존 Person 프로퍼티와 충돌 없음 확인 — 별칭 불필요).
  - 인라인 적대적 리뷰 findings 2건(모두 low, 미수정): ① `generate_verse_text.py` main()에서 `bake_person_context()` 호출이 "Done" 배너·육안검증 블록 뒤에 위치 → 완료 로그 오도 + person_context만 육안검증 출력 없음(데이터 위험 없음, 독립 함수). ② `nodes.py` verses 파싱 블록이 traits 블록과 동일 스코프에서 `import json as _json` 재실행(멱등·무해, 기존 traits 스타일 답습).

## Learnings
- Do differently next time:
  - **generate-* 데이터 작업에서 "API 키 부재 + 산문 품질 기준" 조건이면 스크립트 실행 대신 워크플로우 서브에이전트 직접 저작이 재사용 패턴.** 선례 스크립트는 재생성 아티팩트로 작성해 남기되, 실데이터는 에이전트가 저작 → 품질↑, 키 의존↓. run.md에 메커니즘 치환을 발산으로 명기하면 봉인 시 혼선 없음.
  - **병렬 저작 파일 충돌은 "저작 단계 무파일화"로 원천 차단**: 저작 에이전트는 파일을 쓰지 않고 구조화 출력만 반환 → JS에서 결정적 병합 → 단일 writer 1회 기록. 관계 저작 회고의 "단일파일 순차" 교훈을 워크플로우로 옮긴 형태 — 순차보다 병렬 가능하면서 충돌은 없음. 대량 저작은 이 패턴 기본.
  - **노드 신규 속성 반환**: 문자열 속성(role/intro)은 `nodes.py` clean_props 통과로 코드 변경 없이 반환되지만 JSON 문자열 속성(verses)은 traits 블록을 미러한 `json.loads` 파싱 블록이 별도 필요. 새 문자열 필드가 실수로 exclude 집합에 들어가지 않게 주의.
  - **프리베이크 스크립트에 새 bake_* 추가 시 main()의 완료 배너 앞에 호출을 배치**하고 육안검증 출력도 관례대로 붙일 것(이번엔 배너 뒤라 로그가 완료 후에도 계속 도는 것처럼 보임). getbible 프리베이크 전체 재실행은 멱등이라 다른 데이터에 무해(kept).

## Doc updates
- CONTEXT.md promotion: none (용어 "인물 소개 (Person Context)"는 fg-ask 그릴링 때 이미 신설·정확, 실행 중 신규/변경 용어 없음)
- ADR added: none (메커니즘 치환은 ADR 3조건 미충족 — 재생성 가능해 비가역 아님·명료·트레이드오프 경미)
