# 엔게디 마주 봄 — 365 B를 둘로 나눔: B1(등 돌림 긍정문만)·B2(맞보기 절 빼기만) (task 366)

사용자 1순위 「사울과 다윗이 마주 보는 것이 제일 문제」(`ENGEDI-DARK.md` 「사용자 말」)를 다룬다.
- 365 B(A 위에 바꾼 곳 셋)는 마주 봄을 0/8로 없앴다. 하지만 손·칼·가드가 6/8로 나빠져 불통과했고, 바꾼 곳을 묶어서 원인을 귀속하지 못했다(`ENGEDI-GAZE.md` 「읽은 것」, PROMPTING 21).
- 가설 B1: 부정문(`not looking back`·`does not look back`)이 부른 「돌아봄」이 그려진다(PROMPTING 14).
- 가설 B2: 「눈이 마주침」 낱말(`their eyes do not meet`)이 맞보기를 부른다. 빼기는 다른 축을 흔들 수 있다(PROMPTING 20).

## 고정 절(결과를 보기 전에 적음 — 실행 중 바꾸지 않는다)
- 바탕 = 지금 명세(365 A 채택본, 다윗 `gaze` = `looking down at the hem he is cutting`). 처치는 `gen_engedi_away.py`가 메모리 명세에만 적용한다. 명세 파일은 채택 뒤에만 고친다.
- 문구 diff:
  ```
  처치 B1 (등 돌림 긍정문만)
  figures[saul].gesture.en:
  - facing toward the cave mouth, not looking back, his long cloak
  + facing toward the cave mouth, his back to David, his long cloak
  figures[saul].gesture.ko:
  - 어귀 쪽을 바라보고 뒤를 돌아보지 않는다
  + 어귀 쪽을 바라보며 다윗에게 등을 둔다
  relation.en:
  - Saul crouches looking toward the cave mouth and does not look back;
  + Saul crouches looking toward the cave mouth with his back to David;
  relation.ko:
  - 사울은 어귀 쪽을 바라보며 웅크려 있고 뒤를 돌아보지 않으며,
  + 사울은 어귀 쪽을 바라보며 다윗에게 등을 둔 채 웅크려 있고,
  (「; their eyes do not meet」·「. 둘의 시선은 마주치지 않는다」는 그대로)

  처치 B2 (맞보기 절 빼기만)
  relation.en:
  - … cuts the corner of the cloak trailing on the ground; their eyes do not meet
  + … cuts the corner of the cloak trailing on the ground
  relation.ko:
  - …. 둘의 시선은 마주치지 않는다
  + …
  ```
  - 나머지 글자·순서는 그대로다. 「옮김」은 없다(PROMPTING 19). 다윗 `gaze`·`screen_light`는 건드리지 않는다.
  - **B1은 365 B의 정확한 절반이 아니다.** 사울 몸짓 문구가 365 B는 `his back to the man on the left`, B1은 `his back to David`다(512 상한 때문). 「B ≈ B1 ∪ B2」 비교는 근사로만 읽는다.
- 토큰(채팅 틀 포함, `check_scenes.zimage_tokens`, 실측 2026-10-18): 바탕 A 511 · B1 512(상한에 딱 맞음) · B2 505.
- 생성: B1·B2 × `params.REF_EDIT_SEEDS`(11·42·7·23·5·101·202·303), 1216×640, Z-Image-Turbo, 365와 같은 경로(`run_scene.gen_zimage`). 산출 `~/.local/biblemap-imggen/engedi-away/<B1|B2>/s<시드>.png`. 대조 A·B(`engedi-gaze/<A|B>/`)는 다시 그리지 않는다.
- 판정 페이지: 한 화면에 축 하나, 4문항, 모두 「문제 있는 그림을 누르세요」 한 방향.
  - 그림: 기준(승인본 `samples/face-ab/approved-engedi.png`) + A 8 + B1 8 + B2 8 + B(365) 8 = 33장, 섞기 시드 366(`params.ENGEDI_AWAY_SHUFFLE_SEED`). 네 화면 모두 같은 순서.
  - `G-face`: 「사울과 다윗이 마주 보는 그림을 누르세요 (사울이 다윗 쪽으로 고개나 몸을 돌림)」 — 그림 전체. 365와 글자 그대로.
  - `G-look`: 「다윗이 자르는 옷자락(아래)이 아니라 사울이나 앞쪽을 보는 그림을 누르세요」 — 그림 전체 + 다윗 쪽 확대(왼쪽 0~0.55 폭). 365와 글자 그대로.
  - `G-hand`: 「다윗의 두 손·칼 위치가 옷자락을 자르는 동작에 맞지 않는 그림을 누르세요」 — `G-look`과 같은 확대. 365와 글자 그대로.
  - `G-guard`: 「연필 화풍이 무너지거나, 인물이나 겉옷자락이 사라지거나 엉뚱해진 그림을 누르세요 (손·칼은 앞 문항에서 봤고, 굴 어둠은 이번에 보지 않습니다)」 — 그림 전체. **365에서 바꾼 문항은 이것 하나**(「칼」을 빼 손·칼 축과 겹치지 않게, 365 회고). 그래서 가드 X는 365와 회차 간 비교에 쓰지 않는다.
  - 그림 번호 ↔ 처치·시드 대응은 게시 전에 `samples/engedi-away/metrics.json` `screens`에 적는다. 폰용 비공개 Artifact, 카드 폭 356px, 기계 거르기 없음.
- 판정 규칙. 팔마다 8장 중 눌린 수: 마주 봄 F, 다윗 시선 G, 손·칼 H, 가드 X. 대조는 같은 페이지의 A.
  - 처치(B1·B2만) **통과** = F ≤ F_A − 2 **그리고** H ≤ H_A + 1 **그리고** X ≤ X_A + 1 **그리고** G ≤ G_A + 1.
  - 채택 순서:
    1. 통과한 처치가 있으면 F가 적은 쪽.
    2. F가 같으면 H가 적은 쪽, 그것도 같으면 X가 적은 쪽.
    3. 그것도 같으면 B2(토큰 여유 7 — 다음 손·칼 과제 몫).
    4. 통과한 처치가 없으면 미채택.
  - F_A ≤ 1이면 F ≤ F_A − 2를 맞출 수 없다. 그래도 규칙대로 미채택으로 계산하고, 「읽은 것」에 「대조 마주 봄이 이미 낮아 이 페이지로 가를 수 없음」을 적는다.
  - 365 B(참고 팔)는 숫자만 적고 결론에 쓰지 않는다. 「읽은 것」에서 F·H 각각 B1·B2 중 어느 쪽이 B에 가까운지 귀속을 읽는다.
  - 기준 그림이 `G-face`·`G-hand`·`G-guard`에서 눌리면 보기 설명이 기준과 어긋난다는 신호다. 결론은 그대로 계산하고 「읽은 것」에 적는다. `G-look`은 예외(기준에서도 다윗이 사울 쪽을 봄 — 눌리는 것이 맞다).
  - 결론 줄: `결론: B1 채택|B2 채택|미채택 · 마주 봄 A n·B1 n·B2 n·B n · 다윗 시선 A n·B1 n·B2 n·B n · 손·칼 A n·B1 n·B2 n·B n · 가드 A n·B1 n·B2 n·B n`.
  - 집계·결론 줄은 `python3 gen_engedi_away.py --tally`가 판정 원문 + `screens`로 다시 계산한다(손 집계 실수 방지, 365 회고 「그대로 둘 것」).
- 결과 처리: 채택된 처치를 명세(ko·en)에 반영한다. 미채택이면 명세를 그대로 두고 기록만 남긴다.

## S0 (시드 202, A ↔ B ↔ B1 ↔ B2 — 판정 전, 생성 사고만 거름)
- A: 사울이 몸·고개를 왼쪽 다윗 쪽으로 돌려 그를 본다. 다윗은 아래 옷자락을 보며 칼을 댄다(365 S0 그대로).
- B(365): 사울이 등을 돌려 오른쪽 어귀를 본다.
- B1: 사울 몸은 어귀 쪽으로 조금 틀렸지만 고개를 다윗 쪽으로 돌려 내려다본다. 다윗은 아래를 보며 칼로 자락을 벤다.
- B2: 사울이 A처럼 다윗 쪽으로 몸·고개를 돌린다. 다윗은 아래를 보며 칼을 댄다.
- 넷 다 인물 둘·칼·겉옷자락이 있다. 검은 화면·인물 실종 같은 생성 사고는 없다. 한 장이라 효과로 읽지 않는다.

## S2 생성 · 눈 확인 (판정 전 — 생성 사고만 거름)
- B1·B2 × 8시드 16장(장당 약 67~71s, 합 약 18분). A·B1·B2·B 시드별 몽타주로 봤다.
- 32장 모두 인물 둘·칼·겉옷자락이 있다. 검은 화면·인물 실종 같은 생성 사고는 없다. 효과는 사람 판정으로만 정한다.

## 판정 페이지
- `make_ref_edit_page.py judge-away`로 만들어 폰용 비공개 Artifact로 게시했다(2026-10-18, 4.99MB · 4화면 · 33장). 번호 ↔ 처치·시드는 `samples/engedi-away/metrics.json` `screens`를 따른다(7번 = 기준).

## 사람 판정 원문
(사람 답 대기)
