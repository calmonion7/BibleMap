"""성경 66권 enriched 컨텍스트 생성 레시피.
ADR-0006: 실제 데이터는 LLM이 직접 생성하므로 이 스크립트는 재생성 참고용.
필드: author, writtenDate, verseCount, keyPeople, centralMessage, structure
주입: inject_book_context.py로 Neo4j에 SET."""

import json
import os

BOOKS_JSON = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../data/book_context/books.json'))

# 재생성 시: Anthropic API 또는 Claude Code로 위 66권 각각에 대해
# author(저자), writtenDate(기록연대), verseCount(절수),
# keyPeople(핵심인물3~5), centralMessage(중심메시지1문장), structure(구조개요)
# 를 한국어로 생성한 뒤 books.json에 병합하고 inject_book_context.py를 실행.

if __name__ == '__main__':
    with open(BOOKS_JSON) as f:
        data = json.load(f)
    print(f'현재 {len(data)}권 로드됨')
    sample = next(iter(data.values()))
    print('필드:', list(sample.keys()))
