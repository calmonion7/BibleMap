"""data/person_context/people.json이 인물 소개 DoD를 지키는지 기계검증한다.

2단 품질 계층(ADR-0027): 서사 인물은 role+intro+verses, 족보 단역은 intro 없이 role 한줄+verses.
검사: ① 인물 수 최소 86 ② role 비어있지 않음(80자 이하)·intro는 있으면 300자 이하 ③ verses 1개 이상
④ verse_ref 형식(validate_traits.py REF_RE 재사용) ⑤ textKo·textEn 프리베이크(null 아님).
위반이 있으면 목록을 출력하고 종료 코드 1.
"""
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(__file__)
PEOPLE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", "person_context", "people.json"))

MIN_COUNT = 86

# 개역 약어 + 장:절[-절[:절]] (예: "창 32:26", "창 18:2-5", "시 51:3-4")
REF_RE = re.compile(r"^[가-힣]{1,4}(?:[전후상하]|[0-9])?\s\d+:\d+(?:-\d+(?::\d+)?)?$")


def main():
    with open(PEOPLE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    errors = []
    if len(data) < MIN_COUNT:
        errors.append(f"인물 수 {len(data)}명 (최소 {MIN_COUNT})")

    for pid, p in data.items():
        role = p.get("role")
        if not (isinstance(role, str) and role):
            errors.append(f"{pid}: role 비어있음")
        elif len(role) > 80:
            errors.append(f"{pid}: role 길이 {len(role)} (허용 ≤80)")

        # 2단 계층(ADR-0027): intro는 서사 인물만 갖는다 — 있으면 규칙 검사, 없으면 족보 단역
        intro = p.get("intro")
        if intro is not None:
            if not (isinstance(intro, str) and intro):
                errors.append(f"{pid}: intro 비어있음")
            elif len(intro) > 300:
                errors.append(f"{pid}: intro 길이 {len(intro)} (허용 ≤300)")

        verses = p.get("verses")
        if not (isinstance(verses, list) and len(verses) >= 1):
            errors.append(f"{pid}: verses 비어있음")
            continue

        for v in verses:
            ref = v.get("ref") or ""
            if not REF_RE.match(ref):
                errors.append(f"{pid}: ref 형식 위반 '{ref}'")
            if v.get("textKo") is None:
                errors.append(f"{pid}: textKo null ({ref})")
            if v.get("textEn") is None:
                errors.append(f"{pid}: textEn null ({ref})")

    if errors:
        print(f"[validate_person_context] 위반 {len(errors)}건:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"[validate_person_context] OK — 인물 {len(data)}명 · 위반 0")


if __name__ == "__main__":
    main()
