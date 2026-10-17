#!/usr/bin/env python3
"""`derive_scene.whole_prompt` 낱말 자리 회귀 테스트 (2026-10-18, task 363 회고 eval).

host python3 · 표준 unittest만. GPU 0 — 실제 장면 명세(scenes/*.json)에서 파생만 한다.
task 363 r1: 장면 차림을 몸짓 앞으로 옮기자 길갈 「접은 망토」가 흰 천이 되어 8/8 무너졌고,
인물별 방향 구절을 장면 문장 하나로 합치자 엔게디 사울이 돌아섰다. 중복은 빼기만 하고 자리는 지킨다.
"""
import glob
import json
import os
import unittest

import derive_scene as ds

HERE = os.path.dirname(os.path.abspath(__file__))


def whole_scenes():
    for p in sorted(glob.glob(os.path.join(HERE, "scenes", "*.json"))):
        spec = json.load(open(p, encoding="utf-8"))
        if "whole_background" in spec:
            yield os.path.basename(p)[:-5], spec


def figure_sentence(prompt, spec, f):
    head = f"{ds._side(f, spec).capitalize()}: "
    i = prompt.index(head)
    return prompt[i:prompt.index(". ", i) if ". " in prompt[i:] else len(prompt)]


class WholePromptOrder(unittest.TestCase):
    def test_costume_after_gesture(self):
        for sid, spec in whole_scenes():
            p = ds.whole_prompt(spec)
            for f in spec["figures"]:
                if "beardless" in f["costume"]["en"]:  # 덮어쓰기 경로 — 차림이 cast 자리에 든다
                    continue
                s = figure_sentence(p, spec, f)
                with self.subTest(scene=sid, cast=f["cast"]):
                    self.assertLess(s.index(f["gesture"]["en"]), s.index(f["costume"]["en"]))

    def test_facing_per_figure_no_scene_sentence(self):
        for sid, spec in whole_scenes():
            p = ds.whole_prompt(spec)
            with self.subTest(scene=sid):
                self.assertNotIn("Both figures", p)
                self.assertNotIn("All figures", p)
            for f in spec["figures"]:
                if f.get("screen_facing"):
                    with self.subTest(scene=sid, cast=f["cast"]):
                        self.assertIn(ds.SCREEN_FACING[f["screen_facing"]][0], figure_sentence(p, spec, f))

    def test_cast_costume_not_duplicated(self):
        for sid, spec in whole_scenes():
            p = ds.whole_prompt(spec)
            for f in spec["figures"]:
                cast_cost = ds._cast_in_scene(f).get("costume")
                if cast_cost and cast_cost not in f["costume"]["en"]:
                    with self.subTest(scene=sid, cast=f["cast"]):
                        self.assertNotIn(cast_cost, figure_sentence(p, spec, f))


if __name__ == "__main__":
    unittest.main()
