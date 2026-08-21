"""Claude API로 큐레이션 35인 인물의 소개(person context)를 생성해 JSON으로 저장한다.

실제 소개 데이터는 data/person_context/people.json에 저작되어 있으며(data/person_context/
AUTHORING.md 저작 규칙 준수), 이 스크립트는 API 키가 있을 때 그 데이터를 재생성(regeneration)하는
경로다.

출력: data/person_context/people.json
  {
    "<theographic_id>": {
      "role": "믿음의 조상",
      "intro": "...",
      "verses": [{"ref": "창 15:6"}, ...]
    }
  }

사용법:
  ANTHROPIC_API_KEY=sk-... python3 generate_person_context.py
"""
import glob
import json
import os
import time
import urllib.request

import anthropic

PEOPLE_URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/people.json"

SCRIPT_DIR = os.path.dirname(__file__)
PERSON_EVENTS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", "person_events"))
OUTPUT_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "person_context", "people.json")
)
NAMES_KO_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "data", "names_ko", "people.json")
)


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


PROMPT_TEMPLATE = """성경 인물 {name_ko}({name_en})을 아래 JSON 형식으로 정확히 응답하시오.

{{
  "role": "짧은 명사구 (예: 믿음의 조상)",
  "intro": "2-3문장 소개 (한국어)",
  "verses": ["성경 약어 장:절", ...]
}}

조건:
- role: 이 인물을 한마디로 규정하는 짧은 명사구, 8자 내외
- intro: 2-3문장, 300자 이하. 근거 구절에 뿌리를 둔 사실 서술만 담고 교리적 해석은 피함(교리 중립)
- verses: intro의 근거가 되는 구절 참조 목록(개역 약어), 최소 1개. verses[0]이 가장 대표적인 구절
- JSON 외 다른 텍스트 없이 순수 JSON만 출력
"""


def generate_context(client, name_en, name_ko):
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
    data = json.loads(text.strip())
    return {
        "role": data["role"],
        "intro": data["intro"],
        "verses": [{"ref": ref} for ref in data["verses"]],
    }


def build_roster():
    """data/person_events/*.json 각 파일의 events[0].participants[0]을 theographic_id로 삼는다
    (curated.py CURATED의 35 slug와 동일 집합 — task#278에 persons.py에서 이관)."""
    roster = []
    for path in sorted(glob.glob(os.path.join(PERSON_EVENTS_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            events = json.load(f)
        roster.append(events[0]["participants"][0])
    return roster


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")

    roster = build_roster()
    print(f"Processing {len(roster)} curated people")

    with open(NAMES_KO_PATH, encoding="utf-8") as f:
        names_ko_map = json.load(f)
    people = fetch_json(PEOPLE_URL)
    name_en_map = {p["id"]: p["fields"].get("displayTitle", "") for p in people}

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            result = json.load(f)
    else:
        result = {}

    client = anthropic.Anthropic(api_key=api_key)

    for tid in roster:
        name_en = name_en_map.get(tid, "")
        name_ko = names_ko_map.get(tid, {}).get("ko", name_en)
        if tid in result:
            print(f"  SKIP {name_ko}")
            continue
        print(f"  Generating {name_ko} ({name_en}) ...")
        try:
            result[tid] = generate_context(client, name_en, name_ko)
        except Exception as e:
            print(f"  ERROR {name_en}: {e}")
            result[tid] = {"role": "", "intro": "", "verses": []}
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        time.sleep(0.3)

    print(f"\nDone. {len(result)} people written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
