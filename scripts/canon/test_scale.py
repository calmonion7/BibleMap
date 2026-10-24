#!/usr/bin/env python3
"""`scale.py`·`scale.json` 단위 테스트 (task 408). host python3 · 표준 unittest만 — 크기 기준표 꼴·근거·카드 등급 덮음·환산·문항 채우기·코드 리터럴."""
import glob
import json
import os
import unittest

import scale as S


class Table(unittest.TestCase):
    def test_why_every_value(self):
        """값마다 근거 단계([직접]·[추론]·[저작](이유)) — 근거 없는 숫자가 표에 들어오지 않게."""
        self.assertEqual(S.why_errors(), [])

    def test_schema(self):
        T = S.table()
        for k in ("unit", "body", "age_head", "age_height_min", "height", "build_width", "guide", "refs", "figures", "held_exclude"):
            self.assertIn(k, T)
        for k in ("head", "shoulder", "crotch", "knee", "arm"):
            self.assertTrue(0 < S.v(f"body.{k}") < 1, k)
        self.assertEqual(S.ref("man-height"), 1.0)

    def test_cast_classes_covered(self):
        """cast 카드 등급(heightRel·silhouette.class·ageBand.class)이 표에 다 있다 — 표에 없는 등급은 가이드·검사가 숫자를 못 셈."""
        T = S.table()
        miss = []
        for p in sorted(glob.glob(os.path.join(S.HERE, "cast", "*.json"))):
            with open(p, encoding="utf-8") as fh:
                card = json.load(fh).get("card", {})
            for sect, cls in (("height", card.get("heightRel")), ("build_width", (card.get("silhouette") or {}).get("class")),
                              ("age_head", (card.get("ageBand") or {}).get("class"))):
                if cls not in T[sect]:
                    miss.append(f"{os.path.basename(p)} {sect}.{cls}")
        self.assertEqual(miss, [])

    def test_figures_match_cards(self):
        """본문이 키를 말하는 인물 — 카드 등급이 표의 인물 칸과 같다."""
        with open(os.path.join(S.HERE, "cast", "saul.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["card"]["heightRel"], S.v("figures.saul"))
        with open(os.path.join(S.HERE, "cast", "goliath.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["card"]["heightRel"], "towering")


class Units(unittest.TestCase):
    def test_cubit(self):
        """골리앗 「여섯 규빗 한 뼘」(삼상 17:4) = 289cm → towering = 289 ÷ 어른 남자 키."""
        g = S.v("figures.goliath")
        h = S.cm(g["cubit"], "cubit") + S.cm(g["span"], "span")
        self.assertAlmostEqual(h, 289.25, places=2)
        self.assertAlmostEqual(S.height_rel("towering"), h / S.v("unit.man_cm"), places=2)
        self.assertAlmostEqual(S.cm(1, "span"), S.cm(1, "cubit") / 2, places=3)

    def test_tall_is_shoulder_step(self):
        """tall — 백성의 키가 사울의 어깨 높이에 닿음(삼상 9:2 「어깨 위는 더하더라」): 보통 키 ÷ (1 − 어깨 위). 두 값이 따로 놀지 않게."""
        self.assertAlmostEqual(S.height_rel("tall"), S.height_rel("average") / (1 - S.v("body.shoulder")), places=2)

    def test_head_ratio(self):
        self.assertGreater(S.head_ratio("child"), S.head_ratio("youth"))
        self.assertGreater(S.head_ratio("youth"), S.head_ratio("middle"))
        self.assertEqual(S.head_ratio("없는등급"), S.v("body.head"))
        self.assertEqual(S.build_width(None), S.v("build_width.average"))


class Fill(unittest.TestCase):
    def test_fill(self):
        self.assertEqual(S.fill("키의 {{1/[body.head]|1}}분의 1"), "키의 7.5분의 1")
        self.assertEqual(S.fill("{{[figures.david-youth.0]|0}}~{{[figures.david-youth.1]|0}}세"), "15~20세")
        self.assertEqual(S.fill("숫자 없음"), "숫자 없음")
        with self.assertRaises(ValueError):
            S.fill("{{__import__('os')}}")

    def test_fill_follows_table(self):
        """표 값을 바꾸면 문항 글 숫자도 바뀐다(S4) — 문항에 숫자를 손으로 쓰지 않는 까닭."""
        q = "사울이 다윗보다 키가 {{[height.tall]/[height.average]|2}}배쯤 · 촉 길이가 머리의 {{[w.spear.look.size.ratio]*[w.spear.look.size.parts.point.ratio]/[body.head]|1}}배쯤"
        before = S.fill(q)
        self.assertIn("1.21배", before)
        old = S.table()["height"]["tall"]["v"]
        try:
            S.table()["height"]["tall"]["v"] = 1.3
            self.assertNotEqual(S.fill(q), before)
            self.assertIn("1.3배", S.fill(q))
        finally:
            S.table()["height"]["tall"]["v"] = old


class Literals(unittest.TestCase):
    def test_no_size_literals_in_code(self):
        """크기 숫자는 표에서만(규칙 derive.scale-table) — 지킴 이름이 코드에서 숫자로 다시 정해지면 걸림."""
        self.assertEqual(S.literal_errors(), [])

    def test_literal_detector_catches(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".py", dir=S.HERE, delete=False) as fh:
            fh.write("KNEE = 0.72\nHEAD_STEP, HEAD_TOL = 0.87, 0.04\nBUILD_WIDTH = S.x()\n")
        try:
            errs = S.literal_errors((os.path.basename(fh.name),))
            self.assertEqual(len(errs), 2, errs)
        finally:
            os.unlink(fh.name)


if __name__ == "__main__":
    unittest.main()
