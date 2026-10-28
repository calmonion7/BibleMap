# REF-ADAPTER — 정체성을 화풍과 따로 싣는 수단 외부 조사 (task 449, 2026-10-29)

[[정본 전이]](정본 얼굴을 장면 인물에 싣기)에서 인물 LoRA는 얼굴은 실었지만 화풍을 무너뜨렸다. 445·447·448에서 세 번 재현됐다(`LORA-V5.md` 「판정」).
img2img 세기로도 화풍과 정체성을 함께 지킬 수 없었다(448 S2). 이 노트는 **학습 없이 참조 그림에서 정체성을 받는 수단**이 지금 생성 스택에 있는지 조사한다.
지금 생성 스택은 Z-Image-Turbo Q8 GGUF이고, 기계는 Apple M5 · 메모리 32GB(`sysctl hw.memsize` = 34359738368)다.
생성·설치·내려받기는 하지 않았다. 조사 결과로 다음 시험 작업을 설계한다.

## 판정 기준 (고정 절 — 조사 전에 적음)

1순위 시험 후보가 되려면 다섯을 모두 만족해야 한다.
- (가) 가중치가 상업 이용 가능한 라이선스다. 358에서 Qwen-Image-2.1 edit를 비상업으로 뺀 선례를 따른다(`REF-EDIT.md:108`).
- (나) M5 32GB에서 돈다는 근거가 있다.
- (다) 한 장 10분 이하라는 근거나 추정이 있다(359·360 「안 돔」 문턱 600초와 같음).
- (라) 기반 모델이 Z-Image이거나, 바꿔도 화풍 도달을 다시 잴 길이 있다.
- (마) 얼굴 임베딩(A) 계열이면 아래 재검 (b)를 넘는 근거가 있다.

하나라도 만족하는 후보가 있으면 `시험할 후보 있음`, 없으면 `없음`이다. 근거가 없는 칸은 추측으로 채우지 않고 `근거 없음`이라고 적는다.

## 제외한 수단 (실측 실패 — 다시 조사하지 않음)

- **인물 LoRA**: 445·447·448에서 얼굴은 실렸지만 화풍이 무너졌다. 학습 묶음을 다시 칠해도 양립하는 세기가 없었다(`LORA-V5.md`).
- **klein 4B 다중 참조로 장면 얼굴 편집**: 349는 정면 참조 6/64, FACE-ANGLES는 정면·3/4 참조 모두 0/32였다(`FACE-ANGLES.md` 「사람 판정」). 화풍도 바탕보다 옅어졌다.
- **Qwen-Image-Edit-2511 원본 20스텝**: 장당 48~60분이라 실행 불가였다(`REF-EDIT-2511.md:68`). Lightning 4스텝 조합은 이와 달리 채택됐다. 아래 후보 표에 따로 둔다(어긋남 절 참고).
- **Qwen-Image-2.1 edit 세기 0.7**: 사실상 처치가 없었다(상자 안 변화 5/255). Qwen Research License라 비상업이다(`REF-EDIT.md:108`).
- **SDXL `ip-adapter-plus-face` 얼굴 인페인팅**: 얼굴만 갈아 넣는 방식이다(`ZIMAGE.md:325`). 「큰 부위 잘라붙이기 금지」(2026-10-21)에도 걸린다. 395의 V3 얼굴 되붙임도 원래 화소에서 결이 매끈한 붓칠로 바뀌어 미채택이었다(`FACE-DETAIL-V3.md:33`).

## 10-22 제외 근거 재검

10-22 외부 조사(`FACE-ANGLES.md:3`)는 얼굴 임베딩 계열(PuLID·InstantID·InfiniteYou·IP-Adapter FaceID)을 뺐다. 이유는 「ArcFace 신호에 기대므로 350과 같은 벽」과 「대부분 비상업」이었다. 그때 근거는 추론이었으므로 세 갈래로 나눠 다시 본다.

- (a) **판정과 조건은 다르다 — 맞다. 그러나 벽 하나만 풀린다.** 350(`FACE-ID-JUDGE.md:82`)이 잰 것은 ArcFace를 **판정자**로 쓴 경우다. 장면 속 옆얼굴과 정면 정본을 비교했고 같은 사람의 코사인이 0.1~0.3이었다. 어댑터는 **정면 정본**에서 임베딩을 뽑는다. 정면 정본은 검출된다. 검출 실패는 옆얼굴 정본 4장뿐이었다(david-old·endor-medium·jesse·nahash, `samples/face-id/metrics.json` `controls.det_fail`). 같은 정본을 조금 흔든 양성 대조도 최소 0.8629, 중앙값 0.967로 안정됐다. 그래서 「조건 입력을 못 뽑는다」는 벽은 없다(실측, 같은 파일). 하지만 조건으로 낸 얼굴이 장면의 작은 옆얼굴에서 정체성을 지키는지는 판정으로 확인해야 한다. 그 판정은 사람만 할 수 있다(350 no-go).
- (b) **「그림체를 사람으로 읽음」은 하필 사울과 다윗에서 문제다.** 서로 다른 정본 158쌍의 ArcFace 코사인은 중앙값 0.053, 상위 10% 0.275로 대체로 잘 갈린다. 그런데 **옛 사울~다윗 정본은 0.6526**이었다(같은 파일 `controls.neg`). 판정 문턱 τ는 0.2446이었다. 「젊은 수염 남자 둘」은 임베딩으로도 거의 같은 사람이다. 이 둘이 정본 전이가 막힌 바로 그 인물이다. 사울은 이제 새 정본 `saul-elder`(약 70)로 나이가 갈렸지만, 새 정본끼리는 재지 않았다(근거 없음). 따라서 (A) 계열은 그림체가 정체성 신호를 덮는다는 위험을 그대로 안는다. 10-22 판단은 이 점에서 맞았다.
- (c) **라이선스 — 10-22 판단이 맞고, 실제로는 더 좁다.** (A) 계열은 거의 모두 InsightFace 모델로 얼굴 임베딩을 뽑는다. InsightFace가 배포하는 모델(`buffalo_l` 등)은 「non-commercial research purposes only」이고, 상업 이용은 따로 문의해야 한다([insightface](https://github.com/deepinsight/insightface)). 어댑터 가중치가 apache여도 마찬가지다. InfiniteYou는 가중치부터 cc-by-nc-4.0이다. PuLID-FLUX·UNO·DreamO는 기반 FLUX.1-dev가 모델 사용 자체를 비상업으로 묶는다(2(b)). 출력은 상업 이용이 가능하다(2(d)).
- **재검 결론**: 10-22 제외는 결과적으로 유지된다. 다만 이유를 바로 적는다. 「ArcFace로는 조건을 못 뽑는다」가 아니다. 이유는 셋이다. ① InsightFace·FLUX.1-dev 비상업. ② 바꿔야 할 인물 쌍(사울·다윗)에서 임베딩 자체가 그림체에 묶임. ③ Z-Image용 이식이 없음(후보 표).

## 후보 표

조사일은 2026-10-29다. 계열은 다음과 같다. (A) 얼굴 임베딩 · (B) 일반 이미지 특징 · (C) 인컨텍스트·다중 참조 편집 · (D) Z-Image 계열 자체. Mac 칸의 「실측」은 이 레포 노트에 근거가 있다는 뜻이다.

| 이름 · 출처 | 공개 | 기반 | 계열 | 가중치 라이선스 | Mac 실행 · 메모리 | 한 장 시간 | 삽화에서 정체성 근거 | 화풍을 사진풍으로 끄는가 | 기준 |
|---|---|---|---|---|---|---|---|---|---|
| Z-Image-Edit · Omni-Base — https://github.com/Tongyi-MAI/Z-Image | **미공개**(README 「To be released」. HF `Tongyi-MAI` 모델은 Z-Image-Turbo·Z-Image·MAI-* 뿐, API 조회 2026-10-29) | Z-Image | D | 레포 apache-2.0 | 근거 없음 | 근거 없음 | 근거 없음(논문은 SigLIP2로 참조·편집 조건을 넣는다고만 함 https://arxiv.org/abs/2511.22699) | 근거 없음. 같은 기반이라 끄는 쪽이 적을 것(추론) | (가)(라) 예상 충족, 지금은 시험 불가 → 지켜봄 |
| Z-Image IP-Adapter 로더(Boyo, SD3 가중치 추출) — https://comfyai.run/documentation/BoyoIPAdapterZImageLoader | 근거 없음 | Z-Image(주장) | B | 근거 없음 | 근거 없음 | 근거 없음 | 근거 없음 | 근거 없음 | 3자 문서 하나뿐, 가중치 출처 불명 → 뺌 |
| **Qwen-Image-Edit-2511 + Lightning 4스텝** — https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning | 2025-12-22 | Qwen-Image(편집기). 바탕은 Z-Image로 그대로 그림 | C | 2511·LoRA 모두 apache-2.0(HF 태그 조회) | **실측**: q8 `--low-ram`으로 돌아감. 적재 피크 58.5GB(스왑). **설치돼 있음**(`~/.cache/huggingface/hub/models--Qwen--Qwen-Image-Edit-2511`·`models--lightx2v--…`) | **실측** 편집 1건 505.8초(360), 551초(368 평균 48건) | **실측**(카드 폭 356px): 사울 7/8 · 다윗 8/8 · 대조 0/3·2/3(361, ADR `261017-152627`). 368 기브아에서 다윗 「같은 사람 아님」 6/8은 편집본에서 생김(`NIGHT-PILOT.md:30`) | 카드 배율 「무너짐」 감점 0.11(360). **원래 화소·머리 둘레 Gram은 잰 적 없음** | (가)(나)(다)(라) 충족, (마) 해당 없음 → **1순위** |
| Qwen-Image-Edit-Causal — https://github.com/ModelTC/Qwen-Image-Edit-Causal | 2026-02-15 | Qwen-Image-Edit-2511 | C | apache-2.0(HF 태그) | 근거 없음(H100만 적힘, mflux 지원 근거 없음) | H100에서 참조 1장 1.27초 대 Lightning 1.85초, 3장 2.09초 대 4.66초 | 근거 없음(예시 6개 중 5개 ✅, 수치 없음) | 근거 없음 | (나) 미충족 → 2511 경로가 통하면 속도 후속 |
| PuLID-FLUX — https://huggingface.co/guozinan/PuLID | 2024-05(v0.9), FLUX 판 이후 | FLUX.1-dev | A | 어댑터 apache-2.0. 기반 FLUX.1-dev 비상업 https://huggingface.co/black-forest-labs/FLUX.1-dev/blob/main/LICENSE.md . InsightFace 비상업 | 근거 없음(mflux 명령 없음. stable-diffusion.cpp PR #1542 미병합) | 근거 없음 | 근거 없음(사진 예시뿐) | 근거 없음 | (가)(나)(라) 미충족 → 뺌 |
| InfiniteYou — https://huggingface.co/ByteDance/InfiniteYou | 2025-03 | FLUX.1-dev | A | cc-by-nc-4.0 | 근거 없음 | 근거 없음 | 근거 없음(3자 페이지의 「스타일 변환에서도 유지」 주장뿐) | 근거 없음 | (가) 미충족 → 뺌 |
| InstantID · IP-Adapter FaceID — https://aiofm.info/en/guides/pulid-vs-instantid-vs-faceid | 2024 | SDXL | A | InsightFace 비상업 | 근거 없음 | 근거 없음 | 근거 없음 | 근거 없음 | (가)(라) 미충족 → 뺌 |
| UNO · DreamO — https://huggingface.co/bytedance-research/UNO · https://huggingface.co/ByteDance/DreamO | 2025-04 · 2025-05 | FLUX.1-dev | C | 어댑터 apache-2.0, 기반 비상업 | 근거 없음 | 근거 없음 | 근거 없음 | 근거 없음 | (가)(나) 미충족 → 뺌 |
| OmniGen2 — https://huggingface.co/OmniGen2/OmniGen2 | 2025-06 | 자체(Qwen2.5-VL + 확산) | C | apache-2.0 | 근거 없음(README는 A800만, CPU 오프로드 TODO) | 근거 없음 | 근거 없음 | 근거 없음 | (나) 미충족 → 2511 경로가 막히면 다음 조사 |
| FLUX.1 Kontext dev — https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev | 2025-05 | FLUX.1 | C | 비상업(license: other) | 근거 없음 | 근거 없음 | 근거 없음 | 근거 없음 | (가) 미충족 → 뺌 |
| FLUX.2 klein 9B — https://docs.bfl.ai/flux_2 | 2026-01 | FLUX.2 | C | FLUX 비상업(4B만 apache — 4B는 제외 절) | 근거 없음 | 근거 없음 | 근거 없음(제조사 주장뿐) | 근거 없음 | (가) 미충족 → 뺌 |
| Qwen-Image-2.1 PE-I2I — https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I | 2026-09-20 | Qwen-Image-2.1 | C | license: other(2.1 계열 = Qwen Research License, `REF-EDIT.md:108`) | 근거 없음 | 근거 없음 | 근거 없음 | 근거 없음 | (가) 미충족 → 뺌 |

## 판정

- **판정: 시험할 후보 있음** — 1순위는 외부 신규 수단이 아니라 **이미 채택된 내부 경로**다. Qwen-Image-Edit-2511 + Lightning 4스텝 정본 참조 편집(ADR `261017-152627`)이다.
  - 다섯 기준을 모두 만족하는 유일한 후보다. 바탕은 지금 Z-Image로 그리고, 편집만 위에 건다. 그래서 화풍 도달은 바탕이 지키고, 편집이 화풍을 얼마나 바꾸는지만 재면 된다.
  - 이 경로는 10-17에 카드 배율에서 채택됐다. 그 뒤 화풍(원래 화소 같은 배율, 머리 둘레 Gram)과 얼굴(머리 크롭 같은 사람) 기준이 생겼지만, 그 기준으로 잰 적은 없다. 445 이후 LoRA로 다시 간 것은 이 경로를 재검한 결과가 아니었다. 기록상 마지막 사용은 10-20이다(`grep -rln 2511` 결과 마지막 계획 `261020-185521`).
  - 걸리는 점 셋.
    - ① 368 생산에서 사람이 편집본을 1/7만 골랐다. 기브아 다윗 「같은 사람 아님」 6/8도 편집본에서 생겼다(`NIGHT-PILOT.md:30`).
    - ② 몸 상자를 되붙인다(경계 8px). 「큰 부위 잘라붙이기 금지」와 부딪힐 수 있다. 다만 그 규칙은 klein 작은 크롭 + 색 맞춤 되붙임에서 나왔다.
    - ③ 편집 1건 8~9분, 적재 피크 58.5GB(스왑).
- Z-Image-Edit는 공개되면 (가)(라)를 바로 만족할 가능성이 크다(추론). 다음에 조사할 때 HF `Tongyi-MAI`부터 확인한다.
- (A) 얼굴 임베딩 계열은 재검 결과 유지해서 뺀다. 비상업이고, 사울·다윗 임베딩이 0.65로 겹치며, Z-Image용 이식이 없다.

## 첫 시험 설계 (고정 절 초안 — 숫자 문턱은 시험 작업에서 확정)

- **장면**: 기브아 창(`authored-saul-gibeah-spear`), 시드 11. 바탕은 445 `face-lora-v4/scene`의 **C**(LoRA 없음)를 그대로 쓴다. 다시 그리지 않는다.
- **인물·참조**: `saul-elder`(새 정본 s42)와 `david-youth`. 참조 그림은 `frozen/<id>.png`다. 전신 참조는 `lora-sheet-v2/<id>/07.png`가 지금 정본과 맞는지 먼저 본다. 맞지 않으면 초상만 쓴다(정본이 10-27·10-28에 바뀜).
- **편집**: ADR 1항 그대로(2511 q8 `--low-ram` + Lightning 4스텝, guidance 1, `mflux_qwen_edit_cfg1.py`). `{look}`은 정체성 서술 + 장면 명세 차림(361 개정)이다. 두 인물에 차례로 건다.
- **갈래**:
  - **C**: 바탕 그대로.
  - **E**: ADR 그대로, 몸 상자 되붙임.
  - **W**: 전체 편집 그대로, 되붙임 없음. ②를 따로 보기 위한 갈래다.
  - **T**(소음 바닥): 같은 편집을 바탕 인물 자신의 서술·자기 크롭으로 건다. 「편집기를 한 번 거쳤다」는 것만으로 바뀌는 화풍을 잰다.
- **화풍 먼저(싸게)**: 다윗·사울 머리 둘레를 445·448과 같은 길로 자른다(원래 화소, OWLv2 후보 중 가장 큰 상자, 448의 크롭 바탕 하한 교훈 반영). 거리는 DINOv2 Gram 2·6층 d(E,C)·d(W,C) 대 d(T,C)다. 이어서 사람 화풍 문항을 한 화면에 둔다(원래 화소 같은 배율, 화소 적은 쪽이 작게).
- **얼굴은 화풍을 통과할 때만**: 445 얼굴 A 문항 방식(정본 옆 머리 크롭 「같은 사람인가」), 그다음 8시드다.
- **하지 않음**: 새 내려받기(Causal·OmniGen2), 바탕 다시 그리기, 다른 장면.

## 어긋남 (계획 대비)

- 계획 「하지 않을 것」은 Qwen-Image-Edit-2511을 「359 — 한 장에 48~60분」으로 실측 실패에 넣었다. 실제로는 360에서 **Lightning 4스텝 조합이 채택**됐고, 그 ADR(`261017-152627`)은 지금도 유효하다(retired 아님). 그래서 원본 20스텝만 제외 절에 두고, Lightning 조합은 후보 표의 1순위로 옮겼다. 그릴링 때 이 ADR을 읽지 않은 탓이다.
