"""Claude API로 각 성경 권별 시대적 배경·주제·대표 구절을 생성해 JSON으로 저장한다.

출력: data/book_context/books.json
  {
    "<theographic_id>": {
      "background": "...",
      "themes": ["...", "..."],
      "keyVerse": "창 1:1"
    }
  }

사용법:
  ANTHROPIC_API_KEY=sk-... NEO4J_PASSWORD=... python3 generate_book_context.py
"""
import json
import os
import time
import urllib.request

import anthropic

BOOKS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/books.json"

SCRIPT_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "book_context", "books.json")
)
NAMES_KO_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "names_ko", "books.json")
)


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


PROMPT_TEMPLATE = """성경 {name_ko}({name_en})에 대해 아래 JSON 형식으로 정확히 응답하시오.

{{
  "background": "2-3문장의 시대적·역사적·신학적 배경 (한국어)",
  "themes": ["주제1", "주제2"],
  "keyVerse": "성경 약어 장:절 (예: 창 1:1)"
}}

조건:
- background: 저술 시기, 주요 사건, 신학적 의의를 포함한 2-3문장
- themes: 책의 핵심 주제 키워드 2-3개 (간결하게)
- keyVerse: 이 책을 대표하는 단일 구절 참조 코드 (한국어 약어 사용)
- JSON 외 다른 텍스트 없이 순수 JSON만 출력
"""


def generate_context(client, book_id, name_en, name_ko):
    prompt = PROMPT_TEMPLATE.format(name_en=name_en, name_ko=name_ko)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # strip markdown code fence if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")

    books = fetch_json(BOOKS_URL)
    with open(NAMES_KO_PATH, encoding="utf-8") as f:
        names_ko_map = json.load(f)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # 기존 결과 로드 (재실행 시 스킵)
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            result = json.load(f)
    else:
        result = {}

    client = anthropic.Anthropic(api_key=api_key)

    for b in books:
        tid = b["id"]
        if tid in result:
            print(f"  SKIP {b['fields']['bookName']} (already generated)")
            continue
        name_en = b["fields"]["bookName"]
        name_ko = names_ko_map.get(tid, {}).get("ko", name_en)
        print(f"  Generating {name_ko} ({name_en}) ...")
        try:
            ctx = generate_context(client, tid, name_en, name_ko)
            result[tid] = ctx
        except Exception as e:
            print(f"  ERROR {name_en}: {e}")
            result[tid] = {"background": "", "themes": [], "keyVerse": ""}
        # 중간 저장
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        time.sleep(0.3)  # rate limit 여유

    print(f"\nDone. {len(result)} books written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
