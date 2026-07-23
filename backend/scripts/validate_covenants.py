"""언약 정본(data/covenants/covenants.json)을 기계 검증한다 (task#247 S1).

검증 항목:
  a) 언약 수 5~6건
  b) keyVerseId 전수 실존 — 정본 절 사전(data/bible/verses.json) 대조
  c) startDate 파싱 가능(int 변환 가능한 문자열)
"""
import json
import os

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def main():
    verses = json.load(open(os.path.join(_DATA, "bible", "verses.json"), encoding="utf-8"))
    covenants = json.load(open(os.path.join(_DATA, "covenants", "covenants.json"), encoding="utf-8"))["covenants"]

    assert 5 <= len(covenants) <= 6, f"언약 수 위반: {len(covenants)}건"

    for c in covenants:
        tag = c.get("id")
        for vid in c["keyVerseIds"]:
            assert vid in verses, f"{tag}: keyVerseId 미실존 {vid}"
        int(c["startDate"])  # 파싱 실패 시 ValueError로 실패

    print(f"검사: {len(covenants)}건 언약, keyVerseId 전수 실존, startDate 전수 파싱 가능")
    print("PASS — 탈락 0")


if __name__ == "__main__":
    main()
