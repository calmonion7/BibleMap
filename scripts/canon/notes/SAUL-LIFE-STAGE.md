# 사울 생애 단계 3분할 — `saul` · `saul-elder` · `saul-old` (task 446)

## 왜

사울 정본 카드(`saul` — 40대·검은 수염)와 재위 후반 장면 명세(약 70·희끗한 수염)가 어긋나 있었다. 본문과 프로젝트 연대를 대 보면 **명세 쪽이 맞다**.

| 정차지 | 연대(data/person_events yearLabel) | 사울 나이(삼상 13:1 「사울이 왕이 될 때에 사십 세라」, 선출 BC 1050) | id |
|---|---|---|---|
| 미스바·야베스·길갈 즉위·믹마스·길갈 아말렉 | BC 1050~1045 | 40~45 | `saul` |
| 기브아 수금 | BC 1026 | 약 64 | `saul-elder` |
| 기브아 창 | BC 1020 | 약 70 | `saul-elder` |
| 놉 학살 | BC 1012 | 약 78 | `saul-elder` |
| 엔게디 | BC 1011 | 약 79 | `saul-elder` |
| 엔돌 · 길보아 | BC 1011 · 1010 | 약 79~80 | `saul-old` |

정본 카드가 「재위 중 40대로 고정」이라 수금·창 장면은 `cast_override.card`로 나이·수염·머리를 덮어써 왔다. 이는 CONTEXT 「카드 층 / 얼굴 층」의 규칙(카드 정체성 값은 id 하나에 한 값 — 나이대가 크게 갈리면 id를 생애 단계로 나눈다)을 어긴 것이다. 솔로몬·다윗 선례대로 id를 나눴다.

## 정한 것

1. **`saul-elder` 새 id**(표시 이름 「사울(재위 후반)」) — 기브아 창 `cast_override.card`를 카드로 올림: ageBand `elder` 「about 70, a deeply wrinkled old face, lined forehead and cheeks」 · beardVolume `trimmed` 「close-trimmed grey-streaked beard」 · silhouette `broad` 「broad shoulders, a strong solid chest」 · headOutline `bare` 「short greying hair cut close」. v1 `age` 「aging tall king」. 얼굴 층·키·지물·neg는 `saul` 그대로(같은 사람). 한 id 한 값이라 수금(64)·엔게디(79)도 대표값 70.
2. **`saul-old` 나이** 「in his 60s」 → 「about 80」. 옛 값은 `[저작](같은 사람 연속)`이었고 `saul-elder`(70)보다 어려 순서가 뒤집혀 있었음.
3. **`saul`** 은 즉위~아말렉 다섯 정차지만(값 그대로 — 정본 얼굴 지문 불변).
4. **장면 명세** 네 곳(수금·창·놉·엔게디)의 `cast`·구역·문구 자리표를 `saul-elder`로. 수금·창 `cast_override`(card)와 그 근거를 지우고 `stage_why`를 새 id 근거로 고침. 엔게디 `cast_override`(웅크림 사정)는 남김.
5. **엔게디 표정 칸** 「looking toward the cave mouth」를 뺌 — 카드 문구가 길어져 한 장 프롬프트가 517토큰(상한 512)이 됐고, 같은 뜻이 자세 칸(「facing toward the cave mouth」)에 이미 있음 → 511토큰.
6. **판정기** `judge_face_canon.py` — 같은 사람 묶음(`params.FACE_ID_SAME_PERSON`의 사울 묶음)은 옛 `VS` 문구(「사울 정본과 가장 확연히 구별되는 1장」)가 거꾸로라, 「사울 정본과 같은 사람으로 보이면서 나이는 카드대로 늙은 1장」(`SAME`)으로 고름.

## 전수 조사 — 장면 `cast_override`가 카드 정체성 값을 덮어쓰는 곳(2026-10-28 측정)

- 사울 기브아 수금·창(4값 모두) → **이번에 해소**.
- 다윗 귀환 `david-elder`·`shimei`(4값), 헤브론·솔로몬 출생 `david-prime`(ageBand) → 후속 후보.
- 두 어미 `solomon`(headOutline — 면류관 차림이라 허용 범주).

## 재검 셈(그림은 안 고침 — ADR 260905-104910)

`recheck.py specs`·`images`(venv314, 2026-10-28) — 바꾸기 전(HEAD) → 뒤:

| 셈 | 전 | 뒤 | 까닭 |
|---|---|---|---|
| 전 규칙 통과 명세 | 5/38 | 3/38 | `spec.cast-canon-face` 38/38 → 32/38: `saul-elder` 정본 얼굴 없음(4장면) · `saul-old` 카드 나이가 바뀌어 지문 낡음(엔돌·길보아) — 사람 답 반영 뒤 풀림 |
| `derive.no-inflating-build` 실패 | 9 | 8 | 수금·창 덮어쓰기 문구(「a strong solid chest」)가 카드로 올라가 놉·엔게디도 따름 |
| 칸 통과 | 1473/1599 | 1468/1599 | |
| 잰 규칙 모두 통과 승인 그림 | 4/15 | 3/15 | 기브아 창 s7 · 놉 승인 그림이 「명세 바뀜」으로 낡음(수금 J1은 fail → 못 잼) |

## 정본 얼굴 후보 · 기계 판정

`gen_face_canon.py --who saul-elder saul-old --out ~/.local/biblemap-imggen/face-canon-v4` — 8시드(5·7·11·23·42·101·202·303) × 정면·3/4 = 32장(한 장 약 48초). `judge_face_canon.py --dir … --who <id>`(인물마다 따로) → `judge-<id>.json`.

| 인물 | 정면 점수(vocab·style·clean·head 평균) 높은 순 | 상위 3 | 기계 고름(`SAME`) |
|---|---|---|---|
| saul-elder | s42 9.12 · s202 9.10 · s11 8.88 · s23 8.88 · s303 8.88 · s7 8.88 · s101 8.75 · s5 8.75 | s42 · s202 · s11 | **s11** — 「정본 사울과 얼굴 윤곽·눈매·눈썹·코·입이 가장 가깝게 이어짐 · s42·s202는 수염이 길고 풍성해 다른 사람처럼 느껴짐」 |
| saul-old | s23 9.25 · s303 9.20 · s202 8.75 · s101 8.62 · s42 8.62 · s5 8.62 · s7 8.62 · s11 8.50 | s23 · s303 · s7(3/4) | **s303** — 「세 후보 모두 같은 사람이라 단정하기 어려움 · 그중 두꺼운 일자 눈썹·눈매·곧은 코 비율이 가장 가까움」 |

- `same` 점수 칸은 두 번 모두 0으로 돌아옴 — 판정자가 채우지 않음(이유 글만 씀). 점수는 쓰지 말고 이유 글만 읽을 것.
- Claude 눈 확인(원래 화소, 정본 `saul` 옆에 나란히 · 측정):
  - **saul-elder** — 8장 모두 약 65~70으로 보임. 카드 「greying」보다 머리가 거의 하얗고, 수염이 「close-trimmed」보다 풍성함. 길고 각진 얼굴형·곧은 코는 `saul`과 이어지며, s42·s23은 눈썹이 짙어 가장 가까움.
  - **saul-old** — 8장 모두 75~80. 나이는 `saul-elder`와 확실히 갈림(어깨까지 오는 장발·가슴까지 오는 수염). 다만 카드 「thin gray hair」와 달리 숱 많은 물결 장발이고, `saul`과 같은 사람이라는 느낌은 elder보다 약함(판정자도 같은 말).

## 사람 판정 화면

**https://claude.ai/artifact/N96ZDPomXoZZNma9PGz1aX** (비공개 · 폰용 · 1.42MB)

```sh
python3 batch/make_canon_face_page.py <out.html> --dir ~/.local/biblemap-imggen/face-canon-v4 --who saul-elder saul-old \
  --task "saul-life-stage task 446" --title "사울 생애 단계 정본" --verse "saul-elder=삼상 18:10" "saul-old=삼상 28:20"
```

- 한 화면 한 사람(이전·다음, 1/2 · 2/2). 화면마다 근거 구절 원문(개역한글) · 카드 정의 · **같은 사람 기준 = 지금 `saul` 정본(40대, 고르는 칸 아님)** · 후보 정면 8장(3/4 단추, 기계 점수·이유) · `saul-old`는 지금 정본 s23 「그대로 둠」 · 「모두 아님」. 메모·답 복사는 마지막 화면에만.
- 「전부 기계 추천으로」 → `{"saul-elder":"s11","saul-old":"s303"}`.
- 폰(390×844) Playwright: 페이지 오류 0 · 가로 넘침 없음(scrollWidth 390) · 단계 이동·답 복사 동작(측정).
- `make_canon_face_page.py`에 이번에 더한 것: `--task`·`--title`·`--verse` · 같은 사람 기준 얼굴(`params.FACE_ID_SAME_PERSON`) · 한 화면 한 질문. 이전 기본값(인자 없이)은 제목·답 머리가 그대로.

## 답 반영

```sh
cd scripts/canon
python3 batch/apply_canon_faces.py '<화면에서 복사한 두 줄>' --dir ~/.local/biblemap-imggen/face-canon-v4 --task "saul-life-stage task 446"
P=~/.local/biblemap-imggen/.venv314/bin/python
HF_HUB_OFFLINE=1 $P recheck.py specs && HF_HUB_OFFLINE=1 $P recheck.py images
```

- `keep`(saul-old 지금 정본 s23 그대로)을 고르면 `apply_canon_faces.py`는 손대지 않는다 — 카드 나이가 80으로 바뀌어 `prompt_sha`가 낡았으므로, 그 정본을 새 카드에 맞는다고 본 것이면 `cast/saul-old.json` `canon_face.prompt_sha`를 `gen_face_canon.prompt_sha("saul-old")`로 갱신해야 규칙 `spec.cast-canon-face`가 풀린다.
- `none`이면 카드 문구부터 다시(나이 낱말이 그림에 안 먹는 경우) — 같은 시드 한 장씩 규칙 반복.

## 후속 후보

1. **장면 `cast_override`가 카드 정체성 값(ageBand·beardVolume·silhouette·headOutline)을 덮어쓰지 않는다**를 원장 규칙으로 — 남은 곳: 다윗 귀환 `david-elder`·`shimei`, 헤브론·솔로몬 출생 `david-prime`(ageBand). 생애 단계 id로 나누거나 카드로 올린 뒤 규칙화.
2. **정본 전이**(참조 어댑터 PuLID·InfiniteYou 등 — fu-7fb5a2c109fb)는 이 작업의 `saul-elder` 정본으로.
3. **카드 머리·수염 낱말이 정본 그림에 덜 먹음** — `saul-old` 「thin gray hair」인데 8장 모두 숱 많은 장발 · `saul-elder` 「greying」·「close-trimmed」인데 거의 흰머리·풍성한 수염. 사람 답이 「모두 아님」이면 이것부터(같은 시드 한 장 규칙 반복).
4. `apply_canon_faces.py`의 `keep`은 지문(`prompt_sha`)을 안 고쳐 카드가 바뀐 뒤 「그대로 둠」을 골라도 규칙이 계속 걸림 — keep을 「지금 카드에 맞음」으로 받을지 정하기.
