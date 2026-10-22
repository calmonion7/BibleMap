# 장면 1 기브아 창 · 단계 ②③ 문구·가이드·생성·기계 거르기 (task 400)

단계 ①(task 399, `notes/GIBEAH-STEP1.md`)을 통과한 명세로 **기계 거르기 통과 그림 ≥ 1장**(문항 전부 3회 다수결 맞음 · 8시드)이 나올 때까지 「시도 → 실패 문항 원인 → 규칙 추가(검사 함수까지) → 재시도」. 397 메모 중 이 단계 원인: ① 창을 던져야 하는데 찌르는 행동 ② 수금이 그 시대 악기가 아님(류트).

- 생성은 관문(`generate.spec-gate`)을 지나야 한다 — `batch/gibeah_redraw.py gen --try <시도>`가 첫 GPU 호출 전에 `recheck.require_pass`.
- 시도마다 고정 절(아래 `json fixed <시도>`)을 생성 전에 커밋한다. 문항은 397 문항에서 `e.spear` 괄호 부정문을 긍정문으로 쪼개고(사울 빈손 · 창이 허공), 단계 ① 재저작(벽 · 청년 · 약 70세 사울)과 397 그림 결함(웃통 벗음)을 더했다.
- 명령: `$VENV batch/gibeah_redraw.py gen --try a1` → `python3 batch/gibeah_redraw.py judge --try a1` → `report --try a1` → `check --try a1`(→ `ok`).

## 시도 a1

지금 명세 그대로(가이드 없음) — 397과 달라진 것은 명세뿐(사울 빈손 `his empty throwing hand` · 다윗 `standing with his back against the stone wall` · relation 「다윗과 그 뒤 벽 쪽으로」 · `david-youth` · 사울 약 70세). 문구만으로 던짐·벽이 실리는지 먼저 잰다(단계별 원칙 — 실패한 문항에서만 규칙).

```json fixed a1
{
  "scene": "authored-saul-gibeah-spear",
  "seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "size": [1216, 640],
  "reps": 3,
  "guide": null,
  "ref": {"label": "옛 승인 s5 (참고 — 옛 명세)", "image": "~/.local/biblemap-imggen/night-pilot/authored-saul-gibeah-spear/base/s5.png"},
  "bold": ["18:10", "18:11"],
  "style": [
    {"id": "s.style", "q": "화풍", "what": "미색 종이에 연필로 그리고 색연필로 칠한 동화 그림 화풍인가?"},
    {"id": "s.no-blob", "q": "덩어리", "what": "얼굴·옷 없이 평평한 회색 덩어리나 미완성 실루엣으로 남은 사람·물건이 없나?"}
  ],
  "elements": [
    {"id": "e.moment", "q": "순간", "what": "창이 사울의 손을 떠나 방 안 허공을 날아 다윗 쪽으로 가고, 다윗이 몸을 비틀어 그 길에서 비켜 피하는 순간인가?"},
    {"id": "e.spear-air", "q": "허공의 창", "what": "창 하나가 사울의 손을 떠나 두 사람 사이 허공에 떠 있나?"},
    {"id": "e.saul-empty", "q": "사울 빈손", "what": "사울의 두 손이 모두 비어 있나(창이든 다른 무기든 쥐고 있지 않음)?"},
    {"id": "e.saul-throw", "q": "던진 자세", "what": "사울이 던진 팔을 다윗 쪽으로 뻗고 몸을 앞으로 내민, 방금 던진 자세인가(창을 쥐고 찌르는 자세가 아님)?"},
    {"id": "e.saul-age", "q": "사울 나이", "what": "화면 오른쪽 사울이 70세쯤 된 왕으로 보이나(회색 섞인 짧은 수염 · 회색 머리 · 깊은 주름, 그래도 큰 키·넓은 어깨, 관이나 머리쓰개 없음)?"},
    {"id": "e.david-youth", "q": "청년 다윗", "what": "화면 왼쪽 다윗이 15~20세 청년으로 보이나(수염 없음 · 어린아이가 아닌 자란 몸 · 머리에 붙은 짧은 검은 곱슬머리 · 머리쓰개 없음)?"},
    {"id": "e.wall", "q": "벽 앞", "what": "다윗이 돌벽을 등지고 벽 바로 앞에 서 있나?"},
    {"id": "e.lyre", "q": "수금", "what": "다윗이 손에 든 악기가 작은 나무 수금인가(류트·기타·만돌린처럼 지판과 긴 목이 달린 악기가 아니고, 몸통만 한 큰 하프도 아님)?"},
    {"id": "e.tunic", "q": "튜닉", "what": "다윗이 웃통을 벗지 않고 무릎 길이 모직 튜닉을 입고 있나?"},
    {"id": "e.face-each", "q": "마주함", "what": "다윗은 오른쪽 사울 쪽을, 사울은 왼쪽 다윗 쪽을 향해 두 사람이 서로를 향하나?"},
    {"id": "e.room", "q": "방 안", "what": "거친 돌벽으로 된 소박한 방 안(실내)이고, 궁전 장식이나 바깥 풍경이 아닌가?"},
    {"id": "e.guard", "q": "가드", "what": "손가락 수 이상, 두 겹·덧붙은 인물, 종이 테두리·액자, 글자 같은 결함이 하나도 없나?"}
  ],
  "filter_qs": ["s.style", "s.no-blob", "e.moment", "e.spear-air", "e.saul-empty", "e.saul-throw", "e.saul-age", "e.david-youth", "e.wall", "e.lyre", "e.tunic", "e.face-each", "e.room", "e.guard"]
}
```
