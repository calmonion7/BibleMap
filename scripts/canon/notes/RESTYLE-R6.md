# 요단 엎드린 시므이·배에 탄 가족 r6 — 가이드 꼴 둘 고침 (2026-10-21)

r5 `판정: 보류` — 다윗 시선은 풀렸고(가이드 머리 숙임 · 내려다봄 5/8), 사람 메모 「왼쪽(s202): 시므이가 누웠음 · 오른쪽(s23): 배타는게 이상함」. 둘 다 가이드 꼴 결함으로 본다(PROMPTING 28: 가이드 = 자리·자세): 시므이 `prostrate`는 납작한 타원이라 다리를 뻗고 누운 몸이 됐고, 왕의 가족 `crowd`(선 사람 두 줄)가 배 위에 겹쳐 배 앞 줄서기가 됐다.

## 고정 절 (생성 전에 커밋)

- 정본 고침은 가이드 둘(문구·칸 문장은 r4·r5 그대로, 503토큰): 시므이 꼴 `kneel_bow`(무릎 꿇고 엉덩이가 가장 높고 등이 왼쪽 아래로 기울어 머리가 땅에 · 정강이는 엉덩이 밑) · 칸 [0.33,0.78,0.48,0.97] / 왕의 가족 꼴 `seated`(배 안에 앉은 머리·어깨 한 줄, 아래 끝 = 뱃전 0.636) · 칸 [0.74,0.565,0.95,0.64]. 다윗 `person_bow`는 r5 그대로.
- 가이드 = `samples/restyle-r6/guide.png` sha256 앞 16 `305c69b030b78c09`(두 번 같음) · r5 가이드 파일 그대로.
- 생성 = CN 2602 lite 1.0 · 앞 4스텝 · 8시드. 판정 = r5 문항 + 새 문항 둘(3회 다수결). 거르기 = r5 거르기 + 새 문항 둘. 후보·화면·`판정:` 규칙은 r5와 같다(참고 = 승인본 r4 s11).
  - `e.kneel` 엎드린 사람이 **바닥에 누워 있지 않고** 무릎을 꿇어 엉덩이가 들리고 이마를 땅에 댄 모양인가?
  - `e.boarding` 배 쪽 사람들이 강가에 **줄지어 서 있지 않고** 배 안에 타 있거나 배에 오르고 있나?

```json fixed
{
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "stage1": {"scale": 1.0, "cn_steps": 4},
  "guide": "samples/restyle-r6/guide.png",
  "reps": 3,
  "ref_seeds": [11],
  "ref_image": "samples/restyle-r4/approved-authored-david-returns-jerusalem.png",
  "ref_label": "승인본 r4",
  "extra_elements": [
    {"id": "e.david-king", "q": "다윗", "what": "왼쪽에 선 다윗이 60세쯤 된 왕으로 보이나(희끗한 수염 · 긴 왕의 겉옷 · 머리의 금관)?"},
    {"id": "e.face-each", "q": "마주 봄", "what": "엎드린 사람의 머리가 다윗 쪽(화면 왼쪽)을 향하고, 다윗이 그를 내려다보나(두 사람이 마주함)?"},
    {"id": "e.look-down", "q": "내려다봄", "what": "다윗이 고개를 숙여 엎드린 사람을 내려다보나(먼 곳이나 앞을 보지 않음)?"},
    {"id": "e.one-crown", "q": "금관 하나", "what": "머리에 금관을 쓴 사람이 다윗 한 사람뿐인가?"},
    {"id": "e.gap", "q": "간격", "what": "엎드린 사람이 다윗 발에 붙지 않고 한 걸음쯤 떨어져 있나?"},
    {"id": "e.kneel", "q": "꿇어 엎드림", "what": "엎드린 사람이 바닥에 누워 있지 않고, 무릎을 꿇어 엉덩이가 들리고 이마를 땅에 댄 모양인가?"},
    {"id": "e.boarding", "q": "배에 탐", "what": "배 쪽 사람들이 강가에 줄지어 서 있지 않고, 배 안에 타 있거나 배에 오르고 있나?"}
  ],
  "filter_qs": ["s.style", "s.no-blob", "e.shimei-bow", "e.before-david", "e.david-king", "e.face-each", "e.look-down", "e.one-crown", "e.kneel", "e.boarding"]
}
```

## 명령
- `$VENV batch/restyle_try.py gen --round r6` → `python3 batch/restyle_try.py judge --round r6` → `report --round r6` → `cand --round r6` → `check --round r6`(→ `ok`)

## 결과 (2026-10-21)

- 생성 8장 · 73~78초/장 · 판정 48건 답 빠짐 0.
- 다수결 맞음(8장 중, r5 → r6): 화풍 4 → 7 · **꿇어 엎드림 — → 7** · 엎드림 8 → 7 · 내려다봄 5 → 4 · 마주 봄 6 → 3 · 다윗 왕 8 → 6 · 금관 하나 5 → 7 · 간격 8 → 5 · **배에 탐 — → 2**.

후보: 통과 0/8 (후보 s5, s101)

- 실행자 눈: s5 · s101 모두 배가 물에 떠 이쪽 강가에 닿고 **왕의 가족이 배 안에 앉아 있다**(seated 꼴이 옮겨짐), 시므이는 무릎 꿇고 이마를 땅에 댐(s101 분명), 다윗은 고개 숙여 시므이를 봄. 기계 「배에 탐」 틀림은 배 곁에 선 유다 사람 몇(명세상 배를 붙듦)을 줄서기로 본 것으로 보인다 — 상식 규칙집 v2 「문턱 차이」와 반대 방향(여기선 엄격).
- 고정 절대로 후보 2장(불통과 — s5 배에 탐 · s101 다윗 왕·배에 탐)을 사람 1화면에 올린다.
- 후보 화면(비공개 Artifact, 폰): https://claude.ai/artifact/TgzNJHhJNoMWneBRWG9Bvy — `check_cand_page.py` 통과. 사람 답은 `samples/restyle-r6/pick-verdict.txt`.

## 사람 판정 (2026-10-21, 대화로 받음 — `samples/restyle-r6/pick-verdict.txt`)

- 답: 왼쪽 = **cn s101**(2위) · 쉼 뺀 1.0분(벽시계 8.4분 — 새 확대 보기로 봄) · 메모 「다윗목이 조금 길어보임」

판정: 장면 채택

- 정본 `approved.final` = night-pick 바탕 s101(가이드 `samples/restyle-r6/guide.png` · CN 2602 lite 1.0·앞 4 · round restyle-r6) · 레포 사본 `samples/restyle-r6/approved-authored-david-returns-jerusalem.png` — 승인본 r4 s11을 바꿈(r3·r4 사본은 그대로).
- 남은 결함: 다윗 목이 조금 길다 — 가설: `person_bow` 꼴의 앞으로 기운 목 다각형(어깨에서 머리까지 r의 약 1.3배)이 목을 늘렸다. 다음에 이 꼴을 쓸 때 목을 줄인다(머리 원을 어깨에 더 붙임).
- 상식 규칙집 라벨 후보(`notes/PLAUSIBILITY.md` 「라벨은 계속 모은다」): r6 s101 「목이 김」 → 몸 비례. 고정 절 검증 묶음은 그대로 두고 다음 검증 판에 더한다.
