# 2026-10-22 — 규칙 원장 + 승인 기록 출처 해시 + 전체 재검 명령 (task 392, 일괄 승급)

## 계획 대비 실제
- 계획대로: rules.json(30개 — 계획 28에서 얼굴 화질 맞춤을 떼고 형식 칸), `recheck.py specs|images|stamp|ledger`, 승인 12장 해시, 현황판 갱신. DoD 6개 통과. 지금 규칙집 통과율 첫 측정 = 명세 0/37(CLIP 77 빼면 1/37) · 승인 그림 0/12.
- 차이: ① 계획 실측 「생성 프롬프트 기록 없는 4장」은 실제 1장 — 국소 편집 2장은 plain-words r2 회차, restyle-r6은 자체 metrics 맨 위 `prompt`에 기록이 있었다. ② J1 2장 못 잼(몸 크롭 상자 없음). ③ 일부 범위 규칙을 37 전부에 거니 통과율이 크게 낮아짐 — 의도한 결과. ④ 배포 가드(validate_canon_pipeline)가 recheck.py의 `NOTES`(params와 같은 이름) 재선언을 잡음 — canon 시험엔 안 걸려 커밋 뒤에야 발견. ⑤ CLIP 77 규칙은 판 단계 전용이라 지금 경로와 무관할 수 있음(존폐 사람 결정).

## 배운 것
- 다음엔 다르게:
  - 「기록 없음」을 계획에 적기 전에 묶음 metrics의 세 자리(`scenes[sid].prompt` · `rounds[*].scenes[sid].prompt` · 맨 위 `prompt`)를 모두 찾아본다.
  - 새 canon 스크립트를 커밋하기 전에 `python3 -m backend.scripts.validate_canon_pipeline`을 한 번 돌린다(모듈 상수 이름이 params와 겹치면 배포가 막힌다 — 이 가드에는 예전 위반 18건이 이미 있어 「새로 생긴 줄」만 grep으로 본다).
  - J1을 승인 그림에 다시 돌리니 틀림 사유 대부분이 실제 결함(큰 하프·중세풍 칼·형 넷) — 「사람이 승인했다 = 맞다」로 두지 말고 재검 표시를 사람 앞에 둔다(승인 취소는 사람).
  - 원장 판(version)을 바꾸면 specs → images 순서로 다시 돌려야 한다(images는 specs.json의 판이 다르면 멈춤 — 의도).

## 문서 반영
- CONTEXT.md 승격: 후보 「규칙 원장」·「지금 규칙집 통과율」·「낡음(재검)」 — 사람 확인 대기(CONTEXT.md에 사용자 미커밋 변경이 있어 손대지 않음)
- ADR 추가: 없음(재검은 표시만 — ADR 260905-104910 그대로)
