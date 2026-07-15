"""전체 성경 구절↔인물 색인 정본(data/verse_persons/index.json) 산출.

theographic verses.json은 각 절 레코드에 `verseID`(우리 정본 사전 bible/verses.json의
키 규약 BBCCCVVV와 동일)와 `people`(그 절에 등장/언급되는 인물 rec id 배열)을 직접
보유한다. 따라서 별도 id 매핑·역변환 없이 `{verseID: [personRecId, ...]}` 색인을
그대로 뽑아낸다(저작 아님 — 원본 로드+투영).

- rec id는 우리 Neo4j Person 노드의 theographic_id와 같은 키다(우리가 적재하지 않은
  인물 rec id도 그대로 담고, 이름 해석은 조회 시점에 우리 노드에 있는 것만).
- theographic는 "하나님(God)"도 people로 다루므로 색인에 포함된다.

실행(Neo4j 불필요, 네트워크 fetch 필요):
    python backend/scripts/build_verse_persons.py
"""
import json
import urllib.request
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
URL = "https://raw.githubusercontent.com/robertrouse/theographic-bible-metadata/master/json/verses.json"


def main():
    with urllib.request.urlopen(URL) as resp:
        raw = json.load(resp)
    recs = raw if isinstance(raw, list) else list(raw.values())[0]

    index = {}
    no_id = 0
    empty = 0
    for r in recs:
        f = r.get("fields", {})
        vid = f.get("verseID")
        if not vid:
            no_id += 1
            continue
        people = f.get("people") or []
        if not people:
            empty += 1
            continue
        index[vid] = people

    out_dir = DATA / "verse_persons"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=0) + "\n")

    postings = sum(len(v) for v in index.values())
    dist = Counter(len(v) for v in index.values())
    print(
        f"verse_persons/index.json written: {len(index)} verses with persons, "
        f"{postings} verse-person links (verseID 없음 {no_id}, 인물 없는 절 {empty})"
    )
    print(f"인물 수 분포(상위): {dict(sorted(dist.items())[:5])} ...")


if __name__ == "__main__":
    main()
