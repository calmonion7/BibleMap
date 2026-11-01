# NOB-STEP1 — 놉(다윗과 아히멜렉 — 골리앗의 칼을 받음, 삼상 21:1-9) 단계 ① 명세

옛 명세에는 meaning·relation·whole_background가 이미 있었으나 situation·stage_why·guide가 없었다. 지금 원장으로만 통과시키는 것을 먼저 노렸다. 통과 기준은 `spec_failures` 실패·못 잼 0과 scripture-reviewer 판정표 틀림 0이다. GPU는 쓰지 않았다.

## 시도 1 — 걸린 규칙 (2026-11-01)

| 규칙 | 걸린 까닭 |
|---|---|
| `spec.scene-all-verses` | `situation` 칸이 없다 |
| `spec.lexicon-link` | 진설병·칼·보자기·골리앗의 칼·에봇 요소의 사전 look 문구가 파생 프롬프트에 없다(「a linen ephod」·「huge cloth-wrapped sword」는 사전 L1~L3 문구가 아님) |
| `spec.stage-from-scripture` | ahimelech·david의 `stage_why`가 없다 |
| `generate.figure-scale` · `generate.height-ratio` | `guide`가 없어 못 잼 |
| `derive.prop-size-relative` | 21:9 「보자기에 싸여」가 잇는 사전 wrapped-in-cloth에 look.size가 없다 |
| `derive.no-inflating-build` | 파생 문구에 「huge」(골리앗의 칼) — 거인 아닌 인물이 있는 장면 |

## 보완

- **장면 구절**: 21:1-9 그대로. 21:1-8은 같은 방문·같은 대화로 고정한 순간(21:9 끝 — 칼이 건네짐)의 조금 앞이거나 같은 때다(`situation.same_time`). 20:42(요나단과 헤어짐)는 앞선 일, 21:10(그 날에 가드로 도망)은 뒤의 일이라 뺐다. 옛 명세 21:6 인용이 앞 두 문장에서 끊겨 있어 원문 전체로 고쳤다.
- **도엑 — 순간에 넣음**: 21:7 「그 날에 사울의 신하 한 사람이 여호와 앞에 머물러 있었는데」는 같은 날 같은 자리 [직접]. 그가 칼을 건네는 것을 보았다는 것은 22:9 「아히멜렉에게 이른 것을 내가 보았었는데」 · 22:10 「골리앗의 칼도 주더이다」 · 22:22 「그 날에 에돔 사람 도엑이 거기 있기로」에서 [추론]. 옛 명세는 배경의 「a lone man」(카드 없는 사람)으로 두었으나, 도엑 카드·얼굴 정본(stops에 이 장면)이 있어 세 번째 인물로 올렸다. 자리(오른편 뒤 장막 곁)는 저작.
- **사람 수**: 셋(다윗 · 아히멜렉 · 도엑). 21:2의 소년들은 다른 곳에 있고(21:1 「홀로 있고」), 놉의 다른 제사장들(22:11)은 이 자리에 있었다는 말이 없어 그리지 않는다.
- **지리**: 놉 = 제사장들의 성읍(22:19 [직접]). 자리는 여호와 앞 — 21:6 「여호와 앞에서 물려 낸 떡」 · 21:7 「여호와 앞에 머물러」 · 21:9 「에봇 뒤」로 성소 곁 [추론], 성소가 장막인 것은 삼하 7:6 「장막과 회막에 거하며 행하였나니」 [추론]. 다윗은 숨어 있던 들(20:24 · 20:41)에서 요나단과 헤어져 왔고 화면 오른쪽(바깥)에서 왼쪽 아히멜렉을 마주한다. 장막 휘장은 뒤로 길게 늘어서고 도엑은 오른편 뒤 휘장 앞에 선다(좌우·앞뒤 저작 — 본문 검토 1차로 고침).
- **진설병 — 받은 떡을 다윗 발치에**: 21:6에서 떡은 이미 다윗에게 건네졌다. 옛 명세처럼 장막 안 상에 쌓아 두면 건넨 떡이 아니라 새로 드린 떡이 된다. 다윗 손은 칼을 받으므로(한 사람 지물 하나) 받은 떡은 다윗 발치 천 꾸러미 위에 둔다(자리·덩이 수 저작 — 처음엔 평평한 돌이었으나 제단 예물처럼 읽혀 본문 검토 1차로 고침).
- **에봇 — 걸어 둔 옷**: 21:9 「에봇 뒤에 있으니」는 아히멜렉이 입은 에봇 뒤일 수 없어 따로 놓인 에봇 [추론], 휘장 곁 못에 걸어 둠은 저작(사전 ephod L3 「걸어 두면 …」). 아히멜렉 자신은 세마포 에봇 차림(22:18 [추론]).
- **사전 문구 단계** (`spec.lexicon-link`):
  - 골리앗의 칼: (시도 1~3) L3 「A giant's sword with a broad heavy blade, …」 — L1·L2와 held 문구에 「huge」가 있어 `derive.no-inflating-build`와 부딪쳐 L3로 피했으나, L3는 날을 보여 21:9 「보자기에 싸여」와 어긋났다. (시도 4) 규칙을 고친 뒤 L1 「a huge long sword」로 바꿈.
  - 칼: L1 「a straight iron sword」 — 21:9 「골리앗의 칼이」(꼴 「칼이」)와 21:8 「내 칼과」(꼴 「칼과」) 둘이 sword 항목에 걸린다. 관계 문구에서 건네지는 칼에 실었다.
  - 보자기: L1 「a sword wrapped in cloth」(아히멜렉 몸짓) · (시도 4) L2 「a sword wrapped round and round in cloth so the blade cannot be seen, longer than a man's arm」(관계 — 날이 안 보임).
  - 진설병: L3 「several flat loaves bigger than a palm, stacked up」(배경).
  - 에봇: L1 「a priest's vest-like garment」(배경).
  - 손 지물(`derive.prop-size-coverage`): 아히멜렉·다윗 prop은 goliath-sword held 「a huge cloth-wrapped sword」·「the huge cloth-wrapped sword」 그대로(파생 프롬프트에는 실리지 않음), 도엑은 `none`.
- **생애 단계(stage_why)**
  - 다윗: [추론] 삼상 18:13 · 18:27(소년기 지남) ~ 삼하 5:4(상한), 20:42 바로 뒤 · 21:10 같은 날 가드. 연대 정본 BC 1013경으로 약 27세 → id david(갓 아기스 장면과 같은 날).
  - 아히멜렉: [추론] 삼상 22:20 · 23:6 — 에봇을 맡을 만큼 자란 아들 아비아달이 있어 중년, 22:11 놉 제사장 집의 어른 → id ahimelech(단계 카드 하나, 50대는 카드 값).
  - 도엑: [추론] 삼상 21:7 「사울의 목자장」 · 22:9 「사울의 신하 중에 섰더니」 — 직책이라 다 자란 어른 → id doeg(40대는 카드 값).
- **몸짓·뼈대**: 아히멜렉 「두 손으로 … 내민다」는 `generate.pose-hold`(손 … 내밂)에 들어 뼈대 `plead_out`(두 팔을 가슴 높이로 앞으로 뻗어 두 손목을 나란히). 다윗은 `speak_open_left`(앞 팔을 화면 왼쪽으로 뻗음)로 한 손을 뻗어 칼 꾸러미 끝을 잡음 — 두 손으로 받는 왼쪽 뼈대가 없어 한 손으로 저작했다(→ 「막힘」 ③). 도엑은 뼈대 없이 서 있는 사람 꼴. `guide.split` true.
- **크기**: 사람 수 3 → 무리 단계 small(0.45~0.60). 아히멜렉·다윗 구역 높이 0.58 · 발 0.92. 도엑은 지평선(0.92 − 0.93 × 0.58 ≈ 0.381)에서 발 0.81에 서면 키 0.46 → 구역 [0.80, 0.35, 0.91, 0.81](height-ratio ± 0.04 · figure-scale 하한 0.45 둘 다 안).

## 시도 2 — 걸린 규칙

| 규칙 | 걸린 까닭 | 고침 |
|---|---|---|
| `derive.512-tokens` | 한 장 프롬프트 526토큰 — 카드 셋(90~127토큰씩) | 아히멜렉 몸짓 「resting across his palms」, 도엑 몸짓 「arms at his sides」, 관계 영문 「the two men look at each other while the herdsman watches from the back」(인물 칸 gaze·gesture와 겹침)을 덜어 512 안으로 |
| `derive.prop-size-relative` | 사전 wrapped-in-cloth에 look.size 없음 | **고치지 않음** — 사전 항목 문제라 멈추고 보고(아래 「막힘」 ①) |

파생 문구 눈 확인에서 도엑의 시선이 「looking toward the lean young man on the right」로 나왔다 — 도엑이 다윗보다 오른쪽에 있는데 파생 코드가 다윗을 「오른쪽」으로 부른다. 도엑의 `gaze`를 ahimelech로 바꿔 「looking toward the middle-aged priest on the left」(facing left와 맞음)로 고쳤다.

## 시도 3 — 규칙 재검 · 가이드 눈 확인

`spec_failures('authored-david-nob-priests')` → `derive.prop-size-relative` 하나(사전 wrapped-in-cloth look.size 없음) · `derive_scene --check --figures whole` 통과.

가이드 눈 확인(`samples/nob-step1/guide-1.png` 뼈대 · `guide-2.png` 깊이):
- 첫 판(아히멜렉 [0.22–0.37] · 다윗 [0.60–0.75])은 두 사람 손목 사이가 가이드 1216px에서 약 290px — 골리앗의 칼 길이(사전 size 0.6 × 키 0.58 × 640px ≈ 223px)보다 멀어 칼 한 자루를 둘이 함께 잡을 수 없었다. 두 구역을 가운데로 0.06씩 옮겨(아히멜렉 [0.28–0.43] · 다윗 [0.54–0.69] · `judge.gap_bands` [0.43, 0.54]) 손목 간격 약 150px로 맞췄다.
- 고친 판: 아히멜렉 두 팔이 가슴 높이로 다윗 쪽에 나란히, 다윗 앞 팔이 아히멜렉 쪽에 뻗음. 도엑은 오른편 뒤에 깊이 0.85 사다리꼴로 작게(머리가 두 사람보다 아래). 세 사람 발 높이·크기가 명세와 맞는다. 화면 왼쪽 0~0.28은 비어 장막 휘장·걸어 둔 에봇 자리(문구가 맡음).

## 시도 4 — 사전·규칙 고친 뒤 (task 488)

사전 wrapped-in-cloth look.size가 생기고 `derive.no-inflating-build`가 몸 낱말이 뒤따를 때만 걸리게 좁혀져(아래 「막힘」 ①②), L3로 피했던 문구를 걷었다.

- 관계 영문: 「a giant's sword with a broad heavy blade, longer than a man's arm. It looks so heavy that a man holds it with both hands」(날이 보임 — 21:9 「보자기에 싸여」와 어긋남) → 「a huge long sword, a sword wrapped round and round in cloth so the blade cannot be seen, longer than a man's arm」(goliath-sword L1 + wrapped-in-cloth L2).
- 요소 21:9 「골리앗의 칼이」 en → 「a huge long sword」. 「보자기에 싸여」 ko에 L2(날이 보이지 않음)를 적음.
- 아히멜렉 두 손 근거에서 L3 「두 손으로 받쳐 들어요」를 빼고 「두 손·손 자세 본문 밖 · 저작자 정함」으로.
- 재검: `spec_failures` → `[]` · `derive_scene --check --figures whole` 통과(512 안). 고정 절 488 문항은 낱말이 바뀌지 않아 그대로(`t.wrapped`·`t.big-sword`가 이 문구를 잰다).

## 단계 ③ 문항 등급 (단계 ①에서 미리 정함)

본문이 직접·추론으로 말하는 것은 거르기, 본문 밖 자세·자리·재질·색은 기록이다(RAMAH·ZIKLAG와 같은 원칙).

| 구절 요소 / 인물 칸 | 근거 | 문항 등급 |
|---|---|---|
| 제사장과 젊은 남자 | [직접] 21:1 · 21:9 | 거르기 `t.two-men` |
| 제사장 세마포 차림 | [추론] 22:18 | 거르기 `t.linen` |
| 마주 봄 | [추론] 21:9 대화 | 거르기 `t.facing` |
| 제사장이 칼을 건넴 | [직접] 21:9 「가지려거든 가지라」(내어 줌) · 22:10 「골리앗의 칼도 주더이다」(건네짐 — 평행 기사) | 거르기 `t.handing` |
| 다윗이 손을 뻗어 받음 | [직접] 21:9 「내게 주소서」 | 거르기 `t.receiving` |
| 둘이 같은 칼 한 자루 | [추론] 21:9 | 거르기 `t.same-sword` |
| 다른 무기 없음 | [직접] 21:9 「여기는 그 밖에 다른 것이 없느니라」 | 거르기 `t.one-sword` |
| 칼이 천에 싸임 | [직접] 21:9 「보자기에 싸여」 | 거르기 `t.wrapped` |
| 큰 칼(팔보다 김) | [추론] 21:9 「그같은 것이 또 없나니」 · 사전 size | 거르기 `t.big-sword` |
| 다윗 허리에 무기 없음 | [직접] 21:8 | 거르기 `t.unarmed` |
| 다윗 성인 | [추론] 18:13 · 18:27 · 삼하 5:4 | 거르기 `t.adult` |
| 걸어 둔 에봇 | [직접] 21:9 에봇 · [추론] 걸어 둠 | 거르기 `t.ephod` |
| 진설병(납작한 떡 여러 덩이) | [직접] 21:6 | 거르기 `t.bread` |
| 장막 | [추론] 21:6-7 · 삼하 7:6 | 거르기 `t.tent` |
| 도엑(목자 차림 셋째 남자) | [직접] 21:7 | 거르기 `t.doeg` |
| 도엑이 지켜봄 | [추론] 22:9-10 · 22:22 | 거르기 `t.doeg-watching` |
| 세 사람뿐 | [추론] 21:1 · 다른 제사장 언급 없음 | 거르기 `t.only-three` |
| 제사장 떨며 근심(건넬 때) | [직접] 21:1은 맞을 때만 · 건넬 때까지 이어짐은 [저작] | 기록 `t.trembling`(본문 검토 1차로 거르기 → 기록) |
| 다윗 20대 · 제사장 두 손 · 다윗 한 손 · 다윗 급한 얼굴 · 붉은 튜닉 · 도엑 자리(휘장 앞) · 도엑 회갈색 튜닉 · 에봇 못 · 떡 자리(천 꾸러미) · 돌담 흙뜰 | [저작] | 기록 |
| 화풍 · 덩어리 · 후광 · 교회 · 가드 · 몸 꼴 · 몸 비율 · 팔 모양 | 장면 공통(ZIKLAG fixed 483 글자 그대로) | 거르기 |

고정 절은 `notes/NOB-STEP23.md` 「```json fixed 488」(8시드 · 문항 36개 중 기록 11).

## 막힘 — 사전·규칙 (task 488에서 둘 풀림)

1. ~~사전 wrapped-in-cloth에 look.size 없음~~ → **풀림(task 488)**: 사전에 look.size(man-height 0.6 · 「longer than a man's arm」, 싼 칼과 같은 길이)를 넣고 L2에 그 문구를 실음. 명세 쪽은 21:9 「보자기에 싸여」를 빼거나 kind를 바꾸지 않고 기다렸다.
2. ~~골리앗의 칼 사전 문구 ↔ `derive.no-inflating-build`~~ → **풀림(task 488)**: 부풀림 낱말 뒤에 몸 낱말(torso·chest·body·build·shoulders·man …)이 이어질 때만 걸리게 좁힘 — 「a huge long sword」·「huge cloth-wrapped sword」 같은 지물 문구는 체격이 아니다.
3. **두 손으로 받는 왼쪽 뼈대 없음**: `plead_out`은 화면 오른쪽만 있다(`speak_open_left`·`cradle_stand_left`는 x 뒤집기 한 줄로 있음). 다윗을 한 손으로 저작해 지금은 막히지 않지만, 두 손으로 받게 하려면 make_guide에 `plead_out_left`가 필요하다.
4. (참고) 파생 코드의 시선 문구는 인물을 전체 좌우로만 불러, 맨 오른쪽 인물이 오른쪽 인물을 볼 때 「on the right」가 나온다(이번에는 gaze를 바꿔 피함).

## 본문 검토 (scripture-reviewer)

### 1차 — 틀림 0 · 약함 8 → 모두 고침

| 지적 | 고침 |
|---|---|
| 21:9는 내어 줌·청함까지만 — 건네짐의 근거가 없음 | moment.why · same_time 21:9 · 문항 `t.handing` 근거에 22:10 「골리앗의 칼도 주더이다」 [직접](평행 기사) |
| 같은 방문의 여호와께 물음이 상황에 빠짐 | situation에 「22:10 · 22:13 [직접] · 21:1-9와의 순서는 본문에 없음 — 그리지 않는다」 |
| 관계 영문 「a straight iron sword」가 맨 칼로 읽힐 수 있음 | 「a straight iron sword, still wrapped in its cloth, passing …」(사전 sword L1 글자는 그대로) · 장면 negatives와 S3·S4 neg에 「bare blade」·「unsheathed blade」 |
| 도엑이 「여호와 앞」(21:7)인지 자리가 흐림 | 배경 영문 「a heavy tent curtain stretching along the back」 · situation 좌우 문장에 도엑이 오른편 뒤 휘장 앞에 머묾(21:7 「여호와 앞에 머물러」) |
| 도엑 옷 「rough·undyed」에 근거 없음 | 「a plain gray-brown wool herdsman's tunic」 · 「거칠기·물들이지 않음은 본문 밖 · 저작자 정함」 |
| 떡을 평평한 돌 위에 둔 것이 제단 예물처럼 읽힘 | 다윗 발치 천 꾸러미 위로(배경·S1·요소·same_time — 자리는 저작) |
| 아히멜렉 떪이 건넬 때까지 이어짐을 [추론]으로 씀 | 「건넬 때까지 이어짐은 본문 밖 · 저작자 정함」 · `t.trembling` 거르기 → 기록 |
| situation 「들」 근거 20:35는 요나단이 주어 | 20:24 「다윗이 들에 숨으니라」 · 20:41 「다윗이 곧 바위 남편에서 일어나서」 |

재검: `spec_failures` → `[]` · `derive_scene --check --figures whole` 통과(512 안). 고정 절 488 고침 — `t.handing` 근거 · `t.trembling` 기록 · `t.doeg-tunic`·`t.doeg-back` 문구 · `t.bread-stone` → `t.bread-bundle`(천 꾸러미).

참고: 장면 `negatives` 칸은 38명세 모두 비어 있고 지금 파생 코드가 읽지 않는다(부정어는 단계 `neg`만 씀) — 한 장 모드에서 실제로 먹는 것은 관계 영문의 「still wrapped in its cloth」다.

### 2차 — 틀림 0 · 약함 1 → 고침

- 거르기 문항 `t.doeg`가 「거친 목자 차림」을 물음(거칠기는 저작으로 내렸는데 문항에 남음) → 「목자 차림」. 도엑 costume.verse의 낡은 메모를 「색·수수함은 본문 밖 · 저작자 정함」으로.

**단계 ① 통과** — `spec_failures` → `[]` · 본문 검토 틀림 0. 규칙 고침 1(derive.no-inflating-build 좁힘)·사전 보강 1(wrapped-in-cloth 크기)은 task 488 커밋 3977290.
