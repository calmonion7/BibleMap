# 2026-06-15 — 타임라인 성경 66권 시대순 마커 + 추정연도 + 클릭 레이어

## Plan vs actual
- What went as planned: S1~S4 전부 계획대로. `/books` 엔드포인트(정확35·추정31), TimelineView 책 마커 시대순 머지, "추정" 점선/배지, 클릭→기존 SidePanel Book 오버레이. :8080 UAT 통과(chronological=true, 로마서 클릭→Book 패널, 콘솔 에러 0).
- Divergences: 경미. 추정연도 파일 경로를 `DATA_DIR`(기본 `/app/data`)로 해석(컨테이너 마운트 맞춤), 데이터 JSON에 `nameKo` 추가, bookFilter 시 책 마커도 동일 범위필터, 책 색은 SidePanel Book 계열(#a78bfa).

## Learnings
- Do differently next time:
  - **데이터 오버레이 패턴(결정·근거 보존)**: 추정연도(book_years_approx)는 기존 보조데이터 관례("data/→inject script→Neo4j 속성")와 달리 **Neo4j에 넣지 않고 `/books` 엔드포인트가 런타임에 JSON 오버레이**한다. 이유 — (1) 추정(권위 낮은) 데이터를 권위 그래프와 분리, (2) 마이그레이션/배포 시 inject 스텝 불필요, (3) 마운트(`./data:/app/data`)라 데이터만 고치면 재빌드 없이 반영. **앞으로 이 불일치를 "고치려" Neo4j로 옮기지 말 것 — 의도된 분리임.** (ADR로 올리진 않음: 되돌리기 난이도 낮아 3요건 미충족.)
  - **deep-research → plan fold-in 흐름**: fg-ask 단계에서 추정연대를 deep-research(24출처/25주장 적대검증)로 다진 뒤 결과 표를 plan에 직접 박고, fg-run은 그 표를 그대로 데이터파일로 직렬화. 재리서치 없이 깔끔히 실행됨 — 외부 지식이 필요한 데이터 생성 작업의 좋은 패턴.
  - **추정 정확도 한계**: 야고보서(리서치 양 후보 모두 적대검증 기각), 잠언(직접 검증된 주장 없음)이 특히 약함. UI "추정" 마커로 면책하되, 향후 연대 보정 시 이 둘 우선 재검토.
  - 검증은 dist 빌드 + api 재빌드 후 nginx :8080(API 동일출처)에서 — dev :5173은 API 미노출.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none (오버레이 패턴은 retro 로그에 근거 보존 — ADR 3요건 중 '되돌리기 어려움' 미충족)
