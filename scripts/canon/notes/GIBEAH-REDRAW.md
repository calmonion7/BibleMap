# 기브아 창 장면 다시 그리기 — 394 새 명세로 (task 397)

재검(task 392 `recheck.py images`)에서 기브아 창 승인 그림(night-pick 바탕 s5, 2026-10-19)이 규칙 10개 모두 「낡음」 — 승인 기록 `spec_hash` `bf8cfbbb51fe` ≠ 지금 명세 `3f9b6e4842c1`(394에서 장면 구절 전부로 재저작: 18:11 창 던짐·피함, 소년 다윗 `david-boy`, 작은 나무 수금). 지금 명세로 다시 그려 기계로 거른 최종 후보만 사람에게 보이고, 사람이 고르면 새 승인이 옛 승인을 바꾼다. 사람이 「둘 다 아님」이면 옛 승인 그대로(낡음 표시 유지).

## 고정 절 (생성 전에 커밋)

- **얼굴 단계 = 없음(C 장면만)** — task 395 `판정: 미채택`(V3 얼굴 보정 되붙임은 얼굴이 매끈한 붓칠로 바뀌어 장면 화풍과 어긋남). 사울·다윗 모두 생성 그림 그대로.
- **생성** = LoRA·가이드·CN 없는 Z-Image 한 장(393 「C」와 같은 방식) · 문구 `derive_scene.route_prompt`(기브아는 `whole_background`가 있어 `whole_prompt` — 판 단계 S2·S3의 옛 18:10 문구는 안 씀) · 1216×640 · 시드 `params.SPEC_REGEN_SEEDS` 8개 `[11, 42, 7, 23, 5, 101, 202, 303]`. 문구 241낱말·**326토큰 ≤ 512**(잘림 없음 — `check_scenes.zimage_tokens` 실측), `check_whole` 위반 0.
- **기계 거르기** = `claude -p` Sonnet · 머리말 v2 · 문항 묶음 둘(화풍 S · 장면 요소 E) × **3회 다수결**(판정자 재현성 — 시드 8·같은 묶음). 상식 규칙 채택분(`p.boarding`·`p.one-crown`)은 이 장면 낱말에 걸리지 않음(`plausibility.questions(…, adopted_only=True)` = 빈 목록) → 상식 문항 없음. 장면 요소 문항은 명세 칸·장면 구절(삼상 18:10-11)에서 쪼갰다(요소마다 한 문항). 그림 통과 = 아래 `filter_qs` 다수결 모두 「맞음」.
- **사람에게 보일 후보 = 2장** — 거르기 틀림 수 최소 → 전체 틀림 최소 → 시드 순서. 통과가 2장 미만이면 불통과로 채우고 화면에 「기계 불통과」로 표시. 접힌 칸에 8장 전부(기계 불통과 표시 포함) + 옛 승인 s5(참고 — 옛 명세).
- **사람 화면** = 비공개 Artifact 1화면(폰) · 블라인드 좌우 · 「왼쪽 / 오른쪽 / 둘 다 아님」 + 메모 · 확대 보기 1×~4× · 성경 원문 삼상 18:6-11, **18:10-11 굵게**(18:10 = 같은 자리, 18:11 = 고정한 순간). `check_cand_page.py` 통과가 게시 조건.
- **`판정:` 규칙** — 사람이 후보 하나를 고르면 `판정: 장면 채택` → `approved.final` = night-pick 바탕(그 시드 · 레포 사본 `samples/gibeah-redraw/approved-authored-saul-gibeah-spear.png` · `provenance`로 명세 해시·프롬프트 해시·규칙 판 자동 기록). 「둘 다 아님」이면 `판정: 보류` — 옛 승인 그대로, 명세·그림 결함은 기록만(명세 고치기는 이 과제 밖).

```json fixed
{
  "scene": "authored-saul-gibeah-spear",
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "size": [1216, 640],
  "reps": 3,
  "ref": {"label": "옛 승인 s5 (참고 — 옛 명세)", "image": "~/.local/biblemap-imggen/night-pilot/authored-saul-gibeah-spear/base/s5.png"},
  "bold": ["18:10", "18:11"],
  "style": [
    {"id": "s.style", "q": "화풍", "what": "미색 종이에 연필로 그리고 색연필로 칠한 동화 그림 화풍인가?"},
    {"id": "s.no-blob", "q": "덩어리", "what": "얼굴·옷 없이 평평한 회색 덩어리나 미완성 실루엣으로 남은 사람·물건이 없나?"}
  ],
  "elements": [
    {"id": "e.moment", "q": "순간", "what": "창 하나가 사울의 손을 떠나 방 안 허공을 날아 다윗 쪽으로 가고, 다윗이 몸을 비틀어 그 길에서 비켜 피하는 순간인가?"},
    {"id": "e.spear", "q": "창", "what": "창은 하나뿐이고 둘 사이 허공에 떠 있나(사울 손에 아직 쥐어져 있거나, 벽·바닥에 박혀 있거나, 다윗이 쥐고 있지 않음)?"},
    {"id": "e.david-boy", "q": "소년 다윗", "what": "화면 왼쪽 인물이 14세쯤 된 소년인가(수염 없음 · 둥근 볼 · 작은 키 · 가는 어깨 · 머리에 붙은 짧은 검은 곱슬머리 · 머리쓰개 없음)?"},
    {"id": "e.lyre", "q": "수금", "what": "다윗이 작은 나무 수금을 아직 손에 들고 있나(몸통만 한 큰 하프나 다른 악기가 아님)?"},
    {"id": "e.saul", "q": "사울", "what": "화면 오른쪽 인물이 40대 왕인가(짧게 다듬은 검은 수염 · 큰 키 · 넓은 어깨 · 짧은 검은 머리 · 관이나 머리쓰개 없음)?"},
    {"id": "e.saul-throw", "q": "던진 자세", "what": "사울이 던지는 팔을 다윗 쪽으로 뻗고 몸을 앞으로 내민, 방금 창을 던진 자세이고, 사납게 눈을 부릅뜬 얼굴로 다윗을 보나?"},
    {"id": "e.face-each", "q": "마주함", "what": "다윗은 오른쪽 사울 쪽을, 사울은 왼쪽 다윗 쪽을 향해 두 사람이 서로를 향하나?"},
    {"id": "e.room", "q": "방 안", "what": "거친 돌벽으로 된 소박한 방 안(실내)이고, 바닥에 나무 걸상 하나가 있는 정도의 꾸밈인가(궁전 장식·바깥 풍경이 아님)?"},
    {"id": "e.guard", "q": "가드", "what": "손가락 수 이상, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자 같은 결함이 하나도 없나?"}
  ],
  "filter_qs": ["s.style", "s.no-blob", "e.moment", "e.spear", "e.david-boy", "e.lyre", "e.saul", "e.saul-throw", "e.face-each", "e.room", "e.guard"]
}
```

## 명령
- `$VENV batch/gibeah_redraw.py gen` → `python3 batch/gibeah_redraw.py judge` → `report` → `cand` → `/opt/homebrew/bin/python3 check_cand_page.py 397 <page>` → 게시 → 사람 답 `samples/gibeah-redraw/pick-verdict.txt` → `python3 batch/gibeah_redraw.py record samples/gibeah-redraw/pick-verdict.txt` → `check`(→ `ok`)
