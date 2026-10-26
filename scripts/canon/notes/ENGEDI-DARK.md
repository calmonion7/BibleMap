# 엔게디 「굴 어둠·빛」 — 밝음 낱말 빼기(A)와 먼 굴 입구(B) (task 364)

task 363 r2 판정에서 새 엔게디는 무너짐 7/8이었고, 그중 「굴 어둠·빛」이 6/8이었다(`PROMPT-512.md` r2 집계). 363 회고는 이것이 문구 길이 문제가 아니라고 적었다. 이번 과제는 새 원인 가설 둘을 시험한다.
- 사용자 판정 기준(2026-10-18 그릴링): 「굴 어둠·빛」은 **굴 안 전체가 기준보다 밝음**이다. **굴 입구가 멀리 있는 느낌**이면 더 좋다.
- 화소 밝기는 판정을 대신하지 못한다. 기준보다 어두운 s42·s101도 「어둠·빛」으로 찍혔다. 그래서 성공은 같은 페이지 안의 사람 판정으로만 정한다. 절대 수치는 페이지 사이에 비교하지 않는다(`ENGEDI-TEXT.md`).
- 낱말 가설: 프롬프트가 입구와 빛을 여러 번 직접 부른다(`small bright opening`, `the light from it`, `soft pool of light from the distant cave mouth`, `screen_light`). 근거는 PROMPTING 14(부른 것이 그려진다)와 19(줄일 때는 빼기만, 자리 지킴)다.
  - 약한 반대 근거: `screen_light`가 잘려 들어가지 않았던 353·362에서도 어둠·빛이 많았다. 그래서 구도(입구 거리)를 바꾸는 B도 같이 시험한다.

## 고정 절(결과를 보기 전에 적음 — 실행 중 바꾸지 않는다)
- 문구 diff(영문). 처치는 생성 스크립트 `gen_engedi_dark.py`가 메모리 명세에만 적용한다. 명세 파일은 채택 뒤에만 고친다.
  ```
  처치 A
  whole_background.en:
  - with the cave mouth only a small bright opening far away at the right edge;
  + with the cave mouth only a small opening far away at the right edge;
  screen_light: 필드 삭제
  - Daylight from the small cave mouth far on the right lights only these two men.

  처치 B (= A 위에)
  whole_background.en:
  - with the cave mouth only a small opening far away at the right edge;
  + with the cave mouth only a tiny distant opening at the far end of a long dark passage on the right;
  ```
  - 나머지 글자·순서는 그대로다. 「옮김」은 없다(PROMPTING 19).
  - `the light from it …`·`soft pool of light …`는 남는다. 이번에는 입구 구절과 `screen_light`만 시험한다.
  - 사울의 `looking/facing toward the cave mouth`는 건드리지 않는다(자세 축은 다음 과제).
- 채택 시 한국어 정본(`whole_background.ko`):
  - A: 「굴 어귀는 화면 오른쪽 멀리 작고 밝은 구멍이다」 → 「굴 어귀는 화면 오른쪽 멀리 작은 구멍이다」.
  - B: → 「굴 어귀는 화면 오른쪽 긴 어두운 통로 끝 멀리 아주 작은 구멍이다」.
  - 두 경우 모두 `screen_light` 필드(ko·en·verse)를 지운다.
- 토큰(채팅 틀 포함): r2 510 · A 492 · B 499.
- 생성: 처치 A·B × `params.REF_EDIT_SEEDS`(11·42·7·23·5·101·202·303), 1216×640, Z-Image-Turbo, 363과 같은 경로.
  - 산출은 `~/.local/biblemap-imggen/engedi-dark/<A|B>/s<시드>.png`.
  - 대조 r2(`prompt-512/engedi/s<시드>.png`, 지금 명세 파생 그대로)는 다시 그리지 않는다.
- 판정 페이지: C 화면 하나 + 누른 그림의 이유 화면(`make_ref_edit_page.py judge-dark`).
  - C 화면: 기준(`metrics_lora_scene.REFS["engedi"]`) + r2 8 + A 8 + B 8을 섞기 시드 364(`params.ENGEDI_DARK_SHUFFLE_SEED`)로 섞는다.
  - C 질문은 363과 같다: 「연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요」.
  - 이유 보기(여러 개): 화풍(`style`) · 굴 안이 기준보다 밝다(`bright`) · 굴 입구가 가깝거나 크게 보인다(`mouth`) · 겉옷자락(`cloak`) · 자세(`pose`) · 기타(`etc`).
  - 그림 번호 ↔ r2/A/B·시드 대응은 게시 전에 `samples/engedi-dark/metrics.json` `screens`에 적는다. 폰용 비공개 Artifact, 카드 폭 356px, 기계 거르기 없음.
- 판정 규칙:
  - 「어둠 계열」 = `bright` 또는 `mouth`가 하나라도 눌린 장의 수.
  - 처치 **통과** = 어둠 계열이 r2보다 **적고**, 동시에 전체 무너짐(이유 무관)이 r2 **이하**.
  - 채택 순서: B 통과 → B 채택. B 불통과·A 통과 → A 채택. 둘 다 불통과 → 미채택.
  - 결론 줄: `결론: B 채택|A 채택|미채택 · r2 n/8(밝음 n·입구 n) · A n/8(밝음 n·입구 n) · B n/8(밝음 n·입구 n) · 자세 r2 n·A n·B n`.
- 결과 처리:
  - 채택된 처치의 「화풍」이 r2보다 2장 이상 많으면 채택 전에 멈추고 사람에게 묻는다.
  - 그 밖에는 채택된 처치를 명세(ko·en, `screen_light` 삭제)에 반영한다. 미채택이면 명세를 그대로 두고 기록만 남긴다.

## S0 (시드 7, r2 ↔ A ↔ B)
- A·B 각 67초. 세 장 모두 인물 둘·칼·겉옷자락이 남았다.
- r2 s7: 오른쪽 끝에 밝고 큰 어귀가 있다(사울 바로 뒤).
- A s7: 오른쪽 끝의 밝은 어귀가 사라지고, 굴 안 전체가 어둑하다. 하지만 **사울이 몸을 돌려 다윗을 마주 본다**. 원인 후보는 `screen_light` 삭제다. 「these two men」을 비추던 문장이 빠지면서 두 인물의 관계 문장 비중이 커졌을 수 있다. 자세 축은 이번 판정의 「자세」 보기로 센다.
- B s7: 어귀가 깊은 통로 끝 작은 틈이 되었고, 셋 중 가장 어둡다. 하지만 **종이 둘레 테두리**가 다시 생겼다(362에서 「화풍」으로 찍힌 것). 원인 후보는 `long dark passage`다. 통로를 액자처럼 둘러 그렸을 수 있다. 사울은 A와 같이 돌아섰다.
- 한 장으로 판단하지 않는다(PROMPTING 6). 8시드 판정의 화풍·자세 보기로 확인한다.

## S2 생성 · 눈 확인 (판정 전 — 생성 사고만 거름)
- A·B × 8시드 = 16장(S0 포함), 14장 940초(장당 약 67초). 토큰 A 492 · B 499.
- 생성 사고(인물 실종·검은 화면)는 없다. 16장 모두 인물 둘·칼·겉옷자락이 있다.
- 판정 전에 눈에 띈 것(판정 아님):
  - B는 대부분 어귀가 작고 멀다.
  - B s303·s7은 종이 둘레 테두리가 있다(S0 걱정).
  - A는 s23·s202·s303에 밝은 어귀가 아직 크게 보인다. 남은 `soft pool of light from the distant cave mouth` 때문일 수 있다.
  - A·B 여러 장에서 사울이 다윗을 마주 본다(s11·s23 등). r2는 오른쪽을 보는 장이 더 많다.
- 판정 페이지 **https://claude.ai/artifact/XiDid3PFzo8gkzdNuoeC8Y** (비공개, `make_ref_edit_page.py judge-dark`, 섞기 시드 364, 화면 25·그림 25). 그림 번호 ↔ r2/A/B·시드는 게시 전에 `samples/engedi-dark/metrics.json` `screens`에 적었다.

## 사람 판정 원문
(2026-10-18, 판정 페이지에서 복사해 대화에 붙인 글 그대로)

```
task 364 사람 판정
- [C-engedi] 엔게디 · 연필 화풍이나 장면 뜻이 기준보다 크게 무너진 그림을 누르세요 → 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
- [C-why-engedi-1] 엔게디 그림 1 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-2] 엔게디 그림 2 · 무엇이 무너졌나요? (여러 개) → pose
- [C-why-engedi-3] 엔게디 그림 3 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak, pose
- [C-why-engedi-4] 엔게디 그림 4 · 무엇이 무너졌나요? (여러 개) → bright, cloak, pose
- [C-why-engedi-5] 엔게디 그림 5 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-6] 엔게디 그림 6 · 무엇이 무너졌나요? (여러 개) → bright, mouth
- [C-why-engedi-7] 엔게디 그림 7 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak
- [C-why-engedi-8] 엔게디 그림 8 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak, pose
- [C-why-engedi-9] 엔게디 그림 9 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-10] 엔게디 그림 10 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak, pose
- [C-why-engedi-11] 엔게디 그림 11 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-12] 엔게디 그림 12 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak
- [C-why-engedi-13] 엔게디 그림 13 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-14] 엔게디 그림 14 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak, pose
- [C-why-engedi-15] 엔게디 그림 15 · 무엇이 무너졌나요? (여러 개) → pose
- [C-why-engedi-16] 엔게디 그림 16 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak, pose
- [C-why-engedi-17] 엔게디 그림 17 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-18] 엔게디 그림 18 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak, pose
- [C-why-engedi-19] 엔게디 그림 19 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-20] 엔게디 그림 20 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-21] 엔게디 그림 21 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-22] 엔게디 그림 22 · 무엇이 무너졌나요? (여러 개) → bright, mouth, pose
- [C-why-engedi-23] 엔게디 그림 23 · 무엇이 무너졌나요? (여러 개) → bright, mouth, cloak
(보여 준 그림: 엔게디 굴 어둠·빛 · 처치 A·B + 대조 r2 · 시드 [11, 42, 7, 23, 5, 101, 202, 303] · 카드 폭 356px · 기계 거르기 없음)
```

### 사용자 말(판정과 함께, 글자 그대로)
```
사울과 다윗이 마주보는것이 제일문제고
굴안에 어두워야 하고 입구는 멀게느껴져야함
다윗이 옷자락 자를때 시선처리가 아래를 향해야 하고 양손의 위치 칼위치가 행동에 맞아야함
```

## 집계
그림 번호 ↔ 처치·시드는 `samples/engedi-dark/metrics.json` `screens`를 따른다. 24번(r2 s11)만 「무너짐」이 눌리지 않았다.

| | 무너짐 | 어둠 계열(밝음·입구 중 하나라도) | 밝음 | 입구 | 겉옷자락 | 자세 | 화풍 |
|---|---|---|---|---|---|---|---|
| r2 | 7/8 | 7 | 7 | 7 | 3 | 4 | 0 |
| A | 8/8 | 7 | 7 | 7 | 4 | 7 | 0 |
| B | 8/8 | 7 | 7 | 6 | 4 | 8 | 0 |

- 처치 통과 조건(어둠 계열 < r2, 무너짐 ≤ r2):
  - A: 어둠 계열 7 = r2 7이고 무너짐 8 > 7이다 → 불통과.
  - B: 어둠 계열 7 = r2 7이고 무너짐 8 > 7이다 → 불통과.

결론: 미채택 · r2 7/8(밝음 7·입구 7) · A 8/8(밝음 7·입구 7) · B 8/8(밝음 7·입구 6) · 자세 r2 4·A 7·B 8

- 결과 처리: 미채택이므로 명세(`authored-david-en-gedi-saul.json`)는 그대로 두고 기록만 남긴다. 화풍은 세 쪽 모두 0이라 화풍 가드에 걸리지 않는다.

## 읽은 것
- **밝음 낱말 빼기(A)도, 먼 입구(B)도 사람 눈의 「굴 안이 밝다」를 줄이지 못했다(7·7·7).** 기계는 B 어귀가 작아졌다고 봤지만(S2 눈 확인), 사람 기준(「굴 안이 어둡고 입구가 멀게 느껴짐」)에는 미치지 못했다. 입구 계열만 B에서 한 장 줄었다(7→6).
- **자세가 크게 나빠졌다(r2 4 → A 7 · B 8).** A와 B가 공통으로 바꾼 것은 `bright` 한 낱말과 `screen_light` 문장(「… lights only these two men」) 삭제다. S0에서 본 「사울이 다윗을 마주 봄」이 8시드 판정에서 그대로 확인됐다. 원인 후보는 `screen_light` 삭제다. 낱말 하나 빼기보다 문장 하나 빼기가 관계·시선 문장의 비중을 더 크게 바꾼다. 한 번의 판정이라 단정하지 않는다.
- 이 페이지의 r2 어둠 계열 7/8은 363 r2 페이지의 6/8과 다르다. 보기 설명이 「밝음」과 「입구」로 나뉘었기 때문이고, 절대 수치는 페이지 사이에 비교하지 않는다(`ENGEDI-TEXT.md`).
- 사용자 말의 우선순위(위 원문):
  1. **사울과 다윗이 마주 보는 것이 제일 문제다.** 지금까지 「다음 과제」로 미룬 사울 돌아섬 축이 1순위다.
  2. 굴 안이 어둡고 입구가 멀게 느껴져야 한다. 이번 두 처치로는 안 됐다.
  3. **다윗이 옷자락을 자를 때 시선은 아래를 향하고, 양손과 칼의 위치가 행동에 맞아야 한다.** 새로 나온 기준이다. 지금 명세의 다윗 시선은 「looking toward the king on the right」이다.
- 다음 엔게디 과제의 출발점:
  - `screen_light`는 지우지 않는다(이번 판정에서 자세가 나빠짐).
  - 시선 축(사울 돌아섬 · 다윗 시선 아래 · 손·칼)을 먼저 다룬다. 다윗 시선 구절을 「looking down at the cloak hem he is cutting」 쪽으로 바꾸는 것이 사용자 기준과 직접 맞닿는다.
  - 어둠·빛은 낱말 처치 두 번(362·364)으로 풀리지 않았다. 문구 밖 수단을 검토한다. 단 밝기 후처리는 362에서 종이 테두리가 「화풍」으로 걸렸으므로 그 점을 감안한다.
