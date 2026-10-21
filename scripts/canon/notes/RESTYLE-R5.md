# 요단 숙인 다윗 r5 — 가이드 머리 자리로 시선 주기 (2026-10-21)

r4e `판정: 보류`(사람 「잘라붙이기는 품질이 안좋네」). 다윗 시선은 문구(r3·r4 내려다봄 0/16)로도, 머리 잘라붙이기(r4e)로도 안 됐다 → 남은 수단 = 되붙이지 않는 한 장 생성에서 **가이드의 머리 자리**(PROMPTING 28 고침). 사용자 「진행」.

## 고정 절 (생성 전에 커밋)

- 정본 고침은 `guide.shape.david` = `person_bow` 하나(머리 원을 어깨선 앞(화면 오른쪽 — 시므이 쪽)·아래로, 목이 앞으로 기욺). 문구·칸·regions는 r4 그대로(503토큰).
- 가이드 = `samples/restyle-r5/guide.png` sha256 앞 16 `f48628b1007a06d5`(두 번 같음) · r4 가이드 `5a920685ca5998bb` 파일 그대로.
- 생성 = CN 2602 lite 1.0 · 앞 4스텝 · 8시드. 판정·거르기·후보·화면은 r4와 같다(문항 같음 · 3회 다수결). 접힌 칸 참고 = 승인본 r4 s11.
- `판정:` 규칙 = 하나를 고르면 `판정: 장면 채택`(승인본을 그 그림으로), 「둘 다 아님」이면 `판정: 보류`(r4 s11 그대로).
- 측정 = 내려다봄(r4 0/8)·마주 봄(r4 0/8). 둘 다 그대로면 가이드 머리 자리도 고개를 못 숙인다고 PROMPTING 28에 적는다.

```json fixed
{
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "stage1": {"scale": 1.0, "cn_steps": 4},
  "guide": "samples/restyle-r5/guide.png",
  "reps": 3,
  "ref_seeds": [11],
  "ref_image": "samples/restyle-r4/approved-authored-david-returns-jerusalem.png",
  "ref_label": "승인본 r4",
  "extra_elements": [
    {"id": "e.david-king", "q": "다윗", "what": "왼쪽에 선 다윗이 60세쯤 된 왕으로 보이나(희끗한 수염 · 긴 왕의 겉옷 · 머리의 금관)?"},
    {"id": "e.face-each", "q": "마주 봄", "what": "엎드린 사람의 머리가 다윗 쪽(화면 왼쪽)을 향하고, 다윗이 그를 내려다보나(두 사람이 마주함)?"},
    {"id": "e.look-down", "q": "내려다봄", "what": "다윗이 고개를 숙여 엎드린 사람을 내려다보나(먼 곳이나 앞을 보지 않음)?"},
    {"id": "e.one-crown", "q": "금관 하나", "what": "머리에 금관을 쓴 사람이 다윗 한 사람뿐인가?"},
    {"id": "e.gap", "q": "간격", "what": "엎드린 사람이 다윗 발에 붙지 않고 한 걸음쯤 떨어져 있나?"}
  ],
  "filter_qs": ["s.style", "s.no-blob", "e.shimei-bow", "e.before-david", "e.david-king", "e.face-each", "e.look-down", "e.one-crown"]
}
```

## 명령
- `$VENV batch/restyle_try.py gen --round r5` → `python3 batch/restyle_try.py judge --round r5` → `report --round r5` → `cand --round r5` → `check --round r5`(→ `ok`)
