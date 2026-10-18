# 엔게디 마주 봄 귀속·손 — B′(B에 `David` 낱말)·Bh(B + 다윗이 자락을 들어 올림) (task 367)

사용자 1순위 「사울과 다윗이 마주 보는 것」(`ENGEDI-DARK.md` 「사용자 말」)을 다룬다. 366 회고의 다음 과제 (가)·(나)를 한 판정 페이지로 함께 한다(사용자 2026-10-18 「가,나 둘다」).
- 지금까지 마주 봄을 0/8로 만든 것은 365 B 조합뿐이다(366: A 3·B1 4·B2 3·B 0). 대가는 손·칼 6/8이고, 원인은 B1 쪽(사울 등 돌림 문구)이다(PROMPTING 22).
- (가) 귀속 팔 B′(코드·metrics 이름 `Bp`): B의 마주 봄 0이 사울 몸짓의 `the man on the left` ↔ `David` 낱말 차이 때문인가, 두 변경의 조합 때문인가.
- (나) 채택 후보 Bh: B에서는 두 손이 자락을 함께 움켜쥐고 칼이 묻힌다(그릴링 실측). 자락이 들리면 잡는 손과 베는 손, 칼날이 갈려 보인다는 가설.

## 고정 절(결과를 보기 전에 적음 — 실행 중 바꾸지 않는다)
- 바탕 = 지금 명세(365 A 채택본). 처치는 `gen_engedi_backhand.py`가 메모리 명세에만 적용한다. 명세 파일은 채택 뒤에만 고친다.
- 문구 diff:
  ```
  B (365 그대로 — 재사용 그림의 문구, gen_engedi_gaze.DIFF_B)
  figures[saul].gesture.en: not looking back → his back to the man on the left
  figures[saul].gesture.ko: 어귀 쪽을 바라보고 뒤를 돌아보지 않는다 → 어귀 쪽을 바라보며 등을 왼쪽 사람 쪽으로 둔다
  relation.en: … and does not look back; → … with his back to David;   그리고   ; their eyes do not meet → (삭제)
  relation.ko: … 웅크려 있고 뒤를 돌아보지 않으며, → … 다윗에게 등을 둔 채 웅크려 있고,   그리고   . 둘의 시선은 마주치지 않는다 → (삭제)

  처치 B′ (= B 위에, 귀속 팔)
  figures[saul].gesture.en:
  - facing toward the cave mouth, his back to the man on the left, his long cloak
  + facing toward the cave mouth, his back to David, his long cloak
  figures[saul].gesture.ko:
  - 어귀 쪽을 바라보며 등을 왼쪽 사람 쪽으로 둔다
  + 어귀 쪽을 바라보며 다윗에게 등을 둔다

  처치 Bh (= B 위에, 채택 후보)
  figures[david].gesture.en:
  - one hand holding the hem of the king's cloak that lies on the ground, the other hand cutting it with a small knife
  + one hand lifting the hem of the king's cloak off the ground, the other hand cutting it with a small knife
  figures[david].gesture.ko:
  - 한 손으로 땅에 끌린 사울의 겉옷자락을 잡고 다른 손의 작은 칼로 가만히 벤다
  + 한 손으로 사울의 겉옷자락을 땅에서 들어 올리고 다른 손의 작은 칼로 가만히 벤다
  ```
  - 나머지 글자·순서는 그대로다. 「옮김」은 없다(PROMPTING 19). 다윗 `gaze`·`screen_light`는 건드리지 않는다.
  - 스크립트는 B를 365 diff에서 다시 파생해 365 metrics `prompts['B']`와 글자까지 같은지 단정한다(`b_matches_365`).
- 토큰(채팅 틀 포함, `check_scenes.zimage_tokens`, 실측 2026-10-18): A 511 · B 510 · Bp 506 · Bh 508.
- 생성: Bp·Bh × `params.REF_EDIT_SEEDS`(11·42·7·23·5·101·202·303), 1216×640, Z-Image-Turbo, 365·366과 같은 경로(`run_scene.gen_zimage`). 산출 `~/.local/biblemap-imggen/engedi-backhand/<Bp|Bh>/s<시드>.png`. 대조 A·B(`engedi-gaze/<A|B>/`)는 다시 그리지 않는다.
- 판정 페이지: 한 화면에 축 하나, 4문항. 문항 글자는 366 `AWAY_SCREENS` 그대로다(가드에 칼 없음).
  - 그림: 기준(승인본) + A 8 + B 8 + B′ 8 + Bh 8 = 33장, 섞기 시드 367(`params.ENGEDI_BACKHAND_SHUFFLE_SEED`). 네 화면 모두 같은 순서.
  - 그림 번호 ↔ 팔·시드는 게시 전에 `samples/engedi-backhand/metrics.json` `screens`에 적는다. 폰용 비공개 Artifact, 카드 폭 356px, 기계 거르기 없음.
- 판정 규칙. 팔마다 8장 중 눌린 수: 마주 봄 F, 다윗 시선 G, 손·칼 H, 가드 X. 대조는 같은 페이지의 A.
  - **Bh 통과** = F ≤ F_A − 2 **그리고** H ≤ H_A + 1 **그리고** X ≤ X_A + 1 **그리고** G ≤ G_A + 1.
  - Bh가 통과하면 `Bh 채택`, 아니면 `미채택`. B·B′는 결론(채택)에 쓰지 않는다.
  - 귀속(B′): F_B ≥ 2이면 `판정 불가`(이 페이지에서 B의 마주 봄 0이 재현되지 않음). 그 밖에 F_B′ − F_B ≥ 2이면 `David 낱말`. 그 밖은 `조합`.
  - F_A ≤ 1이면 F ≤ F_A − 2를 맞출 수 없다. 그래도 규칙대로 계산하고 「읽은 것」에 적는다.
  - 기준 그림이 G-face·G-hand·G-guard에서 눌리면 보기 설명이 어긋난다는 신호다. 결론은 그대로 계산하고 「읽은 것」에 적는다. G-look은 예외(기준에서도 다윗이 사울 쪽을 봄).
  - 결론 줄: `결론: Bh 채택|미채택 · 귀속 David 낱말|조합|판정 불가 · 마주 봄 A n·B n·Bp n·Bh n · 다윗 시선 A n·B n·Bp n·Bh n · 손·칼 A n·B n·Bp n·Bh n · 가드 A n·B n·Bp n·Bh n`.
  - 집계·결론 줄은 `python3 gen_engedi_backhand.py --tally`가 판정 원문 + `screens`로 다시 계산한다.
- 결과 처리: Bh 채택이면 B diff와 Bh diff를 명세(ko·en)에 반영하고, `test_engedi_matches_adopted_A`를 「명세 파생 = metrics `prompts['Bh']`」 검사로 바꾼다. 미채택이면 명세를 그대로 두고 기록만 남긴다.

## S0 (시드 202, A ↔ B ↔ B′ ↔ Bh — 판정 전, 생성 사고만 거름)
- A: 사울이 몸·고개를 왼쪽 다윗 쪽으로 돌린다. 다윗은 아래 옷자락을 보며 칼날이 또렷하다(365·366 S0 그대로).
- B(365): 사울이 등을 돌려 앉고 고개는 오른쪽 어귀 쪽이다. 다윗 두 손이 땅의 자락 위에 모이고 칼이 작다.
- B′: 사울이 몸·고개를 다윗 쪽으로 돌려 마주 본다. 다윗은 아래를 보며 칼날이 또렷하다.
- Bh: 자락이 들렸지만 들어 올린 손은 **사울 쪽**(사울이 제 겉옷을 손으로 들고 있음)이다. 사울 고개도 왼쪽을 향한다. 다윗은 땅의 자락에 칼을 댄다.
- 넷 다 인물 둘·칼·겉옷자락이 있다. 검은 화면·인물 실종 같은 생성 사고는 없다. 한 장이라 효과로 읽지 않는다.

## S2 생성 · 눈 확인 (판정 전 — 생성 사고만 거름)
- B′·Bh × 8시드 16장(장당 약 67~69s, S0 2장 134s + 나머지 14장 961s). A·B·B′·Bh 시드별 몽타주로 봤다.
- 32장 모두 인물 둘·겉옷자락이 있다. 검은 화면·인물 실종 같은 생성 사고는 없다. 효과는 사람 판정으로만 정한다.

## 판정 페이지
- `make_ref_edit_page.py judge-backhand`로 만들어 폰용 비공개 Artifact로 게시했다(2026-10-18, 5.00MB · 4화면 · 33장). 번호 ↔ 팔·시드는 `samples/engedi-backhand/metrics.json` `screens`를 따른다(31번 = 기준).
