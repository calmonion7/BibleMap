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

## 사람 판정 원문
(2026-10-18, 판정 페이지에서 복사해 대화에 붙인 글 그대로)

```
task 367 사람 판정
- [G-face] 엔게디 · 사울과 다윗이 마주 보는 그림을 누르세요 (사울이 다윗 쪽으로 고개나 몸을 돌림) → 1, 4, 9, 13, 25, 27, 32
- [G-look] 엔게디 · 다윗이 자르는 옷자락(아래)이 아니라 사울이나 앞쪽을 보는 그림을 누르세요 → 1, 2, 3, 4, 5, 7, 8, 10, 11, 15, 16, 17, 18, 21, 23, 30, 31
- [G-hand] 엔게디 · 다윗의 두 손·칼 위치가 옷자락을 자르는 동작에 맞지 않는 그림을 누르세요 → 3, 4, 7, 8, 10, 11, 12, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30, 33
- [G-guard] 엔게디 · 연필 화풍이 무너지거나, 인물이나 겉옷자락이 사라지거나 엉뚱해진 그림을 누르세요 (손·칼은 앞 문항에서 봤고, 굴 어둠은 이번에 보지 않습니다) → 2, 13, 25, 27, 32, 33
(보여 준 그림: 엔게디 마주 봄 귀속·손 · 처치 Bh + 귀속 B′ + 대조 A + 참고 B + 기준 · 시드 [11, 42, 7, 23, 5, 101, 202, 303] · 카드 폭 356px · 기계 거르기 없음)
```

## 집계
그림 번호 ↔ 팔·시드는 `samples/engedi-backhand/metrics.json` `screens`를 따른다(31번 = 기준). 8장 중 눌린 수. `python3 gen_engedi_backhand.py --tally`가 원문에서 다시 센 값이다.

| | 마주 봄 F | 다윗 시선 G | 손·칼 H | 가드 X |
|---|---|---|---|---|
| A(대조) | 3 | 3 | 4 | 2 |
| B(365, 참고) | 0 | 4 | 6 | 1 |
| B′(귀속) | 3 | 5 | 6 | 2 |
| Bh(채택 후보) | 1 | 4 | 7 | 1 |
| 기준(31) | — | 눌림 | — | — |

- Bh 통과(F ≤ F_A − 2 = 1 · H ≤ 5 · X ≤ 3 · G ≤ 4): F 1 ✓ · G 4 ✓ · X 1 ✓ · **H 7 > 5 ✗** → 미채택.
- 귀속: F_B = 0 < 2라 판정 가능. F_B′ − F_B = 3 ≥ 2 → `David 낱말`.

결론: 미채택 · 귀속 David 낱말 · 마주 봄 A 3·B 0·Bp 3·Bh 1 · 다윗 시선 A 3·B 4·Bp 5·Bh 4 · 손·칼 A 4·B 6·Bp 6·Bh 7 · 가드 A 2·B 1·Bp 2·Bh 1

## 사용자 말
- 2026-10-18, 판정 답과 함께: 「똑같은 판정을 계속하는것 같은데 피드백을 했으면 고쳐져야 하는거 아닌가?」

## 읽은 것
- **B의 마주 봄 0은 이번에도 재현됐고(0/8), 원인은 사울 몸짓 문구의 낱말이다.** 사울 몸짓에 `David`를 넣으면(B′) 마주 봄이 A와 같은 3으로 돌아온다. 366의 두 설명 중 「`David` 낱말」 쪽이다. 몸짓 문장 안의 인물 이름이 그 인물 쪽으로 몸을 돌리게 한다(PROMPTING 14와 같은 꼴).
- **손 문구(Bh)는 손·칼을 고치지 못했다(B 6 → Bh 7).** S0에서 본 대로 「들어 올림」이 사울 손에 붙는 그림이 있다(202). 마주 봄은 B 조합 그대로 낮게 남았다(1).
- **손·칼은 어느 팔에서도 절반 안팎이 눌린다(A 4·B 6·B′ 6·Bh 7).** 네 문항 어디에도 안 눌린 그림은 32장 중 2장이고, 둘 다 지금 명세 A다(6번 = A s5, 19번 = A s11). 365~367 세 회차 동안 문구 한 곳을 바꾸면 한 축이 좋아지고 다른 축(대개 손·칼)이 나빠졌다. 문구 바꾸기로는 손·칼과 마주 봄을 함께 맞추지 못한다고 읽는다.
- 가드는 모든 팔에서 1~2로 낮다. 기준 그림은 G-look에서만 눌렸다(예상대로). 보기 설명이 어긋난 신호는 없다.
- A는 366과 비슷하다(F 3 → 3 · G 2 → 3 · H 3 → 4 · X 1 → 2). 다른 페이지라 회차 간 비교는 참고로만 쓴다.

## 결과 처리
- 미채택 → 명세 `authored-david-en-gedi-saul.json`은 그대로다(부정문 둘·맞보기 절 유지, 다윗 손 「holding」, 다윗 gaze A 객체, `screen_light` 있음). `test_whole_prompt.py`도 그대로다.
