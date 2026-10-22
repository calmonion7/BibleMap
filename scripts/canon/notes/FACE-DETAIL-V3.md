# 장면은 C, 얼굴 보정에만 V3 LoRA — 되붙인 한 장 (task 395)

393 판정 v2의 두 결과 — C 장면 화풍 8/8, V3 얼굴(문항 A) 사울 6/8·다윗 8/8 — 를 한 그림에 모을 수 있는지 잰다. 방법 시험이라 재료는 393의 옛 명세 C 그림(성인 다윗)이다. 새 명세 다시 그리기는 task 397.

## 고정 절 (생성 전, 2026-10-22)

- **재료**: `~/.local/biblemap-imggen/lora-v3-scene/C-s{11,42,7,23,5,101,202,303}.png` 8장(LoRA 없이 그린 기브아 창, 옛 명세) · 머리 상자 `samples/face-lora-v3/heads.json`(C 8장 모두 사울·다윗 둘) · 어댑터 `~/.local/biblemap-imggen/lora/{saul,david}-v3.safetensors`.
- **보정**: 393과 같은 방식 — 머리 상자 긴 변 × `FACE_DETAIL_MARGIN`(2.4) 정사각(그림 안으로 밀어 넣음)을 `FACE_DETAIL_SIZE`(768)로 키워 Z-Image-Turbo Q8 img2img `FACE_DETAIL_STRENGTH`(0.3), 9스텝, 시드 = 장면 시드. 문구 = 공용 화풍 머리 + 「head and shoulders close-up of」 + 트리거 낱말(`saul_bm`·`david_bm`) + 장면 명세 cast 서술. LoRA = **그 머리 인물의 V3 어댑터 하나**, 세기 `LORA_SCENE_SCALE`(1.0). 이번 프로세스는 V3만(LoRA 없는 생성 섞지 않음). 생성 프로세스 하나, 인코딩/생성 따로.
- **되붙임**: 보정 정사각(768)을 원래 정사각 크기로 LANCZOS 축소 → **머리 상자 중심 타원 마스크**(머리 상자 가로·세로 × `FACE_DETAIL_V3_PASTE_GROW` 1.3)를 가우스 흐림(반지름 = 머리 상자 긴 변 × `FACE_DETAIL_V3_PASTE_FEATHER` 0.12)으로 부드럽게 해서 C 원본 위에 합성. 정사각 전체가 아니라 머리만 바꾼다(정사각 가장자리의 배경·옷 결 차이를 피함). **색 맞춤 안 함** — img2img 0.3은 색을 거의 지키므로, 대신 마스크 안 평균 색 차(RGB)를 기록만. 한 그림의 두 머리를 차례로 붙임.
- **산출**: `~/.local/biblemap-imggen/face-detail-v3/heads/C-s<시드>-<인물>.png`(16) · `.../paste/C-s<시드>.png`(8) · 기록 `samples/face-detail-v3/log.json`(머리마다 kind=head·cast·seed·secs·active, 그림마다 kind=paste·색 차).
- **Claude 눈 확인**(가분수·다른 사람·이음새 뚜렷)은 기록만, 거르지 않음.
- **문항**(폰용 비공개 Artifact, 한 화면 한 질문, 화면마다 삼상 18:6-11 원문·18:10 굵게, 답 「판정 face-detail-v3」 → `samples/face-detail-v3/verdict.txt`):
  - **A**(32) 「정본과 같은 사람인가」 — 정본 정면·3/4와 판정할 머리를 같은 칸 크기로, 정본은 실측 선명도(라플라시안)를 머리에 맞춤(393 v2 규칙). 판정할 머리 = 이번 V3 보정 머리 16 + **대조군** 393 C 보정 머리(LoRA 없음, `face-detail/C-s*-*.png`) 16, 갈래 이름 없이 섞음.
  - **B1**(8) 「C 원본과 같은 화풍인가」 — C 원본과 완성 그림 나란히(어느 쪽이 어느 쪽인지 숨기지 않음 — 원본이 기준).
  - **B2**(8) 「머리 둘레에 이음새·색 차이·결 차이가 보이는가」 — 완성 그림의 두 머리 둘레(보정 정사각 영역) 확대. 「아니오(깨끗함)」가 통과.
- **채택 규칙**: **채택** = 사울·다윗 각각 A(V3 보정 머리) ≥ 5/8 **그리고** B1 ≥ 6/8 **그리고** B2 깨끗 ≥ 6/8. **조건부** = 한 인물만 A 충족(B1·B2 충족), 또는 A 둘 다 충족에 B1·B2 중 하나만 미달. **미채택** = 그 밖. 대조군(C 보정 머리)이 A에서 인물마다 3/8 이상이면 「판정이 너그러움」을 결론 옆에 적음.
- 승인 기록은 바꾸지 않는다(ADR 260905-104910 — 채택 여부만).

## 생성 (2026-10-22)

- `gen_face_detail.py v3paste` — 머리 16개 장당 약 17초(인코딩·모델 적재 포함 약 6분), 머리마다 활성 어댑터 = 그 인물 V3 하나(`samples/face-detail-v3/log.json`, DoD 2 통과). 되붙임 8장.
- **계획과 다른 점**: 394가 기브아 명세의 다윗을 `david-boy`로 바꿔 지금 명세로는 성인 다윗 서술이 안 나온다 → 문구의 cast 서술은 **394 앞 명세(`12a25b1^`)의 figures**에서 만들었다(`GIBEAH_393`). cast 서술 문장 자체는 지금 cast 정본 기준이라 393 실행 때 문구와 몇 낱말 다를 수 있다(393 jobs.json은 뒤 실행으로 덮여 대조 못 함).
- 타원 안 평균 색 차(보정 − 원본, RGB): 모든 머리 |Δ| ≤ 2.2 — 색 맞춤 없이도 작다.
- Claude 눈 확인(4시드, 기록만): 얼굴이 조금 바뀜(눈·눈썹 또렷, 사울 수염·얼굴꼴 약간), 다윗 곱슬 유지, 256px 크기에서 이음새·가분수·다른 사람 없음.

## 판정 화면

- `make_face_judge_v3.py` → 비공개 Artifact https://claude.ai/artifact/LFoqwpRz54S91JNyUJ6W5K (48문항: A 32 · B1 8 · B2 8, 5.8MB). 문항 A 정본 선명도 맞춤 비 ±30% 안 ≥ 90%(`test_face_judge_v3`). 답은 「판정 face-detail-v3」 문장으로 → `samples/face-detail-v3/verdict.txt`.
