# task#322 승인본 — 보완 ①(던지는 동작)·②(뿔투구)

**2026-08-30 사용자 승인**: ① 다윗이 물맷돌을 던지는 동작 · ② 골리앗 뿔투구 — **승인**.
③ 두 인물이 서로 보기 — **반려**(세 장 모두 정면).

생성 조합: `--cn 0.6 --bg-ip 0.0 --fig-cn 0.8 --ip 0.7 --ref-band 0.30`, 콘티는 커밋 `be7c8c0`
(다윗 팔 = 닫힌 사지 윤곽). 판정 기록 `notes/final-verdict-r6-conti2-sip07-rb030.json` —
두 장 모두 일곱 축 전부 통과.

**왜 여기 있나**: `gen_final.py`의 산출물 이름이 (cn, bg_ip, fig_cn, sip, ref_band)만 담고
**콘티 판본을 담지 않는다.** 그래서 콘티를 고친 뒤 같은 조합으로 돌리면 승인본을 덮어쓴다 —
이번 태스크에서만 두 번 났고, `.forge/reports/`는 gitignore라 복구도 안 된다. 화소를 여기에
고정한다.

**`reference/` 바로 아래가 아니라 하위 디렉터리인 이유**: `judge_style.reference_paths()`가
`reference/*.png` 전부를 「정답지 = ControlNet 조건화 없는 화풍 기준」으로 읽는다(비재귀).
바로 아래 두면 콘티 CN으로 뽑은 이 그림들이 정답지로 오분류돼 축 A·C를 오염시킨다 —
`arm-negatives/`가 그 실제 사고의 기록이다.
