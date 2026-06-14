"""Claude API로 주요 인물별 성품(character traits)을 생성해 JSON으로 저장한다.

출력: data/character_traits/people.json
  {
    "<theographic_id>": {
      "traits": [
        {"trait": "믿음", "verse_ref": "창 15:6", "description": "..."}
      ]
    }
  }

사용법:
  ANTHROPIC_API_KEY=sk-... python3 generate_person_traits.py [--top N]
"""
import argparse
import json
import os
import time
import urllib.request

import anthropic

PEOPLE_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json"
EVENTS_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/events.json"

SCRIPT_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "character_traits", "people.json")
)
NAMES_KO_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "names_ko", "people.json")
)


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


PROMPT_TEMPLATE = """성경 인물 {name_ko}({name_en})의 성품을 아래 JSON 형식으로 정확히 응답하시오.

{{
  "traits": [
    {{"trait": "성품키워드", "verse_ref": "성경구절 참조", "description": "한 문장 설명"}}
  ]
}}

조건:
- traits: 3-5개의 성품 키워드 (한국어, 예: 믿음, 순종, 겸손, 지혜)
- verse_ref: 해당 성품을 잘 보여주는 구절 참조 (한국어 약어, 예: 창 22:12)
- description: 해당 성품이 드러나는 장면/행동 한 문장 (한국어)
- JSON 외 다른 텍스트 없이 순수 JSON만 출력
"""


def generate_traits(client, name_en, name_ko):
    prompt = PROMPT_TEMPLATE.format(name_en=name_en, name_ko=name_ko)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=100, help="이벤트 참여 횟수 상위 N명")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")

    people = fetch_json(PEOPLE_URL)
    events = fetch_json(EVENTS_URL)

    published = [p for p in people if p.get("fields", {}).get("status", "publish") == "publish"]

    # 이벤트 참여 횟수 집계
    participant_count = {}
    for e in events:
        for pid in e.get("fields", {}).get("participants", []):
            participant_count[pid] = participant_count.get(pid, 0) + 1

    published.sort(key=lambda p: -participant_count.get(p["id"], 0))
    top_people = published[: args.top]
    print(f"Processing top {len(top_people)} people by event count")

    with open(NAMES_KO_PATH, encoding="utf-8") as f:
        names_ko_map = json.load(f)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            result = json.load(f)
    else:
        result = {}

    client = anthropic.Anthropic(api_key=api_key)

    for p in top_people:
        tid = p["id"]
        if tid in result:
            print(f"  SKIP {p['fields'].get('displayTitle', tid)}")
            continue
        name_en = p["fields"].get("displayTitle", "")
        name_ko = names_ko_map.get(tid, {}).get("ko", name_en)
        print(f"  Generating {name_ko} ({name_en}) ...")
        try:
            ctx = generate_traits(client, name_en, name_ko)
            result[tid] = ctx
        except Exception as e:
            print(f"  ERROR {name_en}: {e}")
            result[tid] = {"traits": []}
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        time.sleep(0.3)

    print(f"\nDone. {len(result)} people written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
