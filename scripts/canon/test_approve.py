#!/usr/bin/env python3
"""`approve.night_pick` 단위 테스트 (task 368). host python3 · 표준 unittest만 — 명세는 dict로 지어 넣는다."""
import unittest

import approve
import scene_state as ss
from test_scene_state import spec


class NightPick(unittest.TestCase):
    def test_writes_final(self):
        s = approve.night_pick(spec(), 11, "edit", "/x/s11.png", "user")
        f = s["approved"]["final"]
        self.assertEqual((f["path"], f["seed"], f["kind"], f["image"], f["by"]), ("night-pick", 11, "edit", "/x/s11.png", "user"))

    def test_not_stale_without_stage_approvals(self):
        s = approve.night_pick(spec(), 42, "base", "/x/s42.png", "user")
        self.assertNotIn("final", ss.stale(s, {"attempts": []}))

    def test_ladder_final_still_stale(self):
        s = spec()
        s["approved"] = {"final": {"attempt": "a001", "seed": 11}}
        self.assertIn("final", ss.stale(s, {"attempts": []}))

    def test_bad_kind(self):
        with self.assertRaises(ValueError):
            approve.night_pick(spec(), 11, "both", "/x.png", "user")


if __name__ == "__main__":
    unittest.main()
