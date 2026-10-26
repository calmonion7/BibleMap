# 2026-10-21 — task 355 인물 생애 단계 분할(david-prime·david-elder·solomon-prime) + 1/2 판정이 찾은 기존 값 교정

fg-loop 자동 봉인(회고 건너뜀) 뒤 사용자 요청으로 쓴 늦은 회고. 근거: `.forge/done/261021-230254-cast-life-stage-split/run.md`.

## 계획 대비 실제
- 계획대로 된 것: S1 값 교정(오인용 소품 5건·성전 식양 대상 28:11·도엑 22:19·요압 20:8·요나단 성인·골리앗 놋경갑), S2 id 분할, DoD 6개 모두 기준선 → 통과. 그림 생성 0, 사용자 미커밋 4파일 지문 그대로.
- 어긋난 것:
  - **장면 안 cast id는 다섯 자리에 있다**: `figures[].cast` · 다른 인물의 `gaze` · 판 프롬프트 `{cast:<id>}` · `judge.figures` · **구역 이름**(regions 열쇠 · figures/stages `region` · `guide.depth/shape` 열쇠). 계획은 `figures[].cast`만 적었고, 구역 이름을 「영역 표지」로 보고 그대로 두려다 `check_scenes`가 「judge.figures 인물의 구역 없음」으로 잡았다(규약: judge 인물 = 같은 이름 구역 = cast id). 10장면을 JSON 왕복(서식 바이트 동일 확인 뒤)으로 고침.
  - 카드 층 전체 구별 (h)가 두 번 걸림: 새 id가 동시대 다른 인물과 1필드만 다름(david-prime·joab, david-prime·solomon-prime) → 수염 class로 가름.
  - 인용 (c2)가 두 번 걸림: 기억으로 쓴 「만 이년 후」(원문 「이 주년 후에」)·「왕이 돌아와서」(원문 「돌아와」).
  - 골리앗 장면 한 장 프롬프트는 david-boy 배정으로 566 → 557토큰, 512 안에 못 듦 → 예외 유지·이유 갱신.
  - scripture-reviewer 틀림 0·약함 5. 제가 쓴 값의 약함(골리앗 근거 단계 [직접]→[저작], 다윗 나이 추론에 삼하 3:3, 솔로몬 봉헌 나이 가정 명시, solomon-prime role 근거·물려받은 소품)은 고쳤다.
  - S0 경계(그릴링 과제)는 사람에게 묻지 않고 fg-loop 계약 때 성경 근거 기본값으로 정했다(사용자 지침 「확인 묻지 말 것」).

## 배운 점
- 다음엔 다르게:
  - **cast id를 바꾸거나 나눌 때는 문자열 grep이 아니라 JSON 경로로 참조를 전부 뽑는다**(값이 그 id인 곳 + 열쇠가 그 id인 곳). 그다음 바꾼 장면만 `check_scenes`로 먼저 돌린다. 「region은 cast와 무관」 같은 추측으로 남기지 않는다.
  - 새 id의 카드 층을 정한 뒤 바로 `check_cast_v2` (h)를 돌려 동시대 인물(같은 왕조·같은 장면 무리)과 2필드 이상 다른지 본다 — 원래 id를 복사해 나이대만 바꾸면 다른 인물과 겹치기 쉽다.
  - `_why` 인용은 쓰기 전에 `verses.json`에서 그 절을 꺼내 복사한다(개역한글 「이 주년」·「돌아와」처럼 기억과 다름).
  - 나이 추론은 「간격 합」만으로 쓰지 말고 기준점(즉위 나이·자녀 출생)을 같이 인용한다 — 재판정이 그 빈틈을 잡았다.
  - 새로 나눈 id는 `frozen/<id>.png`가 없어 얼굴 그림을 넣는 IP 경로에서 못 쓴다. 그 경로를 다시 쓸 과제는 정본 그리기부터 넣는다.
  - (forge) 무시된(.gitignore) 계획 파일은 `git mv -k`가 오류 없이 아무것도 안 한다 — 승급은 `mv`로 하고 결과를 `ls`로 확인.

## 문서 갱신
- CONTEXT.md 승격: 없음(생애 단계 분할 원칙은 「카드 층 / 얼굴 층」에 이미 있고, id 이름 사다리·정본 그림 없는 id는 `scripts/canon/cast/CAST.md`에 적음)
- ADR 추가: 없음
- eval: 없음 — 세 함정(장면 안 cast id 다섯 자리·인용 글자·카드 층 겹침)은 모두 기존 `check_scenes`·`check_cast_v2`가 잡았다
- 다음 과제 후보:
  - 성품 낱말 목록 (g)에 `calm`·`steady`·`composed`가 없다(재판정 지적). 넣으면 solomon·solomon-prime 얼굴 층과 david `face.skin`(sun-warmed [직접])이 걸려 정본 문구를 바꿔야 한다 — 그림이 있는 정본이라 사람 결정
  - 골리앗 장면 557토큰: 방패병·골리앗 카드 층 머리쓰개·신분과 장면 차림 충돌 정리, 옛 판 단계 `{costume:david}`·「boy of fifteen」
  - david-prime·david-elder·solomon-prime 정본 그리기(IP 경로가 필요해질 때)
