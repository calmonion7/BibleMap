# 2026-06-20 — 성경 개요 뷰 (task 55): 66권 장르별 카드 그리드 3번째 탭

## 계획 vs 실제
- 계획대로 진행된 것: S1~S4 모두 완료, Playwright 4개 체크 통과
- 이탈:
  - testament 필터: 플랜이 'OT'/'NT' 예시를 썼지만 Neo4j 저장값은 '구약'/'신약'. 인플라이스 수정.
  - onSelectNode 인수: 플랜 스펙은 `{ id, label }` 객체였지만 실제 selectNode는 id 문자열만 수신. 인플라이스 수정.
  - 적대적 검토에서 추가 발견 3건(genre=null 무음 소멸·startYear 필터·빈 상태 UI) → task-56 fix-forward.

## 학습
- 다음에 다르게 할 것:
  1. **플랜 작성 전 Neo4j 실제 저장값 확인**: enum 값(testament, genre), 타입(list vs string) 등은 CONTEXT.md 또는 `curl`로 먼저 확인. testament가 '구약'/'신약'으로 저장된다는 사실은 이미 CONTEXT.md에 있었지만 플랜 작성 시 참조 안 함 — 반복 패턴.
  2. **API 스펙에 응답 샘플 포함**: 필드 이름만 나열하지 말고 실제 값 예시를 한 줄이라도 기술하면 형식 불일치를 사전에 잡을 수 있음.
  3. **기존 API 재사용 전 "이 용도에 맞는가" 명시적 검토**: `/books`는 타임라인 배치용 필터(startYear 없는 책 제외)가 있어 개요 뷰 재사용 시 구조적 결함이 생김. 재사용하기 전에 API 설계 의도를 확인하거나 전용 엔드포인트 분리를 플랜에 포함시켜야 함. (→ 경고를 문서화하는 것보다 API를 고치는 것이 맞다는 판단 — task-56 S2로 처리)
  4. **genre=null 등 데이터 결함 방어는 실행 시 추가**: Playwright 통과만으로는 null/빈값 케이스가 가려짐. 데이터 의존도가 높은 컴포넌트에는 null 방어를 기본으로 포함.

## 문서 업데이트
- CONTEXT.md 승급: 없음 (/books startYear 필터 경고 → 경고 대신 API 분리로 해결, task-56)
- ADR 추가: 없음
