#!/usr/bin/env python3
"""`gen_lora_v4` 관문 셈 단위 테스트 (task 445). host python3 · GPU·그림 없이 — 수치는 notes/FACE-LORA-V4.md 고정 절에서 읽는다."""
import unittest

import gen_lora_v4 as M

OK, NG = "맞음", "틀림"


class Majority(unittest.TestCase):
    def test_two_of_three(self):
        self.assertEqual(M.majority([NG, NG, OK]), NG)
        self.assertEqual(M.majority([NG, OK, OK]), OK)


class Calibration(unittest.TestCase):
    """S2: A 사람 답 일치 ≥ 20/24 그리고 B 「틀림」 ≥ 12/16 → 관문으로 씀."""

    def a(self, agree):
        return [(OK, OK)] * agree + [(OK, NG)] * (24 - agree)

    def test_pass_at_threshold(self):
        self.assertEqual(M.cal_conclude(self.a(20), [NG] * 12 + [OK] * 4)[0], "관문으로 씀")

    def test_a_short(self):
        self.assertEqual(M.cal_conclude(self.a(19), [NG] * 16)[0], "관문 아님")

    def test_b_short(self):
        self.assertEqual(M.cal_conclude(self.a(24), [NG] * 11 + [OK] * 5)[0], "관문 아님")


class SheetGate(unittest.TestCase):
    def test_eighty_percent(self):
        self.assertTrue(M.sheet_gate([OK] * 20 + [NG] * 5)[0])
        self.assertFalse(M.sheet_gate([OK] * 19 + [NG] * 6)[0])


class SceneGate(unittest.TestCase):
    def test_whole_and_heads(self):
        good = [(OK, [OK, OK])] * 6 + [(NG, [NG, NG])] * 2
        heads_bad = [(OK, [OK, NG])] * 3 + [(OK, [OK, OK])] * 5
        g = M.scene_gate({"C": good, "L": heads_bad})
        self.assertEqual(g["C"], (6, 6, True))
        self.assertEqual(g["L"], (8, 5, False))

    def test_missing_head_fails(self):
        g = M.scene_gate({"L": [(OK, [OK])] * 8})
        self.assertFalse(g["L"][2])


class Tally(unittest.TestCase):
    def ans(self, style, l_yes, c_yes=(0, 0)):
        a = {f"S:{w}": s for w, s in zip(M.WHO, style)}
        for arm, ys in (("L", l_yes), ("C", c_yes)):
            for w, y in zip(M.WHO, ys):
                for i, s in enumerate((11, 42, 7, 23, 5, 101, 202, 303)):
                    a[f"A:{arm}:{s}:{w}"] = "yes" if i < y else "no"
        return a

    def test_adopt(self):
        self.assertEqual(M.tally(self.ans(("yes", "yes"), (5, 6)))[0], "채택")

    def test_conditional(self):
        self.assertEqual(M.tally(self.ans(("yes", "yes"), (5, 4)))[0], "조건부")

    def test_style_no_rejects(self):
        self.assertEqual(M.tally(self.ans(("yes", "no"), (8, 8)))[0], "미채택")

    def test_lenient(self):
        self.assertTrue(M.tally(self.ans(("yes", "yes"), (5, 5), (3, 3)))[1]["lenient"])
        self.assertFalse(M.tally(self.ans(("yes", "yes"), (5, 5), (3, 2)))[1]["lenient"])

    def test_retry_arm(self):
        a = {k.replace("A:L:", "A:L07:"): v for k, v in self.ans(("yes", "yes"), (5, 5)).items()}
        self.assertEqual(M.tally(a, "L07")[0], "채택")


if __name__ == "__main__":
    unittest.main()
