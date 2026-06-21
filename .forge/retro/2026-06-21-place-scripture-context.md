# 2026-06-21 — 장소 구절 근거 콘텐츠 보강 (task 73)

## 계획 대비 실제
- **계획대로 (5슬라이스 전부)**: 좌표 43개 장소에 배경 산문 + 대표구절(한/영). LLM 직접 생성(병렬 5배치) → `generate_verse_text.py`에 `bake_place_context` 추가 프리베이크 → `inject_place_context.py` 신규 주입(43개) → `SidePanel.jsx` Place 전용 블록. book_context 파이프라인을 그대로 미러해 구조 리스크 0.
- **발산(모두 경미)**: 하란·우르 keyVerse 동일("창 11:31", 의도된 데이터); 일부 절 trailing space(getbible 원본, book_context와 동일 양상이라 보존); ruff 미설치 → py_compile 대체.

## 배운 것
- **다음에 다르게**: SidePanel의 접힘식 섹션(`collapsed[key] !== false`)은 기본 접힘이라 산문·절 본문·언어탭이 헤더 클릭 전엔 DOM에 없음. **Playwright로 본문/탭을 검증할 땐 헤더를 먼저 클릭해 펼친 뒤 확인할 것.** 언어탭 라벨은 'KO/EN'이 아니라 '한국어/영어'.
- 기존 표면(book_context)과 동일 패턴 작업은 미러가 가장 안전 — 새 ADR 불필요(저장 방식이 ADR-0004 원칙·book_context 선례를 그대로 따름).

## 문서 업데이트
- CONTEXT.md 승급: **"Place Context (장소 컨텍스트)"** 추가 (Book Context의 장소판 — context-specific 도메인 용어).
- ADR 추가: 없음 (저장 방식이 ADR-0004·book_context 선례 답습, 새 트레이드오프 아님).
