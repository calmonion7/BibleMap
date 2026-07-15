# 2026-07-15 — 전체 성경 구절↔단어 역색인 정본 산출 (task 178, part 1/4)

## Plan vs actual
- What went as planned: 기존 build_word_distribution의 STOPWORDS·NNG/NNP·len>=2 토큰화 규약을 import 재사용해 `data/word_verse_index/index.json`(7,918단어·133,537포스팅·31,084절) 산출, `overlays.word_verse_index()` 로더 추가, 스팟체크(사랑·믿음·하나님·기도 각 50절 100% stem 포함) 통과. 기존 substring 엔드포인트 무변경.
- Divergences: 없음 수준. 단일 파일(샤딩 대신, 1.7MB) 채택, 색인은 MIN_COUNT 미적용(1회 등장도 조회돼야 함 — 집계용 word_distribution과 의도적 차이).

## Learnings
- Do differently next time: 특이사항 없음. kiwipiepy는 `/tmp/kiwi-venv` 별도 venv 필요(build_word_distribution 도큐스트링 규약 동일) — 재실행 시 venv부터.

## Doc updates
- CONTEXT.md promotion: none (데이터 인프라 — 도메인 용어 아님)
- ADR added: none
