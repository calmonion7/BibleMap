# FACE-LORA-V4 — 장면 화풍으로 다시 칠한 학습 묶음으로 사울·다윗(청년) LoRA를 다시 학습하면, 새 정본 얼굴이 장면 화풍을 지킨 채 기브아 창에 실리는가 (task 445, 2026-10-27)

393·395에서 LoRA(V2·V3)를 건 장면은 화풍이 16/16 무너졌다(사람 판정). V2 묶음(klein 없음)도 0/8이라 「klein 화풍이 끌려온다」만으로는 설명이 안 된다 — 빈 미색 바탕·클로즈업 위주 구성도 의심. 그래서 이번에는 **묶음 화풍 하나만** 바꿔(모든 묶음 그림을 Z-Image img2img로 장면 화풍에 다시 칠함) 다시 학습하고, 학습 전에 묶음 화풍을 기계로 먼저 잰다. 정본은 오늘(a3bebe7) 카드에서 파생한 새 정본이다.

## 고정 절 (실행 전 — 그림·판정을 보기 전에 적음)

- **대상** = 사울(`saul`) · 다윗 청년(`david-youth`) — 기브아 창(`authored-saul-gibeah-spear`) 등장 인물 그대로. 정본 = `frozen/saul.png`(face-canon-v3 s11) · `frozen/david-youth.png`(s23), 3/4 = 같은 시드 `~/.local/biblemap-imggen/face-canon-v3/<id>/s<시드>-34.png`.
- **트리거 낱말** = `saul_bm` · `davidy_bm`(기브아 문구 502 + 둘 = 511/512, 실측 2026-10-27).
- **묶음(V3 구성 그대로, 새 정본으로)** — `~/.local/biblemap-imggen/lora-sheet-v4/<id>/NN.png+txt`, 캡션 `<트리거>, a man, <구도>`(정체성·화풍 낱말 없음, V3와 같은 구도 문구):
  - 초상 13 = 정면 정본 1 + klein 4B 각도 정본(3/4 · 옆얼굴, 참조 = 정면 정본, 시드 11·42·7, 보는 쪽 = 기브아 facing: 사울 left · 다윗 right — `gen_face_angles.views`와 같은 지시문) 6 + 좌우 반전 6.
  - 전신 8 = klein 4B, 참조 [정면 정본, 같은 시드 3/4 정본], 자세 4(`params.LORA_V3_BODY` 그대로) × 시드 11·42, 768×1152 — `gen_lora_v3.body`와 같은 지시문.
  - 원경 4 = 서기 0.38 · 꿇어앉기 0.30(`LORA_V3_FAR`) × 시드 2 — `gen_lora_v3.far` 그대로(다시 칠하기 **전** 전신으로 만든 뒤 함께 다시 칠함).
  - Claude 눈 거르기(원래 화소 확대 — 가분수·다른 사람·두 사람): 다시 칠하기 전 klein 산출에서. 거른 장은 빼고 기록한다(다시 그리지 않음). 남은 묶음이 20장 아래면 벽.
- **다시 칠하기(바꾸는 한 변수)** = 묶음 모든 그림(정면 정본 포함)을 Z-Image-Turbo Q8 img2img, 세기 `LORA_V4_RESTYLE`(0.5), 9스텝, 크기 그대로, 시드 = 그림 번호. 문구 = `derive_scene.ST`(장면 공용 화풍 머리) + 캡션의 구도 문구 + 기브아 명세의 그 인물 cast 서술(`cast_describe(_cast_in_scene)` — 장면 문구가 그 인물을 부르는 말과 같게). LoRA 없음.
- **학습** = V3 설정 그대로(`train/<saul|david>-v3.json` 복사 — z-image-turbo · quantize 8 · rank 16 · AdamW 1e-4), 바꾸는 것은 `data`·`output_path`·300스텝이 되는 에폭 수. 사울 → 다윗 청년 차례로 한 백그라운드 프로세스(피크 약 31GB, 다른 생성과 겹침 금지). → `~/.local/biblemap-imggen/lora/{saul,david-youth}-v4.safetensors`(300스텝 어댑터).
- **장면 비교** = 393과 같은 경로: 지금 명세 `derive_scene.route_prompt` 한 장(1216×640, 9스텝, 시드 `[11, 42, 7, 23, 5, 101, 202, 303]`). **C** = LoRA 없음(트리거 없음) · **L** = 두 v4 어댑터 동시, 세기 `LORA_V4_SCALE`(1.0), 두 인물 cast 서술 앞에 트리거 낱말만. 생성 직전 실제 문구 토큰 수(Z-Image 채팅 틀 포함)를 장마다 `samples/face-lora-v4/metrics.json`에 — > 512면 생성하지 않고 멈춤(벽). L은 `get_active_adapters()` = 두 어댑터 기록. m17e 편집 사슬 없음.
- **화풍 판정자** = `batch/style_judge.py`의 문항 s.style(JORDAN-GUIDE 고정 절 원문 「미색 종이에 연필로 그리고 색연필로 칠한 동화 그림 화풍인가?」) 하나 · 머리말 v2 · claude -p Sonnet · 그림마다 3회 따로 · 다수결(3회 중 2 「틀림」이면 틀림).
  - **S2 맞춰 보기(GPU 0)**: 묶음 A = 393 `lora-v3-scene/{C,V2,V3}-s*.png` 24장 전체 그림(사람: C 맞음 8 · V2·V3 틀림 16) · 묶음 B = 395 `face-detail-v3/paste/C-s*.png` 8장의 두 머리 둘레(머리 상자 긴 변 × 2.4 정사각, `gen_face_detail.region`)를 원래 화소에서 잘라 3배 LANCZOS 확대한 16장(사람: 틀림 — 「화풍이 틀린것 같은데」). 기준: A 다수결이 사람 답과 ≥ 20/24 일치 **그리고** B 다수결 「틀림」 ≥ 12/16 → `판정자: 관문으로 씀`, 아니면 `판정자: 관문 아님`(기계 관문 없이 사람 화면 맨 앞 화풍 문항에 맡김 — 벽 아님).
  - 측정만(결론 안 바꿈): V3 묶음(`lora-sheet-v3`) 50장도 같은 판정자로 — 「V3 묶음이 이미 화풍 맞음이었나」(관문이 원인을 재는지).
- **묶음 화풍 관문**(판정자가 관문일 때): 인물마다 묶음 그림 다수결 「맞음」 ≥ 80%. 미달 인물은 세기 `LORA_V4_RESTYLE_RETRY`(0.65)로 그 인물 묶음 전부 한 번 다시 칠해 다시 잼. 그래도 미달이면 벽 → `판정: 미채택` + 다음 후보.
- **장면 화풍 관문**(판정자가 관문일 때): 그림마다 전체 그림 1 + 두 머리 둘레(OWLv2 머리 상자, 원래 화소 3배) 2를 판정. 갈래마다 「전체 맞음」 장 수와 「두 머리 모두 맞음」 장 수. 통과 = C 둘 다 ≥ 6/8 **그리고** L 둘 다 ≥ 6/8. L 미달이면 세기 `LORA_V4_SCALE_RETRY`(0.7)로 L 8장만 한 번 다시(재학습 없음). 그래도 L 미달이면 벽 → `판정: 미채택`. C가 미달이면 판정자·장면 문제로 적고 벽(L 수리로 못 고침).
- **사람 판정 화면 하나**(폰 비공개 Artifact, 한 화면 한 질문, 화면마다 삼상 18:6-11 개역한글 원문 · 18:10 굵게):
  - 맨 앞 **화풍 2문항**(인물마다 1): 시드 11(못 찾으면 두 머리 다 찾은 첫 시드)의 C와 L 머리 둘레를 원래 화소 3배로 나란히 — 「L이 C와 같은 화풍인가」. 안내 「아니오면 나머지는 안 풀어도 됨」.
  - **얼굴 A 32문항**: 「정본과 같은 사람인가」 — L 머리 16 + 대조군 C 머리 16을 갈래 이름 없이 섞음. 393 v2 규칙(`human.face-matched-quality`) 그대로: 머리마다 판정 화면용 얼굴 보정(그 갈래 방식 — L은 그 인물 v4 어댑터 하나 세기 1.0, C는 LoRA 없음; `FACE_DETAIL_*` 그대로, 완성 그림에는 안 붙임), 정본 정면·3/4를 보정 머리의 실측 선명도(라플라시안)에 맞춰 줄였다 키움, 정본 두 장과 머리를 같은 칸 크기로.
  - 답 「판정 face-lora-v4」 → `python3 gen_lora_v4.py record '<답>'` → `samples/face-lora-v4/verdict.txt`.
- **채택 규칙**: **채택** = 화풍 2문항 모두 「같음」 **그리고** 얼굴 A L이 인물마다 ≥ 5/8. **조건부** = 화풍 2문항 모두 「같음」이고 한 인물만 A 충족. **미채택** = 그 밖(화풍 하나라도 「다름」이면 얼굴과 무관하게 미채택). 대조군 C가 인물마다 ≥ 3/8이면 「판정이 너그러움」을 결론 옆에 적음.
- 하지 않음: 다른 인물 · rules.json 승급 · 기브아 승인 그림·명세 수정 · 얼굴 되붙임·큰 부위 잘라붙이기 · 옛 V3 LoRA 얼굴 비교. 이번 수단이 막히면 다음 후보는 참조 어댑터(PuLID·InfiniteYou)·다중 참조 편집(한 줄만).
- 그림은 레포 밖(`~/.local/biblemap-imggen/`), 목록·판정은 `samples/face-lora-v4/`.

```json fixed
{
  "reps": 3,
  "cal_a_min": 20,
  "cal_b_wrong_min": 12,
  "sheet_pass_ratio": 0.8,
  "sheet_min": 20,
  "scene_pass_min": 6,
  "adopt_face_min": 5,
  "lenient_control_min": 3,
  "crop_zoom": 3
}
```

## 명령 (레포 `scripts/canon/`)
- `python3 gen_lora_v4.py cal` → `cal-report` (S2, GPU 0)
- `python3 gen_lora_v4.py views` · `body` (klein) → `raw` → `$VENV gen_lora_v4.py restyle` → `python3 gen_lora_v4.py sheet-judge` (S3)
- `python3 gen_lora_v4.py train` (S4)
- `$VENV gen_lora_v4.py scene` → `$VENV gen_lora_v4.py heads` → `python3 gen_lora_v4.py scene-judge` (S5)
- `$VENV gen_lora_v4.py detail` → `python3 gen_lora_v4.py page` → 게시 → `record` (S6)

## 결과
