#!/usr/bin/env python3
"""후보 화면 규칙 테스트 (task 376, notes/VERSE-REGEN.md 고정 절) — 작은 가짜 J1 답으로 후보·되돌림·표본·화면 수를 단언한다.

  python3 -m unittest test_candidate_page"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as D
import judge_learn as JL

OK, NO = "맞음", "틀림"


def seed(moment, wrong=0, n=4):
    """moment 답 + 나머지 문항 n개 중 wrong개 틀림."""
    return {"moment": moment, **{f"q{i}": (NO if i < wrong else OK) for i in range(n)}}


class CandidateRule(unittest.TestCase):
    def test_fewest_wrong_among_moment_ok(self):
        # s7은 틀림이 가장 적지만 장면 뜻이 틀림 → 후보가 될 수 없다
        c = JL.pick_candidates({"x": {11: seed(OK, 3), 42: seed(OK, 1), 7: seed(NO, 0)}})["x"]
        self.assertEqual(c["cand"], 42)
        self.assertFalse(c["reject"])

    def test_tie_takes_earlier_seed(self):
        c = JL.pick_candidates({"x": {11: seed(OK, 2), 42: seed(OK, 1), 7: seed(OK, 1)}})["x"]
        self.assertEqual(c["cand"], 42)

    def test_all_moment_wrong_is_reject(self):
        c = JL.pick_candidates({"x": {11: seed(NO), 42: seed(NO), 7: seed(NO)}})["x"]
        self.assertEqual((c["cand"], c["sample"], c["reject"]), (None, None, True))

    def test_missing_answer_counts_wrong(self):
        # 답 없음(실패 호출): moment가 없으면 후보 불가, 다른 칸이 없으면 틀림으로 셈
        a = {"x": {11: {**seed(OK, 0), "q0": None}, 42: {**seed(OK, 0), "moment": None}, 7: seed(OK, 0)}}
        c = JL.pick_candidates(a)["x"]
        self.assertEqual(c["wrong"][11], 1)
        self.assertEqual(c["cand"], 7)

    def test_sample_is_not_cand_and_ignores_answers(self):
        seeds = [11, 42, 7, 23, 5, 101, 202, 303]
        a1 = JL.pick_candidates({"x": {s: seed(OK, 0 if s == 11 else 2) for s in seeds}})["x"]
        a2 = JL.pick_candidates({"x": {s: seed(OK, 0 if s == 11 else (3 if s % 2 else 1)) for s in seeds}})["x"]
        self.assertEqual(a1["cand"], 11)
        self.assertNotEqual(a1["sample"], 11)
        self.assertEqual(a1["sample"], a2["sample"])   # 같은 후보면 J1 답이 달라도 같은 표본
        self.assertEqual(a1["sample"], next(s for s in JL.sample_order("x", seeds) if s != 11))

    def test_screens(self):
        self.assertEqual(JL.screens([{"reject": False}] * 13 + [{"reject": True}]), 27)
        self.assertEqual(JL.screens([{"reject": False}] * 14), 28)


class CandJudgment(unittest.TestCase):
    H = {"틀림": [8, 10], "맞음": [30, 40]}   # 잡기 0.8 · 통과 0.75

    def test_adopt(self):
        sc = [{"reject": False, "machine_cand": 5, "cand": 5}] * 8 + [{"reject": False, "machine_cand": 5, "cand": 7}] * 2
        self.assertEqual(JL.cand_rules(sc, self.H)[0], "판정: 후보 화면 채택")

    def test_hold_on_switch_revive_and_hits(self):
        sc = [{"reject": False, "machine_cand": 5, "cand": 7}] * 3 + [{"reject": False, "machine_cand": 5, "cand": 5}] * 5 \
            + [{"reject": True, "machine_cand": None, "cand": 11, "revived": 11}]
        line, r = JL.cand_rules(sc, {"틀림": [7, 10], "맞음": [30, 40]})
        self.assertEqual(line, "판정: 보류 (어긴 규칙 1, 2, 3)")
        self.assertEqual([ok for ok, _ in r], [False, False, False])


class PromptRoute(unittest.TestCase):
    def test_route_by_whole_background(self):
        nob, ark = D.load("authored-david-nob-priests"), D.load("authored-david-ark-jerusalem")
        self.assertIn("whole_background", nob)
        self.assertNotIn("whole_background", ark)
        self.assertEqual(D.route_prompt(nob), D.whole_prompt(nob))
        self.assertEqual(D.route_prompt(ark), D.plate_whole_prompt(ark))


if __name__ == "__main__":
    unittest.main()
