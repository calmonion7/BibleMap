# 데이터 생성: generate 스크립트는 레시피 아티팩트, 실제 데이터는 LLM이 직접 생성

이 환경에는 `ANTHROPIC_API_KEY`가 `.env`에 없고, host Python에도 `anthropic` SDK가 기본 설치되지 않는다. generate 스크립트(`generate_book_events.py`, `generate_verse_events.py` 등)는 **재생성 레시피 아티팩트**로 커밋하고, 실제 커밋되는 JSON 데이터는 Opus가 theographic JSON 등 실제 데이터를 참조해 직접 생성한다.

**이렇게 결정한 이유**: API 키 없이 스크립트를 실행할 수 없는 상황이 task 47·48·51에서 세 번 반복됐다. 스크립트 실행을 전제로 계획을 짜면 매번 동일한 발산이 발생하므로, 계획 단계부터 "LLM 직접 생성"을 기본 경로로 설정하는 것이 맞다.

**트레이드오프**: 스크립트 실행 방식은 재현 가능하고 자동화가 쉽지만 API 키가 필요하다. LLM 직접 생성 방식은 환경 제약 없이 즉시 실행 가능하지만, 같은 스크립트를 재실행하면 LLM이 다른 결과를 낼 수 있다(추정 데이터는 허용 범위, 고정 데이터는 커밋으로 고정).

**앞으로 계획할 때**: generate 스크립트 실행 슬라이스를 "LLM이 theographic JSON / Neo4j 실제 데이터를 조회해 JSON 직접 생성"으로 처음부터 기술할 것.
