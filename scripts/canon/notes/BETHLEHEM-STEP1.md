# BETHLEHEM-STEP1 — A2(베들레헴 — 사무엘이 다윗에게 기름 붓다, 삼상 16:13) 단계 ① 명세 (task 588)

일정 페이지의 유형별 개척 A2(의식·큰 무리)다. 옛 판 명세(meaning·whole_background 없음, `stages`만)에 옛 승인(local-edit s42, 사람 메모 「기름을 부으는 위치가 이상함」)이 있다. 장면 전체 칸을 새로 쓰고 `stages`도 같은 말로 맞췄다. 통과 기준은 `spec_failures` 실패·못 잼 0과 scripture-reviewer 판정표 틀림 0이다. GPU는 쓰지 않았다.

## 시도 1 — 걸린 규칙 (2026-11-04)

| 규칙 | 걸린 까닭 |
|---|---|
| `spec.whole-fields` | meaning·relation·whole_background·인물 문구 칸이 없다(옛 판) |
| `spec.scene-all-verses` | `situation` 칸이 없다 |
| `spec.lexicon-link` | 「기름 뿔을 취하여」 요소의 사전 oil-horn look 문구가 파생 프롬프트에 없다 |
| `spec.stage-from-scripture` | samuel·david-boy·jesse의 `stage_why`가 없다 |
| `generate.figure-scale`·`youth-height`·`height-ratio`·`eye-level-perspective` | `guide`가 없어 못 잼 |
| `derive.prop-size-relative` | 사전 oil(액체)에 look.size가 없다 — **오탐**(아래) |
| `spec.crowd-era-dress` | 형 무리 옷 문구가 없다 |

## 보완

- **장면 구절**: 16:4-5(베들레헴 · 제사에 청함) · 16:10(형 일곱) · 16:11(말째가 양을 지킴) · 16:12(모습 · 「일어나 기름을 부으라」) · 16:13(순간). 16:6-9(엘리압·아비나답·삼마)는 16:10이 「일곱으로 다」로 묶어 따로 넣지 않았다.
- **그 자리의 사람**: 형 일곱은 「그 형제 중에서」 [직접]. 이새는 16:10-11에서 아들들을 지나게 하고 사무엘과 말을 주고받은 이라 [추론]. 장로들(16:4-5)은 제사에 청함을 받았으나 기름 붓는 순간에 있었다는 말이 없어 그리지 않는다.
- **장소**: 16:5 「제사에 청하니라」 → 제사 자리 [직접]. 제단 연기는 16:2 「암송아지를 끌고 가서 … 제사를 드리러 왔다」에서 [추론]. 빈터·돌담·흙벽 집은 [저작].
- **여호와의 신**(16:13): 형상 없이 — 요소 `out`(ADR 261025-120741).
- **생애 단계**: 사무엘 — 8:1 · 12:2 노년(id samuel). 다윗 — [직접] 16:11 「아직 말째가 남았는데 그가 양을 지키나이다」 + [추론] 17:33·17:42 → 소년(id david-boy). 이새 — [직접] 17:12 「나이 많아 늙은 자로서」(id jesse).
- **지물**: 사무엘 기름 뿔(사전 oil-horn L1 「an animal horn full of oil」) · 다윗 빈손(두 손 몸 앞 — 두 손 보임) · 이새 지팡이(사전 walking-staff, [추론] 슥 8:4). 다윗의 목자 지팡이는 뺐다 — 본문에 없는 지물이고, 16:11 「양을 지키나이다」는 목자 소년 차림(무릎 길이 물들이지 않은 튜닉)으로 실었다.
- **크기**: 사람 수 10 → 무리 단계 small(0.45~0.60). 초점 사무엘 0.56 · 발 0.92 → 지평선 0.399. 다윗 0.515(short), 형 무리 발 0.84 · 0.48, 이새 발 0.88 · 0.517.
- **구도 가이드**: 카드 인물 셋 모두 새 뼈대(`make_guide.POSES`) — 사무엘 `pour_over`(앞 팔을 들어 손목이 다윗 숙인 머리 위 · 다른 손 가슴께), 다윗 `bow_clasp_left`(listen_clasp에서 머리만 숙임), 이새 `staff_hold_left`(앞 손이 지팡이 위끝 가까이). 형 일곱은 다윗 뒤 무리 꼴. 무리 너비 0.42 = 보이는 실루엣 약 일곱(0.39는 여섯).
- **파생 머리 낱말**: 사무엘·다윗 구역 가운데가 둘 다 0.4 미만이면 둘 다 「On the left, in front:」(같은 발 y)가 되어 인물 절이 갈리지 않는다 — 다윗 구역 가운데를 0.414로 옮겨 「In the center:」.

## 규칙 고침 (오탐 좁힘)

- `derive.prop-size-relative`(`recheck.prop_size_errors`): 한 인용에 여러 사전 항목이 걸리면 구체 항목만 크기 대상 · 사전 `exclude` 칸 — `spec.lexicon-link`(task 514)와 같은 선. 「기름 뿔을 취하여」가 일반 「기름」(액체)에 크기를 요구했다. 시험 `PropSizeRelative.test_specific_entry_wins`.
- 인용 대조(`check_cast_v2.BOOK`)에 스가랴 「슥」(38)이 없어 「슥 8:4」 인용을 사무엘상으로 읽었다 — 한 줄 더함.

## 시도 2 — 규칙 재검

`spec_failures('authored-samuel-bethlehem-david-anointing')` → `{}` · `derive_scene --check --figures whole` 통과(512토큰 안 — 처음 538토큰이라 몸짓·관계 문구의 겹침을 줄임). 전 규칙 통과 명세 13 → 14/40, 다른 명세 회귀 없음.

가이드 눈 확인(`samples/bethlehem-step23/guide-1.png` 뼈대 · `guide-2.png` 깊이): 사무엘 손목이 다윗 머리 위에 오고, 형 실루엣이 다윗 뒤에 일곱쯤, 이새는 오른쪽에 떨어져 섰다.

## 단계 ③ 문항 등급 (단계 ①에서 미리 정함)

공통 문항(scene-authoring 단계 ③ 목록 — s.style · s.no-blob · t.no-halo · t.no-church · t.guard · t.body-natural · t.proportion · t.arms-natural · t.era-dress · t.hands-visible · t.arm-length · p.no-floating)에 더해:

| 문항 | 묻는 것 | 근거 | 등급 |
|---|---|---|---|
| t.old-prophet | 왼쪽에 흰 수염 늙은 남자가 서 있나 | 16:13 사무엘 · 8:1 늙음 | 거르기 |
| t.horn | 그 늙은 남자가 한 손에 짐승 뿔(병·항아리·나팔 아님)을 들었나 | 16:13 「기름 뿔을 취하여」 | 거르기 |
| t.pour-head | 뿔의 열린 입이 소년 머리 바로 위로 기울었나 | 16:13 「그에게 부었더니」 | 거르기 |
| t.oil | 뿔에서 금빛 기름이 소년 머리로 흘러내리나 | 16:13 「부었더니」 | 거르기 |
| t.one-pourer | 뿔·그릇을 든 사람이 늙은 선지자 한 사람뿐인가 | 16:13 「사무엘이 … 취하여」 | 거르기 |
| t.boy | 가운데 사람이 수염 없는 앳된 소년인가 | 16:11 말째 · 17:33 소년 | 거르기 |
| t.ruddy | 소년 얼굴빛이 불그스름한가 | 16:12 「그의 빛이 붉고」 | 거르기 |
| t.shepherd-dress | 소년이 수수한 무릎 길이 튜닉(왕 옷·갑옷 아님)인가 | 16:11 [추론] | 거르기 |
| t.brothers | 소년 뒤에 어른 남자가 여럿(다섯 이상) 서 있나 | 16:13 「그 형제 중에서」 · 16:10 일곱 | 거르기 |
| t.brothers-empty | 뒤의 남자들 손에 뿔·그릇이 없나 | 16:13(붓는 이는 사무엘뿐) | 거르기 |
| t.father | 오른쪽에 회색 수염 늙은 남자가 떨어져 서 있나 | [추론] 16:10-11 · 17:12 | 거르기 |
| t.outdoor | 야외 마을 빈터인가(방 안 아님) | 16:4-5 | 거르기 |
| t.altar | 뒤쪽에 돌 제단과 오르는 연기가 있나 | [추론] 16:2 · 16:5 | 거르기 |
| t.no-spirit | 하늘에서 내려오는 빛줄기·비둘기·날개 달린 형상이 없나 | 16:13 감동 — 형상 없음(ADR 261025-120741) | 거르기 |
| t.seven | 뒤의 남자가 일곱인가 | 16:10(수는 [직접]이나 겹침으로 셀 수 없음) | 기록 |
| t.bowed | 소년이 고개를 숙였나 | 저작 | 기록 |
| t.standing | 모두 서 있나(무릎 꿇음 없음) | 저작 | 기록 |
| t.jesse-staff | 오른쪽 늙은 남자가 지팡이를 쥐었나 | [추론] 슥 8:4 | 기록 |
