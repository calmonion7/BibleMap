#!/usr/bin/env python3
"""자른 구도 갈래 단위 테스트 (task 464). host python3 · 표준 unittest만 — 크기 기준표 framing과 recheck.figure_scale_errors 분기를 본다."""
import copy
import unittest

import derive_scene as D
import recheck
import scale as S

GATH = "authored-david-gath-achish"
JORDAN = "authored-david-returns-jerusalem"


class FocusRange(unittest.TestCase):
    def test_no_framing_is_crowd_stage(self):
        s = D.load(JORDAN)
        self.assertNotIn("framing", s.get("guide") or {})
        self.assertEqual(S.focus_range(s), S.crowd_stage(S.people_count(s)))

    def test_knee_reads_table(self):
        s = copy.deepcopy(D.load(JORDAN))
        s["guide"]["framing"] = "knee"
        self.assertEqual(S.focus_range(s), ("knee", tuple(S.v("framing.knee")["focus_h"])))


class FigureScale(unittest.TestCase):
    def test_knee_without_why_fails(self):
        s = copy.deepcopy(D.load(GATH))
        s["guide"]["framing"] = "knee"
        s["guide"].pop("framing_why", None)
        self.assertTrue(any("framing_why" in e for e in recheck.figure_scale_errors(s)))

    def test_knee_small_figures_fail(self):   # 갈래를 켜고 몸 전체 키(0.595)를 그대로 두면 범위 밖
        s = copy.deepcopy(D.load(GATH))
        s["guide"]["framing"] = "knee"
        s["guide"]["framing_why"] = "21:13 「침을 수염에 흘리매」"
        for k in ("david", "achish"):
            s["regions"][k] = [s["regions"][k][0], 0.305, s["regions"][k][2], 0.90]
        self.assertTrue(any("(무리 단계 knee)" in e for e in recheck.figure_scale_errors(s)))

    def test_gath_passes_with_knee(self):
        s = D.load(GATH)
        self.assertEqual(s["guide"].get("framing"), "knee")
        self.assertEqual(recheck.figure_scale_errors(s), [])


if __name__ == "__main__":
    unittest.main()
