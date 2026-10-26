# 2026-10-25 — 기브아 창 사람 키쯤(1.0) · 날아간 자리 4분의 3 · 수금 기준표 크기 (task 411, fg-loop 일괄 승급)

## Plan vs actual
- What went as planned: 사전 창 길이 근거(「단창」 19:9·19:10·20:33·22:6 · 삼하 1:6 · 26:7) · 문항 o0j가 거절 그림 2/2를 잡음 · m16e 통과 1/8 → 사람 화면.
- Divergences:
  - recheck.flight_errors가 창 길이를 「사전 비 × 사울 구역 키」로 셈해 키 등급(tall 1.205)을 안 나눔 — 합성(paste_step)은 나눔. 1.0 창이 어느 자리에도 안 들어가 처음 드러남(옛 0.67에서도 1.2배 길게 잼).
  - 계획 「넣기 상자를 기준표 크기로」는 헛짚음 — 상자는 이미 충분히 컸고 klein이 작게 그렸음. 크기는 지시 문구(크롭 안 머리에 견줌)가 움직임.
  - m16 바탕은 m15와 문구·가이드 바이트가 같아 다시 그리지 않음(GPU 0).

## Learnings
- Do differently next time:
  - 같은 크기를 두 곳(검사·생성)에서 셈하면 한 함수(기준표)에서 — 하나만 고치면 다른 쪽이 조용히 어긋남.
  - 명세 칸을 고친 뒤 바탕을 다시 그리기 전에 바탕 문구·가이드 바이트를 m 이전 시도와 대조 — 같으면 편집만 다시.
  - 크기 결함이면 상자·칠하기보다 「크롭 안에 보이는 부위에 견준 크기 문구」부터(PROMPTING 29).

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none
- 기타: 시험 FlightPosition.test_butt_divides_by_height_class · held_target/held_head_en 시험(실행 중 추가) · PROMPTING 29(쥔 지물 넣기 편집)
