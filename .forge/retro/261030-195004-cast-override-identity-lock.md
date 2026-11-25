# 2026-10-30 — task 452 장면 덮어쓰기 정체성 잠금(spec.cast-identity-fixed) · 다윗 생애 단계 middle 신설

## 계획 대 실제
- 계획대로 된 것:
  - 규칙을 테스트 먼저 넣어 실제 4건을 잡았다.
  - 헤브론 덮어쓰기를 지우고 카드 나이 글을 「in his 30s」로 넓혔다.
  - 사람 답(둘 다 s23)을 반영해 DoD 1~8이 모두 통과했다.
  - 전 규칙 통과 명세는 5/38로 작업 전과 같다.
- 어긋난 것:
  - **david-middle 체격 broad**([저작]): david-prime과 같게 두면 히람과 카드 층이 1칸만 달라 (h)에 걸렸다. 수염 full 안은 같은 장면 나단과 (d)에 걸렸다. 355 회고의 「새 id가 다른 인물과 1필드만 다름」이 다시 나왔다.
  - **다윗 귀환 512/512**: 카드 값을 되돌리니 525토큰이라, 구절 요소·사람 메모가 아닌 꾸밈말 4곳을 뺐다. 여유는 0이다.
  - **판정기 기준이 사울로 고정**: `judge_face_canon.py`의 같은 사람 기준이 사울로 하드코딩돼 있었다. 다윗에게 돌렸으면 「사울과 가장 다른 장」을 골랐을 것이다. 묶음 첫 id로 일반화했다.
  - **david-middle 나이 글이 정본에 안 실림**: 덮어쓰기 값을 그대로 카드로 올린 「about 50, fuller face with lines at the eyes and brow」로 그린 8장이 8/8 30대였다. 시드 23 한 장 반복 1회로 「weathered … deep lines … gray at the temples」로 고친 뒤 8시드를 다시 그렸다(GPU 약 13분 추가).
  - **stash 실수**: 작업 전 테스트와 비교하려고 `git stash push -- .`를 했다. 사용자의 미커밋 파일 5개도 함께 치워졌다가 pop으로 복원됐다.
  - **테스트 여파 3곳**(`make_night_page.NAME` · `judge_spec` m2 · 출생 지역 키): 「id를 바꾸면 테스트도 찾아라」(446 회고)를 미리 적용하지 않아 전체 테스트 실패로 뒤늦게 찾았다.

## 배운 것
- 다음엔 다르게:
  - **카드 나이 글을 새로 쓰거나 옮기면, 8시드 전에 고정 시드 정면 한 장을 먼저 그려 눈으로 본다.** 장면 덮어쓰기에서 「통과」하던 글도 정본 초상에서는 안 먹을 수 있다. 「lines at the eyes」류 부드러운 낱말은 30대로 나오고, 「gray at the temples」·「weathered」처럼 색·질감 낱말이 나이를 싣는다.
  - **생애 단계 id를 새로 나눌 때는 `check_cast_v2` (d)(h)를 카드 쓰자마자 돌린다.** 동시대 인물(히람·나단)과 class 1칸 차이 충돌이 거의 매번 난다. 가를 칸은 [저작] 체격·수염 중 단계 흐름에 맞는 쪽으로 고른다.
  - **작업 전 상태 비교는 `git worktree add --detach <scratch> HEAD`로 한다. `git stash`는 쓰지 않는다.** 이 레포는 사용자의 미커밋 변경이 늘 섞여 있다.
  - **id를 옮기거나 새로 만들 때 finder에 `grep -rn '"<id>"' *.py batch/*.py`(이름표·변형 고정 절)를 넣는다.** 테스트 파일만이 아니다.
  - 512 근처 장면(다윗 귀환 512·엔게디 511)은 카드 글을 바꾸는 작업의 DoD에 토큰 측정을 넣는다.
- 지킬 것:
  - 판정 화면에 Claude 눈 확인 한 줄(`--note`)을 실었다. 사람 답이 기계 고름과 2/2 일치했다(446은 2/2 갈림).
  - 사람에게 보이기 전에 「모두 아님」이 확실한 후보 묶음을 고쳐서 판정 하나를 아꼈다.

## 문서 갱신
- CONTEXT.md 승급: 없음(용어집 「카드 층 / 얼굴 층」이 이미 같은 말)
- ADR 추가: 없음

## 후속 후보

<!-- followup: fu-acecd0bd603d | source: cast-override-identity-lock | task: 452 | date: 2026-10-30 | status: open | taken: - -->
- 다윗 귀환 장면이 512/512로 여유가 0이다. 이 장면을 다시 쓸 때는 줄일 자리를 먼저 정하거나, 그리기 전에 토큰 관문을 둘 것.
  근거: task 452 S4 — 카드 값 복원 525 → 꾸밈말 4곳을 빼서 512(notes/DAVID-LIFE-STAGE-MIDDLE.md 「다윗 귀환 512토큰」).

<!-- followup: fu-a189b20ed0b3 | source: cast-override-identity-lock | task: 452 | date: 2026-10-30 | status: open | taken: - -->
- 생애 단계 id의 v1 `hair` 칸(「dark curly hair」)이 카드 나이 글(david-middle 「gray at the temples」)과 어긋난다. 판정기 vocab이 이 칸을 써서 회색 머리를 감점한다. 카드 글이 바뀐 id의 v1 칸 정합 점검 규칙 후보.
  근거: task 452 S5 — judge-david-middle.json 이유 글 「머리와 수염이 회색빛이 돌아 어두운 색 조건에서 벗어난다」.
