"""task 432 — rule_ab 고정 절 고르기 · 시드 목록 · 시드·A/B마다 다른 그림·판정 키 · 미리 정한 채택 규칙."""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch"))
import rule_ab as R


class FixedTest(unittest.TestCase):
    def test_423_default_one_seed_old_keys(self):
        R.use(423)
        self.assertEqual(R.FX["seeds"], [11])
        case = R.FX["cases"][0]
        self.assertEqual(R.key(case, "A", 11), f"{case['id']}-A")   # 423 metrics.json 옛 키 그대로

    def test_432_seeds_paths_keys_differ(self):
        R.use(432)
        self.assertEqual(R.FX["seeds"], [42, 7, 5, 11, 23, 101, 202, 303])
        self.assertEqual(R.FX["reps"], 3)
        case = R.FX["cases"][0]
        paths = {R.img(case, ab, s) for ab in "AB" for s in R.FX["seeds"]}
        keys = {R.key(case, ab, s) for ab in "AB" for s in R.FX["seeds"]}
        self.assertEqual((len(paths), len(keys)), (16, 16))
        self.assertTrue(all("two-mothers-step23" in p for p in paths))

    def test_436_one_side_a_only(self):
        """task 436 — b_from null: 지금 명세 그대로 A만(그림 8 · B 없음 · 통과 한 줄). 432 prompts 검사는 여기로 옮김
        (434가 벽 문구를 「dressed stone」으로 바꿔 432 b_from이 지금 명세에 없다)."""
        import contextlib, io
        from unittest import mock
        import derive_scene as D
        R.use(436)
        case = R.FX["cases"][0]
        self.assertEqual(R.sides(case), "A")
        self.assertEqual(len({R.img(case, ab, s) for ab in R.sides(case) for s in R.FX["seeds"]}), 8)
        a, b = R.prompts(case)
        self.assertEqual((a, b), (D.route_prompt(D.load(case["scene"])), None))
        self.assertEqual(R.side({}, case), "A")
        out = io.StringIO()
        with mock.patch.object(R, "load", return_value={"answers": {}}), contextlib.redirect_stdout(out):
            R.report()
        lines = out.getvalue().splitlines()
        self.assertEqual(sum(l.startswith("통과:") for l in lines), 1)
        self.assertFalse(any(l.startswith("채택:") or " B " in l for l in lines))

    def test_missing_block_exits(self):
        with self.assertRaises(SystemExit):
            R.fixed(999999)


class AdoptTest(unittest.TestCase):
    RULE = {"qs": ["x"], "gain": 3, "loss": 2}

    def ok(self, a, b):
        """a·b = {qid: 맞음 장 수} → 8시드 다수결 표."""
        return {ab: {s: {q: s < n[q] for q in n} for s in range(8)} for ab, n in (("A", a), ("B", b))}

    def test_gain_needed(self):
        self.assertTrue(R.adopt(self.ok({"x": 1, "y": 5}, {"x": 4, "y": 5}), ["x", "y"], self.RULE)[0])
        self.assertFalse(R.adopt(self.ok({"x": 1, "y": 5}, {"x": 3, "y": 5}), ["x", "y"], self.RULE)[0])

    def test_loss_over_two_blocks(self):
        self.assertTrue(R.adopt(self.ok({"x": 0, "y": 5}, {"x": 8, "y": 3}), ["x", "y"], self.RULE)[0])   # 2장 떨어짐은 괜찮음
        yes, _, _, lost = R.adopt(self.ok({"x": 0, "y": 5}, {"x": 8, "y": 2}), ["x", "y"], self.RULE)
        self.assertEqual((yes, lost), (False, ["y"]))


if __name__ == "__main__":
    unittest.main()
