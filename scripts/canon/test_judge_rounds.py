#!/usr/bin/env python3
"""회고 eval(2026-10-21 restyle·상식 규칙집): 공용 판정 스크립트를 고쳐도 지난 회차 기록이 그대로 다시 셈 되는가.

restyle_try.py는 r1~r6·r4e가 한 파일을 함께 쓰며 회차마다 고쳐졌다 — 고칠 때마다 지난 회차 `check`가 깨질 수 있다.
plausibility.py는 「잡음 ≥ 2/3」을 0.667 소수와 비교해 2/3을 떨어뜨린 적이 있다(notes/PLAUSIBILITY.md v1 결과) → 분수 비교를 고정한다.
GPU·네트워크 없음(기록된 metrics만 다시 센다).
  python3 test_judge_rounds.py"""
import os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(*args):
    r = subprocess.run([sys.executable, *args], cwd=HERE, capture_output=True, text=True)
    return r.returncode, r.stdout.strip().splitlines()[-1:] or [r.stderr[-200:]]


class JudgeRounds(unittest.TestCase):
    def test_restyle_rounds_recount(self):
        for rnd in ("r1", "r2", "r3", "r4", "r4e", "r5", "r6"):
            with self.subTest(round=rnd):
                self.assertEqual(run("batch/restyle_try.py", "check", "--round", rnd), (0, ["ok"]))

    def test_style_judge_recount(self):
        self.assertEqual(run("batch/style_judge.py", "check"), (0, ["ok"]))

    def test_plausibility_recount(self):
        for v in ([], ["--v", "2"]):
            with self.subTest(v=v):
                self.assertEqual(run("batch/plausibility.py", "check", *v), (0, ["ok"]))

    def test_plausibility_two_thirds_is_fraction(self):
        sys.argv = ["x"]
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import plausibility as P
        rid = next(iter(P.RULES))
        self.assertEqual(P.decide({rid: [2, 3, 0, 5]})[rid], "채택")   # 2/3 잡음 · 헛경보 0 → 채택(0.667 소수 비교면 미채택)
        self.assertEqual(P.decide({rid: [1, 2, 0, 5]})[rid], "미채택")


if __name__ == "__main__":
    unittest.main()
