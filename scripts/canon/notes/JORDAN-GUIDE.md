# JORDAN-GUIDE — 요단 귀환 구도 가이드: 명세에 지리(동편·서편)·새 구도 → 깊이 가이드 + CN 2602 lite → 격자 → 8시드 → 사람 1화면 (task 388)

## 고정 절 (2026-10-21 — 생성·예측 전에 적음)

387 사람 답 「둘 다 아님」, 메모 「다윗, 시므이 무리 (15+20) 포커스 하고 베냐민 사람 1천명은 조금멀리 원근감으로 구도잡기」 · 「배는 강어귀에 다다르고 가족들이 배에 오르려는 장면이 아닌가?」 · 「나룻배가 건너가니는 반대편 강가에서 다윗 가족을 태우러 건너온다는 얘기」.
배치(「다윗 바로 앞」)는 문구 0/8 · 국소 편집 0/12였다(PROMPTING 25) → 이번 수단은 **[[구도 가이드]] 하나**(문구·편집 갈래 없음).

### ① 명세 고침 (정본 `scenes/authored-david-returns-jerusalem.json`)
- 상황 칸에 **지리**: 왕과 일행·시므이·시바 일행·베냐민 일천·바르실래는 요단 **동편**(17:22·24 마하나임), 유다 족속은 **서편** 길갈(19:15 · 19:40 「왕이 길갈로 건너오고」). 나룻배는 건너가고(19:18) — 서편에서 와 왕 쪽 강가에 닿아 가족이 오름(본문 밖 · 387 사람 메모).
- 새 구역 `ziba`(시바 일행 35명, S2d) · `boat`(닿은 배) · `gilgal`(강 건너 서편 둑의 유다 족속, S2e — 1층 판정 표기 「길갈로 오니라」를 빼지 않고 실음). 새 칸 `guide` = `{depth, shape, why}` — 가이드 그림은 `regions`·`guide`에서만 파생.
- 1층 판정: `.forge/reports/scripture-words-review.md` 「task 388」 — 1차 맞음 7·표기 5·차단 0 → 재판정 맞음 12·표기 1·차단 0 → 표기 고친 뒤 최종 차단 0. 파생 357토큰(≤ 512).

### ② 구도 가이드
- `batch/make_guide.py` → `samples/jordan-guide/guide.png`(1216×640, 결정적 — 같은 명세 → 같은 sha256). 깊이 그림: 가까움 밝게(1) · 멂 어둡게, 하늘 0 · 땅 지평선 0.26에서 아래로 0.12→0.5. 꼴 person · prostrate(머리 왼쪽 = 다윗 쪽) · crowd(작은 실루엣 두 줄) · boat · bank, 가우스 흐림 3px. 선은 주지 않는다(ZIMAGE §2 「콘티 되그림」).
- 앞 초점: 다윗(1.0) · 다윗 발 앞 시므이(1.0) · 곁 바르실래(0.95). 가까운 중경: 시바 일행(0.72). 강가: 유다 몇(0.58) · 오르는 가족(0.55) · 닿은 배(0.52). 멀리: 베냐민 일천(0.22). 강 너머: 서편 둑 유다 족속(0.1) · 둑(0.08).

### ③ 생성 경로
- 바탕 경로 그대로(인코딩/생성 분리 · Q8 GGUF 우회 2줄 · 1216×640 · 9스텝 · guidance 0), 생성 쪽만 `ZImageControlNetPipeline` + **CN 2602 lite**(`control_layers_places [0,10,20]` · `control_refiner_layers_places [0,1]` · `control_noise_refiner` · `control_in_dim 33`, 가중치 strict 로드) — `run_scene.py --worker gencn`.
- **CN 스텝**: 파이프라인에 `control_guidance_end`가 없어 ControlNet 호출을 세어 앞 k번 뒤엔 출력 없음(None — 트랜스포머가 CN 없이 돈다).
- 문구 = 387과 같은 `render`(나룻배 L2 · 요단 L1 사전 삽입꼴) — 정본만 바뀌었다. 묶음 `jordan-guide`(`plain_words.py --set jordan-guide`, run_night 표 등록).
- 생성 프로세스 한 번에 하나(pgrep), 긴 배치는 `nohup caffeinate -i`.

### ④ 시험 1장 → 격자(무인 관문) → 본 실행
- 시험 1장: 강도 0.8 · CN 전 9스텝 · 시드 11 — 경로·장당 시간·피크 메모리(`torch.mps.driver_allocated_memory` 최대)를 잰다. 피크가 가용(약 17GiB)을 넘으면 노트에 적고 멈춘다.
- **격자** = 강도 {0.65, 0.8, 1.0} × CN 스텝 {전 9, 앞 4} × 시드 {11, 42} = 12장, 장마다 J1·J1-prop·E·W·S 판정.
- **통과 설정** = 그 설정의 두 시드 모두 S 두 문항(화풍 · 가이드 복제 없음)이 「맞음」.
- **고르기** = 통과 설정 중 배치 문항 셋(`e.before-david` · `e.ziba-front` · `e.benjamin-far`) 두 시드 맞힘 합 최대. 같으면 낮은 강도 → 적은 스텝.
- 통과 설정이 **없으면** 본 실행·사람 화면 없이 `판정: 보류`, 이 노트에 격자 표와 다음 수단(사람 결정)을 적는다.
- **본 실행** = 고른 설정 × 8시드(11·42·7·23·5·101·202·303), 그림마다 J1·J1-prop·O1·E·W·S.

### ⑤ 기계 판정 (claude -p Sonnet, 387과 같은 머리말)
- **J1**(v2) — 정본 명세 문항(순간 · 배경 · 무리 다섯 · 다윗 자세·지물·방향 · 가드), 지물 칸은 **J1-prop**(p2, 크롭 2.5배) 답.
- **E**(v2, 전체) — 장면 요소 7문항(아래 `elements`). 무리는 화면 기준 말로 묻는다(누가 시바·베냐민인지 판정자가 못 가림).
- **W**(v2) — 사전 특징: 나룻배(L2) · 요단(L1).
- **S**(v2, 전체) — 화풍 · 가이드 복제(아래 `style`).
- **O1** — 이상한 점, 기록만(본 실행만).

### ⑥ 1위·2위
- **틀림 칸** = J1(지물 칸은 J1-prop) + E + W + S의 「틀림」 수 — 이번엔 「다윗 바로 앞」을 **넣는다**(목표가 배치).
- 1위 = 틀림 칸 최소, 같으면 시드 순서. 2위 = 나머지에 같은 규칙.

### ⑦ 사람 화면 1화면 (폰 360px 비공개 Artifact)
- 좌우 블라인드(장면 id 해시) = **1위 / 2위**. 질문 하나 「장면 구절에 맞게 그린 쪽은?」(왼쪽 / 오른쪽 / 둘 다 아님).
- 성경 원문 상자(장면 구절 8절 전부, 19:18 굵게, 스크롤) · 여러 줄 메모칸 · 쉼 뺀 타이머.
- 접힌 칸: 가이드 그림 · 본 실행 8장 · 격자 12장 · 387 문구 1위 s101(참고 표시) — 기계 불통과 포함.
- 사람 답(「판정 문장」) = `samples/jordan-guide/pick-388-verdict.txt`(루프 검사 꼴 `*388*verdict*`). 대화로 오면 원문을 그 파일 메모에 두고 `source: conversation`.

### `판정:` 규칙
- 사람이 후보 하나(왼쪽/오른쪽)를 고르면 `판정: 장면 채택` → 정본 `approved.final`(night-pick 바탕 꼴 + 가이드·강도·CN 스텝) + 레포 사본 `samples/jordan-guide/approved-authored-david-returns-jerusalem.png`.
- 「둘 다 아님」이면 `판정: 보류`, 격자 통과 없음도 `판정: 보류` — 이 노트에 다음 수단(같은 문구·같은 가이드 A/B는 다시 묻지 않는다).

### 측정만 (규칙 아님)
- 「다윗 바로 앞」·바르실래·무리 맞힘(387 대비 각 0/8) · 시바 초점 · 베냐민 멀리 · 배 닿음·가족 오름 · 화풍·복제 · 장당 시간 · 피크 메모리 · O1 · 쉼 뺀 사람 시간.

### 명령
- `VENV=~/.local/biblemap-imggen/.venv314/bin/python` · `$VENV batch/plain_words.py <cmd> --set jordan-guide`
  - `one`(시험 1장) · `grid`(격자 12장 + 판정 + 고르기, 무인) · `scene`(본 실행 8장 + 판정) · `check`(→ `ok`) · `cand`(후보 화면) · `record <판정.txt>` · `verdict` · `approve` · `report`
- 가이드 재현: `python3 batch/make_guide.py --out <임시>/g.png` → sha256 = `samples/jordan-guide/guide.png`
- 후보 화면 검사: `/opt/homebrew/bin/python3 check_cand_page.py 388 ~/.local/biblemap-imggen/pages/jordan-guide-cand.html`

```json fixed
{
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "threshold": 6,
  "token_max": 512,
  "revert_plus": 4,
  "levels": ["L1", "L2", "L3"],
  "forbidden": ["pretend", "feign", "feigning", "sacred", "holy", "ceremonial", "symbolic", "ritual", "divine"],
  "no_ladder": true,
  "one": {"scale": 0.8, "cn_steps": 9, "seed": 11},
  "grid": {"scales": [0.65, 0.8, 1.0], "cn_steps": [9, 4], "seeds": [11, 42]},
  "scenes": {
    "authored-david-returns-jerusalem": {
      "wide": false,
      "word_qids": ["background[0]"],
      "units": [
        {"id": "ferry-boat", "role": "bg", "start": "L2", "judge": "scene",
         "slot": {"path": "stages[1].prompt", "old": "a small flat boat that carries people across a river"}},
        {"id": "jordan", "role": "bg", "judge": "scene",
         "slot": {"path": "stages[0].prompt", "old": "the Jordan river"}}
      ],
      "elements": [
        {"id": "e.shimei-bow", "q": "시므이", "what": "한 사람이 무릎 꿇고 이마를 땅 가까이 대고 엎드려 비는 모양인가?"},
        {"id": "e.before-david", "q": "시므이 자리", "what": "엎드린 사람이 다윗(왼쪽에 서서 오른쪽을 보는 왕) 바로 앞, 발 앞 가까이에 있나?"},
        {"id": "e.old-man", "q": "바르실래", "what": "아주 늙은 노인(흰 수염·늙은 몸)이 다윗 곁에 서 있나?"},
        {"id": "e.no-sword", "q": "다윗 손", "what": "다윗 손에 칼이 없나(빈손인가)?"},
        {"id": "e.ziba-front", "q": "앞쪽 무리", "what": "엎드린 사람 바로 뒤, 화면 앞쪽 가까이에 사람 한 무리(수십 명)가 크게 보이게 서 있나?"},
        {"id": "e.benjamin-far", "q": "먼 무리", "what": "그림 먼 뒤쪽에 아주 작게 보이는 큰 무리(많은 사람)가 있나?"},
        {"id": "e.boat-landed", "q": "배", "what": "배가 이쪽 강가(가까운 둑)에 닿아 있고 사람들이 그 배에 오르고 있나?"}
      ],
      "style": [
        {"id": "s.style", "q": "화풍", "what": "미색 종이에 연필로 그리고 색연필로 칠한 동화 그림 화풍인가?"},
        {"id": "s.no-blob", "q": "가이드 복제", "what": "얼굴·옷 없이 평평한 회색 덩어리나 미완성 실루엣으로 남은 사람·물건이 없나?"}
      ],
      "placement": ["e.before-david", "e.ziba-front", "e.benjamin-far"]
    }
  }
}
```
