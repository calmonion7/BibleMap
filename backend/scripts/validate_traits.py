"""data/character_traits/people.json이 AUTHORING.md의 분류 규칙을 지키는지 기계검증한다.

검사: ① 라벨이 통제 어휘 안 ② 인물당 2~5개·라벨 중복 없음 ③ verse_ref 형식 ④ 필드 결손.
위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(__file__)
TRAITS_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", "character_traits", "people.json"))

# AUTHORING.md §3 통제 어휘 — 문서와 함께 갱신할 것
VIRTUES = {
    "믿음", "순종", "겸손", "용기", "인내", "지혜", "긍휼", "사랑", "충성", "정직", "신실", "온유",
    "절제", "헌신", "경건", "감사", "용서", "환대", "공의", "근면", "순결", "담대함", "분별", "통회",
}
FLAWS = {"교만", "시기", "기만", "우유부단", "불순종", "분노", "탐욕", "비겁"}
VOCAB = VIRTUES | FLAWS

# 개역 약어 + 장:절[-절[:절]] (예: "창 32:26", "창 18:2-5", "시 51:3-4")
REF_RE = re.compile(r"^[가-힣]{1,4}(?:[전후상하]|[0-9])?\s\d+:\d+(?:-\d+(?::\d+)?)?$")


def main():
    with open(TRAITS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    errors = []
    for pid, p in data.items():
        traits = p.get("traits") or []
        if not (2 <= len(traits) <= 5):
            errors.append(f"{pid}: 성품 {len(traits)}개 (허용 2~5)")
        labels = [t.get("trait") for t in traits]
        for lbl in labels:
            if lbl not in VOCAB:
                errors.append(f"{pid}: 어휘 밖 라벨 '{lbl}'")
        if len(labels) != len(set(labels)):
            errors.append(f"{pid}: 라벨 중복 {labels}")
        for t in traits:
            ref = t.get("verse_ref") or ""
            if not REF_RE.match(ref):
                errors.append(f"{pid}: verse_ref 형식 위반 '{ref}'")
            if not (t.get("trait") and t.get("description")):
                errors.append(f"{pid}: 필드 결손 {t.get('trait')}")

    if errors:
        print(f"[validate_traits] 위반 {len(errors)}건:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    n = sum(len(p.get("traits") or []) for p in data.values())
    print(f"[validate_traits] OK — 인물 {len(data)}명 · 성품 {n}개 · 위반 0")


if __name__ == "__main__":
    main()
