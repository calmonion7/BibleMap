# 2026-07-11 — 구절 근거 없는 verse-event 20건에 고아 구절 앵커 연결 (task#160)

## Plan vs actual

- **What went as planned:**
  - DoD 전부 충족: verse-event 20건이 `/event/{id}/verses`에서 non-empty·올바른 책·범위⊆고아·bake textKo/En null 0(신규 775절 전부). 4건 본문 성경 대조 일치, 에스더 사건 Playwright 모달(2:1–18) 렌더 확인.
  - 방향 B(고아 앵커) 그대로. 6개 책 중 5개는 전 절이 고아라 범위⊆고아 자동 충족(역대상만 940/942).
  - 소스 오브 트루스 이원화 유지: `verse_events/events.json`에 저작 verses/rangeLabel(내구 원천), `event_verses/events.json`에 병합(앱이 읽는 오버레이). rangeLabel은 `generate_event_verses.py`의 `build_range_label` 재사용 → 기존 777건과 동일 규약.
  - S2 저작 품질 높음: 6개 병렬 에이전트가 정교한 단락 경계(룻 성문 3:1–4:12 / 오벳 4:13–22 분할, 역대상 궤운반이 14장 제외 13+15~16장, 에스더 와스디 1:9–22로 1:1-8 배경 제외, 계 밧모 1:9–20·새예루살렘 21:1–22:5로 서문·에필로그 제외).

- **Divergences:**
  - **하이브리드 실행.** 진짜 병렬 창작인 S2(저작)만 Dynamic Workflow(6개 책 병렬, eco sonnet 캡)로, S1(고아계산)·S3(병합)·S4(베이크)·S5(검증)는 결정적·정확성 critical이라 메인 세션 직접 실행. eco/단순성 + regen 병합 직접통제 필요에 근거. fg-run의 "scout inline first, fan out where it helps"에 부합.
  - **[중대] regen이 신규 20건이 아니라 authored 327건까지 파괴함을 발견.** 커밋 오버레이 777키 = theographic 450 + authored 327(ADR-0005/0008 큐레이션) + (신규)20. `generate_event_verses.py` 전체덮어쓰기 regen은 authored 327건을 조용히 소실시키던 **사전 잠복 함정**(theographic 드리프트 아님 — 원천 실제 450건). 계획의 regen-safety 우려("theographic 재빌드가 20건 덮어씀")보다 범위가 넓었음.
  - **대응 범위 확장:** verse-event 전용 훅 대신 `preserve_non_theographic(result, theo_ids)`로 비-theographic 엔트리 전체(authored 327 + verse-event 20)를 텍스트째 보존. DoD와 사전 함정 동시 해결(feedback_fix_adjacent_bugs).
  - 첫 훅이 정의만 되고 `main()` 호출 누락 → regen이 여전히 450키·20건 유실. regen-safety 테스트(백업→regen→assert→복원)가 이 버그를 잡음.
  - rangeLabel: 에이전트 프리뷰("3:1–4:12")와 정규 `build_range_label`("3:1–18, 4:1–12")이 다름 → 저장/표시는 기존 777건 규약과 통일된 정규형 사용(정확성 문제 아님).
  - 기존 777건 textKo null 24개는 getbible 한글 사전 공백(HEAD에도 존재), Non-goals라 미변경.

## Learnings

- **Do differently next time:**
  - **누적 다중소스 아티팩트의 "재빌드" 스크립트는 먼저 그 파일의 실제 구성을 측정하고 다뤄라.** event_verses 오버레이는 theographic + authored + verse-event가 시간에 걸쳐 누적된 파일인데, `generate_event_verses.py`는 theographic만으로 전체를 재빌드·덮어쓴다 → 다른 소스를 조용히 소실. 이는 theographic-chronology 회고의 `load_books.py` 재fetch 함정과 **동형**: "원천에서 재빌드"하는 스크립트를 누적 아티팩트에 돌리기 전, **그 스크립트가 읽는 것 vs 파일이 누적한 것**을 대조하라. 계획에서 "신규 N개만 보존"으로 안전범위를 좁히지 말고 전체 구성을 먼저 재라.
  - **파괴적 검증 테스트는 백업→실행→assert→복원으로 감싸라.** regen-safety 테스트를 그렇게 감쌌기에, "훅 정의만 하고 호출 배선 누락"이라는 내 버그가 실피해 0으로 잡혔다. 그리고 regen-safety는 "훅 걸었으니 됐겠지"로 넘기지 말고 **실제로 재빌드를 돌려 키 수·엔트리 생존을 확인**해야 함.
  - **저작 에이전트의 라벨 프리뷰를 저장하지 말고 recipe 아티팩트의 라벨 함수를 재사용하라.** 에이전트는 사람용 프리뷰를 주지만, 저장·표시 라벨은 `build_range_label`로 생성해 기존 데이터 규약(장 경계 분절)과 일치시켜야 함.
  - **고아 집합이 큰 책(역대상 940·느헤미야 406·계 404)은 책 단위 병렬 저작이 정답.** 한 컨텍스트에 6책(총 ~2,282절 영문)을 넣으면 희석. 책별 팬아웃 + sonnet(eco)이 정교한 pericope 경계까지 처리. 규모 실측(S1)으로 팬아웃 형태를 확정한 뒤 워크플로우를 짠 것이 유효.
  - **하이브리드 실행이 데이터 태스크에 맞는다.** 슬라이스 중 진짜 병렬 창작만 워크플로우로, 결정적·정확성 critical(특히 회고가 경고한 병합류)은 직접. 전 슬라이스를 서브에이전트에 위임하는 것보다 싸고 안전.

## Doc updates
- CONTEXT.md promotion: none (새 도메인 용어 없음 — 고아 구절·verse-event 근거는 fg-ask에서 이미 정제됨)
- ADR added: none (regen 함정은 사실상 버그 픽스라 ADR 3조건 미달; 동형 `load_books.py` 함정도 회고로만 기록된 선례와 일치. 회고 "Do differently"가 다음 fg-ask/fg-run이 읽는 연료)
