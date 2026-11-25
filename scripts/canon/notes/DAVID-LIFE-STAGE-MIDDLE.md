# 장면 덮어쓰기 정체성 잠금 · 다윗 중년 생애 단계 — task 452

후속 fu-75c03afec241(task 446 전수 조사)에서 시작했다. ADR `261030-011200` 이후 장면 인물의 정체성을 나르는 수단은 카드 문구(어휘 정본)뿐이다.
그런데 장면 `cast_override.card`가 그 문구를 장면마다 바꾸고 있었다. 이 작업은 그것을 규칙으로 막고, 걸리던 곳을 카드 쪽으로 푼다.

## 규칙 `spec.cast-identity-fixed`

- 명세 인물마다 `cast_override.card`의 `ageBand`·`beardVolume`·`silhouette`이 카드와 class·text 모두 같아야 한다(`recheck.cast_identity_fixed_errors`).
- 머리 윤곽(`headOutline`)·옷 색(`costumeColor`)은 차림이라 덮어써도 된다(용어집 「카드 층 / 얼굴 층」). 예: 두 여인 솔로몬 면류관, 귀환 다윗 면류관.
- 글만 바꿔도 걸린다. 모델이 보는 것은 글이라, class가 같아도 「late 30s → about 30」이면 정체성이 흔들린다(그릴링 Q1).

## 작업 전 걸리던 곳(4인물·3장면)

| 장면 | 인물 | 바뀐 값 | 푼 방법 |
|---|---|---|---|
| 헤브론 | david-prime | 나이 글 late 30s → about 30 | 카드 나이 글을 「in his 30s, a firm face with faint lines at the eyes」로 넓혀 30·37·38·약 40을 한 글로 덮음, 덮어쓰기 삭제 |
| 솔로몬 출생 | david-prime | 나이 class prime → middle(about 50) | 새 생애 단계 id `david-middle` — 덮어쓰기 값을 카드로 올림 |
| 다윗 귀환 | david-elder | 나이·수염 글, 체격 class average → lean | 세 키를 카드 값으로 · 면류관·겉옷 글은 남김 |
| 다윗 귀환 | shimei | 나이·수염·체격 글 줄임(512토큰) | 세 키를 카드 값으로 · 머리 윤곽 줄인 글은 남김 |

## david-middle 카드

- 나이: 덮어쓰기에 있던 값과 근거([추론] 삼하 5:4·5:5·12:24 + 프로젝트 연대 약 50세)를 그대로 카드로 올렸다.
- 체격: `average` → `broad`(「broad settled shoulders, a thickening waist」) [저작]. david-prime과 같은 값으로 두면 동석 아닌 히람과 카드 층이 한 칸(옷 색)만 달라 `check_cast_v2` (h)에 걸렸다.
  수염을 `full`로 올리는 안을 먼저 시도했으나, 그러면 같은 장면의 나단(middle·full·average)과 한 칸 차이가 되어 (d)에 걸렸다.
- 얼굴 층은 david-prime과 같다(같은 사람).

## 다윗 귀환 512토큰

카드 값으로 되돌리니 525토큰이었다(그릴링 때 잰 527은 머리 윤곽까지 되돌린 값). 정체성 아닌 꾸밈말만 뺐다(PROMPTING 19 빼기만):

- 배경 「with low distant hills」(4)
- 배경 「far back along the same near bank, small in the distance,」 → 「far back on the near bank, small,」
- 배경 「a close group」 → 「a group」
- 관계 「who lies bowed toward him a short step away」 → 「bowed a short step away」(4)

결과는 **512/512로 여유가 0**이다. 이 장면에 낱말 하나만 더해도 넘친다.
사람 메모에서 온 문구(「다윗이 바라봐야지 아래로」의 시선, 「상호작용이 없네」의 「chin lowered toward Shimei」)와 구절 요소 문구는 건드리지 않았다.
구절 요소 0번의 en은 덮어쓰기 글 「in his early 60s」에서 카드 글 「around 60」으로 맞췄다.

## 정본 얼굴

- 판정기 `judge_face_canon.py`의 같은 사람 기준이 사울로 고정돼 있었다. 그대로 다윗에게 돌리면 「사울과 가장 다른 장」을 고른다.
  기준을 `params.FACE_ID_SAME_PERSON` 묶음 첫 id로 일반화했고, 다윗 묶음에 david-prime·david-middle을 넣었다(기준 = `frozen/david.png`, 20대 도망자 정본).
- 생성: `gen_face_canon.py --who david-prime david-middle --out ~/.local/biblemap-imggen/face-canon-v5`(8시드 × 정면·3/4).
- 판정기 결과(같은 사람 기준 = 다윗 20대 정본): david-prime 고름 s23 · david-middle 고름 s23. 기계 이유 글은 참고만 한다(446에서 사람 답과 2/2 갈림).

### david-middle 나이 글 고치기(같은 시드 한 장 반복 1회)

- 원래 글 「about 50, fuller face with lines at the eyes and brow」로 그린 8장은 **8/8이 30대**였다. david-prime 후보와 나이가 구분되지 않았고, 기계 판정도 대부분 「50세치고 젊다」고 적었다.
  이 묶음은 `face-canon-v5/david-middle-v1/`에 보관했다(판정 `judge-david-middle-v1.json`).
- 시드 23 정면 한 장으로 글만 바꿔 다시 그렸다. 새 글은 「about 50, a weathered face with deep lines at the eyes and across the brow, gray at the temples」([저작])이다.
  관자놀이·수염이 희끗하고 눈가·이마에 주름이 생겨 40대 후반~50으로 읽혔고, 같은 사람이라는 인상도 유지됐다.
- 새 글로 8시드를 다시 그렸다. 8장 모두 희끗하다. s42·s101·s202는 흰머리가 많아 50대 후반 쪽, s11·s23·s7이 50 전후로 보인다(Claude 눈).
  기계 판정은 「흰머리가 약하다」와 「어두운 머리 어휘에서 벗어난다」를 함께 적어 엇갈린다(v1 `hair` 「dark curly hair」 낱말 탓으로 보임 — 추론).

## 사람 판정 화면

**https://claude.ai/artifact/JauNEv6hHe9N9ewuq7KvLm** (비공개 · 폰용 · 1.23MB)

```sh
python3 batch/make_canon_face_page.py <out.html> --dir ~/.local/biblemap-imggen/face-canon-v5 --who david-prime david-middle \
  --task "david-life-stage task 452" --title "다윗 생애 단계 정본" --verse "david-prime=삼하 5:5" "david-middle=삼하 12:24" \
  --note "david-prime=…" "david-middle=…"
```

- 한 화면 한 사람(1/2 · 2/2). 같은 사람 기준 = 지금 `david` 정본(20대). david-prime 화면에는 지금 정본(옛 글 late 30s, 「그대로 둠」)도 있다.
- `make_canon_face_page.py`에 `--note`(Claude 원래 화소 눈 확인 한 줄)를 더했다 — 446 회고 「눈 확인을 화면에 같이」.
- 폰(390×844) Playwright: 페이지 오류 0 · 가로 넘침 없음(scrollWidth 390) · 두 화면 구절 원문 자료 확인(측정).

## 사람 답 (2026-10-30)

`{"david-prime":"s23","david-middle":"s23"}` — 둘 다 기계 고름(s23)과 같다. 옛 david-prime 정본(10-27 s42, 옛 글 late 30s)은 `frozen/retired-v1/david-prime.png`.

반영 뒤 재검:
- `spec.cast-canon-face` 6장면 모두 통과(반영 전 5장면 걸림)
- 전 규칙 통과 명세 5/38(작업 전과 같음) · 새 규칙 `spec.cast-identity-fixed` 38/38 통과
- 승인 그림 잰 규칙 모두 통과 3/15 → 2/15. 줄어든 1장은 솔로몬 출생 승인본(10-26)이다. 명세의 인물 id가 david-middle로 바뀌어 「그림 뒤 명세가 바뀜」이 됐을 뿐, 그림 판정이 나빠진 것은 아니다. 다시 그릴 때 새 정본을 쓴다(이번 범위 밖).
- 테스트 343 OK.
