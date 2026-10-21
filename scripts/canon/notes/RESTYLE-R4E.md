# 요단 다윗 시선 국소 편집 r4e — 채택본 r4 s11의 다윗 머리만 (2026-10-21)

r4 `판정: 장면 채택`(s11). 남은 결함 = 다윗이 시므이를 내려다보지 않음(r3·r4 16/16 — PROMPTING 28 「선 사람 시선은 문구로 안 됨」). 사용자 다음 수단 「2」(머리 국소 편집).

## 고정 절 (편집 전에 커밋)

- 조리법 = task 371·386 그대로(`gen_local_edit.edit`): 작은 크롭 → 1024 FLUX.2-klein-4B(mflux q8 · 4스텝) 지시 하나 → 원본 크롭 색 맞춤(`color_match`) → 타원 마스크 안쪽만 되붙임. 새 바탕 생성 없음.
- 바탕 = 채택본 `samples/restyle-r4/approved-authored-david-returns-jerusalem.png`.
- 크롭 (L, T, 변) = (190, 150, 200) — 다윗 머리·어깨·턱에 댄 손과 오른쪽 아래 여백. 마스크 상자(원본 좌표) = (232, 178, 318, 300) — 머리·얼굴·턱 손(눈으로 잡음, 격자 확대 확인).
- 지시 두 갈래(같은 「Keep …」), klein 시드 1·2·3 → **6장**:
  - **H1** 「The king lowers his head and looks down toward the ground at the lower right, his eyes cast downward.」
  - **H2** 「The king tilts his head forward and down, gazing down at the lower right corner.」
- 판정 = 전체 그림에 S 2 + 아래 E 5, 그림마다 3회(claude -p Sonnet · 머리말 v2) 다수결. 편집 전 채택본도 대조로 잰다(고르기에서 뺌).
- **거르기** = `filter_qs` 다수결 모두 맞음. **후보 2장** = 거르기 틀림 최소 → 전체 틀림 최소 → 갈래·시드 순서(모자라면 불통과로 채우고 표시) → 사람 1화면(블라인드 · 원문 · 메모 · 접힌 칸 6장 + 편집 전 채택본).
- `판정:` 규칙 = 하나를 고르면 `판정: 장면 채택`(정본 `approved.final` path local-edit · 바탕 r4 s11 · 편집 차례), 「둘 다 아님」이면 `판정: 보류`(r4 s11 그대로).

```json fixed
{
  "base": "samples/restyle-r4/approved-authored-david-returns-jerusalem.png",
  "crop": [190, 150, 200],
  "box": [232, 178, 318, 300],
  "seeds": [1, 2, 3],
  "arms": {
    "H1": "The king lowers his head and looks down toward the ground at the lower right, his eyes cast downward. Keep his gold circlet, his grey curly hair and beard, his hand, his red robe, the lighting and the same soft pencil and colored-pencil illustration style.",
    "H2": "The king tilts his head forward and down, gazing down at the lower right corner. Keep his gold circlet, his grey curly hair and beard, his hand, his red robe, the lighting and the same soft pencil and colored-pencil illustration style."
  },
  "reps": 3,
  "elements": [
    {"id": "e.look-down", "q": "내려다봄", "what": "다윗이 고개를 숙여 엎드린 사람을 내려다보나(먼 곳이나 앞을 보지 않음)?"},
    {"id": "e.david-king", "q": "다윗", "what": "왼쪽에 선 다윗이 60세쯤 된 왕으로 보이나(희끗한 수염 · 긴 왕의 겉옷 · 머리의 금관)?"},
    {"id": "e.face-each", "q": "마주 봄", "what": "엎드린 사람의 머리가 다윗 쪽(화면 왼쪽)을 향하고, 다윗이 그를 내려다보나(두 사람이 마주함)?"},
    {"id": "e.edit-clean", "q": "이음새", "what": "다윗의 머리·얼굴·손에 이음새·얼룩·두 겹·뒤틀림이 없고 목과 몸에 자연스럽게 이어지나?"},
    {"id": "e.shimei-bow", "q": "시므이", "what": "한 사람이 무릎 꿇고 이마를 땅 가까이 대고 엎드려 비는 모양인가?"}
  ],
  "filter_qs": ["s.style", "s.no-blob", "e.look-down", "e.david-king", "e.edit-clean"]
}
```

## 명령
- `python3 batch/restyle_try.py gen --round r4e` → `judge --round r4e` → `report --round r4e` → `cand --round r4e` → `check --round r4e`(→ `ok`)
