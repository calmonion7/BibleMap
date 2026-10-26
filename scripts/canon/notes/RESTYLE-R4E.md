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

## 결과 (2026-10-21)

- 편집 6장 · 장당 약 41초 · 판정 42건(7장 × S·E × 3회) 답 빠짐 0.
- 실행자 눈(머리 크롭 비교): **6장 모두 다윗이 고개를 숙여 아래를 본다.** H1 s1 · H2 s1 · H2 s3은 머리털이 청록빛으로 바뀌고 어깨 경계가 흐리다. H1 s2 · H2 s2가 가장 자연스럽다.
- 기계(다수결): 내려다봄 H1 s2 · H1 s3 맞음(편집 전 채택본 0/3) · 이음새 없음 H1 s2만 맞음(나머지 「초록빛 얼룩」·「어깨 번짐」) · 화풍은 **편집 전 채택본도 3/3 틀림** — 이 장면에선 화풍 문항이 편집을 가르지 못한다(389·r2의 판정자 재현성 경고와 같은 결). 다윗 왕 다수결 맞음 H2 s1 · H2 s2뿐(H1 s2는 1/3 · 편집 전 채택본도 0/3 — r4 판정에선 같은 s11이 틀맞맞(맞음)이었다 — 재현성 경고).

후보: 통과 0/6 (후보 H1 s2, H1 s3)

- 고정 절대로 후보 2장(불통과 — 화풍·다윗 왕 문항)을 사람 1화면에 올린다(접힌 칸 6장 + 편집 전 채택본).
- 후보 화면(비공개 Artifact, 폰): https://claude.ai/artifact/4ACJvSDj4FWwiZS6Vqbbvt — `check_cand_page.py` 통과. 사람 답은 `samples/restyle-r4e/pick-verdict.txt`.

## 사람 판정 (2026-10-21, 대화로 받음 — `samples/restyle-r4e/pick-verdict.txt`)

- 답: 둘 다 아님 · 쉼 뺀 0.2분 · 대화 메모 「잘라붙이기는 품질이 안좋네」

판정: 보류

- 승인본은 r4 s11 그대로. 머리 국소 편집(크롭 되붙임)은 시선은 움직였지만(실행자 눈 6/6 고개 숙임) 머리털 색·어깨 경계·머리 크기 화풍이 바탕과 어긋나 사람이 받지 않았다 — **선 인물의 머리처럼 화면 가운데 큰 부위는 잘라붙이기 대상이 아니다**(371·386의 칼·침·기름처럼 작은 지물·흐름과 다름).
- 다음 수단: 되붙이지 않는 쪽 — 구도 가이드의 다윗 머리 자리를 숙인 꼴로(한 장 생성, 이음새 없음).
