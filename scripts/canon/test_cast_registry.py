#!/usr/bin/env python3
"""cast 등록 정합 (task 394 회고). host python3 · 표준 unittest만.
세 곳이 따로 적는 「어느 장면에 누가 나오나」 — 장면 명세 figures · CAST.md 장면 줄 · cast/<id>.json stops — 가 서로 맞는지,
그리고 명세의 인용 절이 구절 범위(verses.range) 안인지. 394 성경 검토가 잡은 어긋남(기브아 다윗 cast를 바꾸고 stops를 안 바꿈 ·
범위 밖 인용)은 check_cast_v2·check_scenes가 통과시켰다."""
import glob
import json
import os
import re
import unittest

import check_cast_v2 as CC
import check_scenes as CS

HERE = os.path.dirname(os.path.abspath(__file__))


def cards():
    out = {}
    for p in glob.glob(os.path.join(HERE, "cast", "*.json")):
        with open(p, encoding="utf-8") as fh:
            c = json.load(fh)
        out[c["id"]] = c
    return out


def specs():
    out = {}
    for p in glob.glob(os.path.join(HERE, "scenes", "*.json")):
        with open(p, encoding="utf-8") as fh:
            s = json.load(fh)
        out[s["id"]] = s
    return out


class CastRegistry(unittest.TestCase):
    def setUp(self):
        self.reg, self.cards, self.specs = CC.stop_cast(), cards(), specs()

    def test_card_stops_match_cast_md(self):
        bad = [f"{cid}:{s}" for cid, c in self.cards.items() for s in c.get("stops") or [] if cid not in self.reg.get(s, [])]
        bad += [f"{s}:{cid}" for s, cs in self.reg.items() for cid in cs if cid in self.cards and s not in (self.cards[cid].get("stops") or [])]
        self.assertEqual(bad, [])

    def test_scene_figures_in_cast_md(self):
        bad = {sid: sorted({f["cast"] for f in s["figures"]} - set(self.reg[sid])) for sid, s in self.specs.items() if sid in self.reg}
        self.assertEqual({k: v for k, v in bad.items() if v}, {})


class QuoteRange(unittest.TestCase):
    def test_quotes_inside_range(self):
        bad = {}
        for sid, s in specs().items():
            m = re.match(r"(\S+)\s*(.+)", s["verses"]["range"])
            book = CS.BOOK[m.group(1)]
            inside = set(CS.verse_ids(book, m.group(2)))
            out = [k for k in s["verses"].get("quotes", {}) if not set(CS.verse_ids(book, k)) <= inside]
            if out:
                bad[sid] = out
        self.assertEqual(bad, {})


if __name__ == "__main__":
    unittest.main()
