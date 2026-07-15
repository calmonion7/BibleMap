"""data/god_reliance/*.json이 AUTHORING.md 규칙을 지키는지 기계검증한다.

검사: ① mode가 통제어휘 5종 안 ② trigger.verse·outcome.verse 각각 정본 사전
(bible/verses.json)에서 해석됨 ③ obeyed는 mode=="부르심"일 때만 불리언으로 존재
④ approxYear 정수 ⑤ trigger.label·outcome.label 결손 ⑥ kind는 물음 계열(물음-응답·
물음-침묵) outcome에만 5값 통제어휘 ⑦ 구 스키마(최상위 verse/label) 잔존.
위반이 있으면 목록 출력 + 종료 코드 1. 인물별 항목 수와 표본적음(<6) 목록도 보고.
"""
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
GOD_DIR = DATA / "god_reliance"

MODES = {"물음-응답", "물음-침묵", "독단-개입", "독단-어긋남", "부르심"}
ASK_MODES = {"물음-응답", "물음-침묵"}
KINDS = {"이룸", "더하심", "다르게", "거절", "침묵"}
LOW_SAMPLE = 6
_REF_HEAD = re.compile(r"^(\S+)\s+(\d+):(\d+)")


def _build_resolver():
    books = json.loads((DATA / "names_ko" / "books.json").read_text())
    verses = json.loads((DATA / "bible" / "verses.json").read_text())
    alias2bb = {}
    for i, (_, v) in enumerate(books.items(), 1):
        for a in v.get("alias", []):
            alias2bb[a] = i
        alias2bb[v["ko"]] = i

    def resolve(ref: str):
        m = _REF_HEAD.match((ref or "").strip())
        if not m:
            return None
        book, ch, vs = m.group(1), int(m.group(2)), int(m.group(3))
        bb = alias2bb.get(book)
        if not bb:
            return None
        vid = f"{bb:02d}{ch:03d}{vs:03d}"
        return vid if vid in verses else None

    return resolve


def main():
    resolve = _build_resolver()
    files = sorted(GOD_DIR.glob("*.json"))
    if not files:
        sys.exit(f"[validate_god_reliance] {GOD_DIR}에 인물 파일이 없음")

    errors = []
    counts = {}
    for fp in files:
        slug = fp.stem
        try:
            entries = json.loads(fp.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{slug}: JSON 파싱 실패 — {e}")
            continue
        if not isinstance(entries, list):
            errors.append(f"{slug}: 최상위가 배열이 아님")
            continue
        counts[slug] = len(entries)
        for i, e in enumerate(entries):
            tag = f"{slug}[{i}]"
            mode = e.get("mode")
            if mode not in MODES:
                errors.append(f"{tag}: 어휘 밖 mode '{mode}'")
            if not isinstance(e.get("approxYear"), int):
                errors.append(f"{tag}: approxYear 정수 아님 '{e.get('approxYear')}'")
            if "verse" in e or "label" in e:
                errors.append(f"{tag}: 구 스키마 최상위 verse/label 잔존")
            for seg in ("trigger", "outcome"):
                s = e.get(seg)
                if not isinstance(s, dict):
                    errors.append(f"{tag}: {seg} 객체 결손")
                    continue
                if not (s.get("label") and isinstance(s["label"], str)):
                    errors.append(f"{tag}: {seg}.label 결손")
                if not resolve(s.get("verse", "")):
                    errors.append(f"{tag}: {seg}.verse 해석 실패 '{s.get('verse')}'")
            out = e.get("outcome") if isinstance(e.get("outcome"), dict) else {}
            if mode in ASK_MODES:
                if out.get("kind") not in KINDS:
                    errors.append(f"{tag}: 물음 계열 outcome.kind 5값 아님 '{out.get('kind')}'")
            elif "kind" in out:
                errors.append(f"{tag}: kind는 물음 계열 outcome에만 허용")
            has_obeyed = "obeyed" in e
            if mode == "부르심":
                if not isinstance(e.get("obeyed"), bool):
                    errors.append(f"{tag}: 부르심인데 obeyed 불리언 없음")
            elif has_obeyed:
                errors.append(f"{tag}: obeyed는 부르심에만 허용")

    if errors:
        print(f"[validate_god_reliance] 위반 {len(errors)}건:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    total = sum(counts.values())
    low = sorted(s for s, n in counts.items() if n < LOW_SAMPLE)
    print(f"[validate_god_reliance] OK — 인물 {len(files)}명 · 항목 {total}개 · 위반 0")
    print(f"  표본적음(<{LOW_SAMPLE}) {len(low)}명: {low}")


if __name__ == "__main__":
    main()
