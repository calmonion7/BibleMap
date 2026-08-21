"""하나님 의존도 API — data/god_reliance/<slug>.json 정본을 서빙.

의존도 = (물음-응답 + 물음-침묵 + 순종한 부르심) ÷ 전체 × 100 (ADR-0023 정의 ii).
god_reliance는 slug 키, 인물 엔드포인트는 theographic_id 키 → person_events participants[0]로
id↔slug 매핑(journey.py와 동형). 구절 본문은 정본 사전에서 합성(구절 레이어 연결).
"""
import functools
import glob
import json
import os
import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..curated import CURATED, slug_to_id
from ..overlays import _resolve, _resolve_dir, bible_verses, books_ko

router = APIRouter()

# "물음"(응답 여부 무관) — 정의 ii의 분자. 부르심은 obeyed=true만 분자.
_ASK_MODES = ("물음-응답", "물음-침묵")
LOW_SAMPLE = 6
_REF_HEAD = re.compile(r"^(\S+)\s+(\d+):(\d+)")


@functools.lru_cache(maxsize=1)
def _alias_to_bb() -> dict:
    m = {}
    for i, (_, v) in enumerate(books_ko().items(), 1):
        for a in v.get("alias", []):
            m[a] = i
        m[v["ko"]] = i
    return m


def _resolve_verse(ref: str):
    mo = _REF_HEAD.match((ref or "").strip())
    if not mo:
        return None
    book, ch, vs = mo.group(1), int(mo.group(2)), int(mo.group(3))
    bb = _alias_to_bb().get(book)
    if not bb:
        return None
    return f"{bb:02d}{ch:03d}{vs:03d}"


@functools.lru_cache(maxsize=1)
def _slug_to_id() -> dict:
    """god_reliance 슬러그 → 인물 theographic_id. curated.slug_to_id()(35)를 god_reliance
    파일 존재로 제한해 파생한다 — 별도 person_events 순회 없음."""
    d = _resolve_dir("god_reliance")
    if not d:
        return {}
    present = {os.path.splitext(os.path.basename(fp))[0] for fp in glob.glob(os.path.join(d, "*.json"))}
    return {slug: pid for slug, pid in slug_to_id().items() if slug in present}


@functools.lru_cache(maxsize=1)
def _id_to_slug() -> dict:
    return {v: k for k, v in _slug_to_id().items()}


@functools.lru_cache(maxsize=None)
def _load_entries(slug: str) -> tuple:
    fp = _resolve(f"god_reliance/{slug}.json")
    if not fp:
        return tuple()
    with open(fp, encoding="utf-8") as f:
        return tuple(json.load(f))


def _percent(entries) -> int:
    if not entries:
        return 0
    num = sum(
        1 for e in entries
        if e["mode"] in _ASK_MODES or (e["mode"] == "부르심" and (e.get("obeyed") or e.get("covenant")))
    )
    return round(num / len(entries) * 100)


@functools.lru_cache(maxsize=1)
def _all_percents() -> dict:
    return {slug: _percent(_load_entries(slug)) for slug in _slug_to_id()}


@router.get("/person/{person_id}/reliance")
def get_person_reliance(person_id: str):
    slug = _id_to_slug().get(person_id)
    if not slug:
        return JSONResponse({"personId": person_id, "available": False, "phases": []})

    entries = sorted(_load_entries(slug), key=lambda e: e.get("approxYear", 0))
    verses = bible_verses()

    def _seg(ref, label):
        vid = _resolve_verse(ref)
        vt = verses.get(vid, {}) if vid else {}
        return {"label": label, "verse": ref, "verseTextKo": vt.get("textKo"), "verseTextEn": vt.get("textEn")}

    phases = []
    mode_counts = {}
    for e in entries:
        mode_counts[e["mode"]] = mode_counts.get(e["mode"], 0) + 1
        trig, out = e["trigger"], e["outcome"]
        outc = _seg(out["verse"], out["label"])
        if "kind" in out:
            outc["kind"] = out["kind"]
        ph = {
            "mode": e["mode"],
            "approxYear": e["approxYear"],
            "sameVerse": trig["verse"] == out["verse"],
            "trigger": _seg(trig["verse"], trig["label"]),
            "outcome": outc,
        }
        if "response" in e:  # 선택적 중간 단(계기→행동→결과 3단)
            ph["response"] = _seg(e["response"]["verse"], e["response"]["label"])
        if "obeyed" in e:
            ph["obeyed"] = e["obeyed"]
        if e.get("covenant"):
            ph["covenant"] = True
        phases.append(ph)

    pct = _percent(entries)
    all_p = _all_percents()
    n = len(all_p) or 1
    percentile = round(100 * sum(1 for v in all_p.values() if v <= pct) / n)
    rank = 1 + sum(1 for v in all_p.values() if v > pct)

    return JSONResponse(
        {
            "personId": person_id,
            "slug": slug,
            "nameKo": CURATED.get(slug, {}).get("nameKo", slug),
            "available": True,
            "percent": pct,
            "sampleSize": len(entries),
            "lowSample": len(entries) < LOW_SAMPLE,
            "percentile": percentile,
            "rank": rank,
            "total": len(all_p),
            "modeCounts": mode_counts,
            "phases": phases,
        },
        headers={"Cache-Control": "max-age=300"},
    )


@router.get("/reliance/ranking")
def get_reliance_ranking():
    rows = []
    for slug, pid in _slug_to_id().items():
        entries = _load_entries(slug)
        rows.append(
            {
                "slug": slug,
                "personId": pid,
                "nameKo": CURATED.get(slug, {}).get("nameKo", slug),
                "percent": _percent(entries),
                "sampleSize": len(entries),
                "lowSample": len(entries) < LOW_SAMPLE,
            }
        )
    rows.sort(key=lambda r: (-r["percent"], r["nameKo"]))
    return JSONResponse({"ranking": rows}, headers={"Cache-Control": "max-age=300"})
