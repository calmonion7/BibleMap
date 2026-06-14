# 2026-06-14 — Book SidePanel + 검색 통합 + 인물 성품 표시 (파트 3/4)

## 계획 vs 실제
- 계획대로 진행된 것: Book SidePanel 뷰, topPersons/topEvents API, Person traits 주입·표시, theme.js Book 타입 추가.
- 편차:
  - S1(Book 검색): 코드 변경 없이 이미 작동 → 긍정적 발산.
  - 외부 성경 API(api.getbible.net/v2/kor) 실패 → 구절 참조 텍스트 표시 fallback으로 처리.
  - neighborTotal에서 "그래프 뷰에서 전체 탐색" 문구 제거 (GraphView 삭제 정리).

## 학습
- getbible.net 한국어 API(/v2/kor)는 신뢰성이 낮음. 외부 성경 텍스트 API 사용 시 fallback 필수.

## 문서 업데이트
- CONTEXT.md 승급: 없음
- ADR 추가: 없음
