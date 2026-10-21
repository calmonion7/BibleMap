# 화풍 판정자 점검 (task 389, GPU 0)

388 격자(`notes/JORDAN-GUIDE.md`)에서 s11은 여섯 설정 모두 화풍 「틀림」이었고, 그래서 통과 설정이 없어 `판정: 보류`였다.
판정자 이유는 「매끈한 디지털 채색, 연필·색연필 결 없음」. 실행자 눈으로는 1.0·4 s11에도 풀에 연필 빗금 결이 보였고, 「맞음」이라 한 s42가 오히려 평평했다.
그래서 「CN이 화풍을 눌렀다」와 「판정자·시드가 그렇게 본다」를 가른다.

## 고정 절 (판정 전에 커밋)

- 문항: 388 고정 절 `style` 두 문항(s.style 화풍 · s.no-blob 가이드 복제) 그대로 — `style_judge.py`가 JORDAN-GUIDE.md에서 읽는다. 머리말 v2 · claude -p Sonnet · 전체 그림만.
- 묶음(30장):
  - **A** 387 r1 8장 — CN 없음, 같은 요단 장면·같은 시드. 핵심 대조.
  - **B** 사람 승인 최종 10장 — 정본 `approved.final`에 그림이 있는 night-pick·local-edit 장면. 사람이 앱 최종으로 고른 그림이라 화풍 「맞음」 정답으로 본다(양성 대조, 가정).
  - **C** 388 격자 12장 — 같은 문항 반복 안정성.
- 장마다 **3회** 따로 묻는다(세션 없음). 장의 화풍 = s.style 다수결(3회 중 2).
- 일치율 = 3회 s.style 답이 모두 같은 장 / 30장.
- **결론 규칙**(위에서부터 처음 맞는 것):
  1. B 다수결 「틀림」 ≥ 3장 **또는** 일치율 < 0.8 → `점검: 판정자 불안정`
  2. A s11 다수결 「틀림」 → `점검: CN 무관`
  3. 그 밖 → `점검: CN 탓`
- 측정만(규칙 아님): 묶음별 다수결 맞음 수 · 다수결로 다시 센 388 격자 통과 설정 — **388 `판정: 보류`는 바꾸지 않는다**(판정 규칙 사후 변경 금지).
- 갈래별 다음 수단(모두 사람 결정):
  - 판정자 불안정 → 화풍 관문을 이 판정자로 두지 않는다. 사람 승인 그림을 정답으로 판정자를 교정(문구·여러 번 다수결·기계 지표)하거나, 388 s42 화풍 맞음 설정을 사람이 직접 본다.
  - CN 무관 → s11 장면 자체가 판정자 눈에 연필 화풍이 아니다. CN 관문 탓이 아니니 시드를 바꾼 격자(또는 s11 뺀 관문)를 사람이 정한다.
  - CN 탓 → 388 다음 수단 2(배치는 가이드로 움직였으니 화풍을 지키는 CN 강도·스텝 아래쪽 탐색).

```json fixed
{
  "reps": 3,
  "A_seeds": [11, 42, 7, 23, 5, 101, 202, 303],
  "B_scenes": ["authored-david-gath-achish", "authored-david-gibeah-harp", "authored-samuel-bethlehem-david-anointing",
               "authored-samuel-ramah-death", "authored-saul-gibeah-spear", "authored-saul-gilgal-amalek", "authored-saul-jabesh-rescue",
               "authored-saul-michmash-battle", "authored-saul-mizpah-chosen", "authored-saul-nob-massacre"],
  "C_grid": ["g-0.65-9", "g-0.65-4", "g-0.8-9", "g-0.8-4", "g-1.0-9", "g-1.0-4"],
  "unstable_b_wrong": 3,
  "unstable_agree": 0.8
}
```

## 명령
- `python3 batch/style_judge.py judge` → `report` → `check`(→ `ok`)
