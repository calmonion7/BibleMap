# S4 — 장면 생성 (task#315)

같은 콘티 조건 입력(`cond-scene-ctrl.png`, `--at 9000`) · `SCENE_CN=0.8` · `STEPS=30` · `GUIDANCE=6.5` ·
1216x640 · `ip_adapter_scale=0.3`(S2 판정) · 시드 {11, 42, 7} 고정으로 네 조건 × 3시드 = 12장을
생성했다. 스크립트: `gen_scene.py`. 로그: `gen_scene.log`.

## 1. 네 조건을 무엇으로 구현했는가

| 조건 | 파일명 | IP-Adapter | 레퍼런스 | 마스크 |
|---|---|---|---|---|
| (a) | `a-none-s{11,42,7}.png` | **미로드**(unload가 아니라 애초에 `load_ip_adapter`를 호출하지 않음) | 없음 | 없음 |
| (b) | `b-nomask-s{11,42,7}.png` | 로드, N=2, scale=[0.3,0.3] | 다윗+골리앗(`frozen/*.png`) | 없음 — `cross_attention_kwargs` 미전달, 두 레퍼런스가 화면 전체에 걸린다 |
| (c) | `c-mask-s{11,42,7}.png` | 로드, N=2, scale=[0.3,0.3] | 다윗+골리앗 | `masks/david.png`↔다윗, `masks/goliath.png`↔골리앗 |
| (d) | `d-mask-bg-s{11,42,7}.png` | 재로드, N=3, scale=[0.3,0.3,0.3] | 다윗+골리앗+배경(`bg-ref.png`, 아래 §2) | 위 둘 + `masks/background.png` |

(a)→(b)/(c) 사이에 어댑터를 한 번(N=2)만 로드하고, (d)로 넘어갈 때 `unload_ip_adapter()` 후
N=3으로 다시 로드했다 — diffusers는 어댑터 개수가 바뀌면 재로드가 필요하다(실측, 아래 §3).

## 2. (d)의 배경 레퍼런스 — 출처와 근거

**출처**: `gen/bg-on-s11.png`(1216x640, 이미 있는 장면 산출물) + `masks/background.png`(여집합 마스크).

**만드는 법**: bbox 크롭이 아니라 **마스크 합성**을 골랐다. `masks/background.png`는 두 인물
모양의 "구멍"이 뚫린 형태라 배경 잉크 픽셀의 바운딩 박스를 구하면 캔버스 전체가 나온다(구멍이
화면 가장자리에 닿지 않으므로) — bbox 크롭이 원본과 다를 게 없어 무의미하다. 대신
`PIL.Image.composite(bg_on, blank, mask)`로 인물 구멍 자리를 **배경 자신의 평균 RGB**로 메웠다.
채울 색을 손으로 고르지 않고 배경 마스크가 덮는 실제 픽셀에서 파생했다(파라미터 0, eco) —
실측값 `fill_color=(250, 239, 222)`로, `STYLE` 프롬프트의 "warm cream paper"와 방향이 맞는
크림색이 나왔다(우연이 아니라 배경 자체가 이미 그 색조로 그려졌기 때문).
결과: `bg-ref.png`.

## 3. 스모크에서 고친 것 — `ip_adapter_masks` 리스트 중첩

계획 인수인계 문면의 배선 예시 `cross_attention_kwargs={"ip_adapter_masks": [masks]}`(마스크
텐서를 리스트로 한 번 더 감싼다)를 그대로 썼더니 조건 (c) 시드 11 스모크가 즉시 실패했다:

```
ValueError: Length of ip_adapter_masks array (1) must match length of self.scale array (2)
and number of ip_hidden_states (2)
```

**원인(실측, diffusers 0.40.0 `attention_processor.py:4310-4312`)**: `IPAdapterMaskProcessor.preprocess()`
는 이미 `(N, 1, H, W)` 텐서 하나를 돌려준다. 이걸 파이썬 리스트로 한 번 더 감싸면 `len(...)==1`로
읽혀 어댑터 개수(2)와 안 맞는다. diffusers는 **리스트가 아닌 텐서를 받으면** 내부에서
`list(tensor.unsqueeze(1))`로 알아서 N개로 쪼갠다 — 감싸지 않고 텐서 그대로 넘겨야 한다.

**고친 배선**: `cross_attention_kwargs={"ip_adapter_masks": masks}` (masks = `proc.preprocess([...])`의
반환값 그대로, 리스트로 감싸지 않는다). 이 형태로 재실행해 스모크(c-mask s11)가 통과했다.

## 4. 실측 배선 형태 (diffusers 0.40.0)

- `pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name=["ip-adapter_sdxl.bin"]*N)`
  — N=2((b)(c)) 또는 N=3((d)). 개수가 바뀌면 `unload_ip_adapter()` 후 재로드해야 한다(실측 확인).
- `pipe.set_ip_adapter_scale([0.3]*N)`
- `ip_adapter_image=[[ref1],[ref2],...]` — 어댑터마다 이미지 리스트 하나(1장씩).
- 마스크 배선(조건 (c)(d)에서만): `masks = IPAdapterMaskProcessor().preprocess([mask1, mask2, ...],
  height=640, width=1216)` → `tuple(masks.shape) == (N, 1, 640, 1216)`, `dtype=torch.float32`.
  `cross_attention_kwargs={"ip_adapter_masks": masks}` — **리스트로 감싸지 않는다**(§3).
- 조건 (a)(b)는 `cross_attention_kwargs`를 아예 전달하지 않는다((b)는 `ip_adapter_image`만 전달).

## 5. 프롬프트 — `bg_on` 채택

`derive_prompts.py`를 다시 돌려 `prompts.json`을 신선하게 재생성한 뒤 `bg_on`을 네 조건 전부에
동일하게 썼다(`bg_off`는 쓰지 않았다). 근거:

1. **이미지·텍스트 조건 일치**: 조건 (d)가 배경 레퍼런스 이미지를 태우므로, 텍스트도 배경 어휘를
   실어야 이미지·텍스트 두 조건이 같은 것을 말한다(NEEDS.md §2가 이미 지적한 원칙 — "조건 입력과
   프롬프트가 같은 것을 말해야 한다"의 직접 적용).
2. **변수를 하나로 가둔다**: 네 조건(a~d)의 유일한 실험 변수가 IP-Adapter/마스크 축이어야 S5
   판정이 깨끗하다. 프롬프트까지 조건마다 바꾸면(가령 (a)(b)(c)는 `bg_off`, (d)만 `bg_on`) 두 축이
   섞여 SWEEP.md의 교훈("원인이 셋이면 섞으면 못 가른다")을 반복하게 된다.
3. **토큰 여유 확인됨**: `bg_on` 프롬프트는 75/77 토큰으로 이미 `gen_candidates.py`에서 검증됐고
   이번 실행에서도 다시 게이트를 통과했다(§6).

## 6. CLIP 77토큰 게이트

파이프라인 tokenizer로 재실측(하드 게이트, 초과 시 `sys.exit`):

| 대상 | 토큰 수 |
|---|---|
| prompt(bg_on) | 75/77 |
| negative | 40/77 |

## 7. 산출

12장 전부 `.forge/reports/canon-pilot/scene/`에 존재, 전부 RGB·1216x640·625~789KB. sha256 전수 상이를
`gen_scene.py`가 스크립트로 단정한다(끝의 `assert len(set(digests)) == len(digests)` +
`assert len(outputs) == 12`, 콘솔 "SANITY 통과 — 12장, sha256 전수 상이").

| 조건-시드 | sha256(앞 16자) | 생성 시간 |
|---|---|---|
| a-none-s11 | `ca89eb2697988b99` | 59s |
| a-none-s42 | `4f8ddb0a9fbb90d8` | 93s |
| a-none-s7 | `d2cd40203b9de62e` | 100s |
| b-nomask-s11 | `fa123fca50477647` | 128s |
| b-nomask-s42 | `2bfc7bc94cbd2e5f` | 144s |
| b-nomask-s7 | `e336ad61cb03dcac` | 170s |
| c-mask-s11 | `9e39bc0d1ca2a6b1` | 138s(스모크 겸용, §3 정정 후) |
| c-mask-s42 | `1a5a7a88ed0f5f7a` | 165s |
| c-mask-s7 | `b8dea23491fd5f25` | 173s |
| d-mask-bg-s11 | `0fdb7272063ca7d0` | 601s(이례적으로 느림, 아래 참고) |
| d-mask-bg-s42 | `2b565a4b46202c1f` | 186s |
| d-mask-bg-s7 | `aea613b5333885dc` | 534s |

**합계(실제 GPU 연산 시간, 12장 개별 시간의 합) = 2,491s(약 41.5분).** 조건별 평균: (a) 84s ·
(b) 147s · (c) 159s · (d) 440s — 어댑터 개수(N)가 늘수록, 마스크가 붙을수록 느려지는 방향은
일관되나 (d)의 s11(601s)·s7(534s)이 s42(186s)보다 3배 가까이 느려 **어댑터 개수만으로 설명되지
않는 변동**이 있다(§1의 vm_stat 실측 — 이 머신이 32GB 중 대부분을 이미 점유해 여유 메모리가
수백MB대였다. 압축 메모리 페이지인/아웃 부담이 실행마다 달라졌을 가능성이 크다 — 확정 원인은
아니고 관측만 남긴다).

**두 프로세스 실행**: §3의 `ValueError`로 1차 실행이 `c-mask-s11` 생성 도중 죽었다(1차 로그는
`gen_scene.log.smoke-fail-1`로 보존). 1차 실행에서 이미 만들어진 `a-none-s{11,42,7}.png` 3장은
`gen_one()`의 기존 파일 스킵 로직으로 2차 실행에서 재생성하지 않고 그대로 채택했다(sha256도 1차
산출물 그대로) — 위 표의 a-none 세 행의 생성 시간은 1차 로그(`gen_scene.log.smoke-fail-1`)에서,
나머지 9행은 2차 로그(`gen_scene.log`)에서 가져왔다. `gen_scene.log`가 스크립트 안에서 직접
출력하는 "12장 완료 총 2259s"는 2차 프로세스 하나만의 벽시계 시간(스킵된 a-none 3장은 거의
0초로 지나갔으므로)이라 위 2,491s와 다르다 — 둘 다 정확하지만 **2,491s가 "12장을 실제로 그리는 데
든 GPU 시간"의 올바른 합계**이고 2,259s는 "그 시간에 두 번째 프로세스가 떠 있던 시간"이다.

12장 몽타주(시드 11, 네 조건): `scene-s11-montage.png`(육안 확인용, 판정 아님) — 다윗(좌)·골리앗
(우)이 네 조건 전부에서 콘티와 같은 좌우 배치·규모 대비로 나타난다는 사실만 확인했다(S5의 판정
문항 ①②③에 해당하는 시각적 사실이나, 이 슬라이스는 판정을 내리지 않는다 — S5에 넘긴다).
