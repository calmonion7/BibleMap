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


ENGEDI = "authored-david-en-gedi-saul"


def engedi():
    return json.load(open(os.path.join(HERE, "scenes", ENGEDI + ".json"), encoding="utf-8"))


class GazeObject(unittest.TestCase):
    """task 365 — gaze가 문구 객체 {ko,en,verse}여도 파생된다. 기존 파생은 한 글자도 바뀌지 않는다."""

    def test_engedi_matches_adopted_C(self):  # 사용자 채택 C s23(notes/ENGEDI-HANDFIX.md 「막 자른 뒤」) — 명세 파생 = C 프롬프트
        c = json.load(open(os.path.join(HERE, "samples", "engedi-aftercut", "metrics.json"), encoding="utf-8"))["prompt"]
        self.assertEqual(ds.whole_prompt(engedi()), c)

    def test_object_gaze_en_in_figure_sentence(self):
        spec = engedi()
        d = next(f for f in spec["figures"] if f["cast"] == "david")
        d["gaze"] = {"ko": "자르는 옷자락을 내려다봄", "en": "looking down at the hem he is cutting", "verse": "삼상 24:4"}
        p = ds.whole_prompt(spec)
        self.assertIn(d["gaze"]["en"], figure_sentence(p, spec, d))
        self.assertEqual(ds.check_whole(spec), [])
        d["gaze"] = {**d["gaze"], "verse": ""}
        self.assertTrue(ds.check_whole(spec))



class WideQuestions(unittest.TestCase):
    """task 370 — 방향 문항은 「누구와 마주 보는가(얼굴·상체)」, 판 묶음(대조)은 처치 칸 문항만 같은 문구로 잇달아."""

    def test_facing_from_gaze(self):
        import make_night_page as P
        spec = ds.load("authored-david-gath-achish")
        david, achish = spec["figures"]
        self.assertEqual(P.facing_q(achish), ("아기스가 누구와 마주 보는가(얼굴·상체)가 틀린 그림", "다윗과 마주 봄 · 화면 왼쪽을 향함"))
        self.assertEqual(P.facing_q(david)[1], david["gaze"]["ko"])   # 문구 객체면 그 ko
        self.assertEqual(P.josa("나하스", ("과", "와")), "나하스와")

    def test_facing_without_gaze(self):   # task 373 — 한 장 모드 칸이 없는 판 경로 장면: 판 facing + 그 방향 앞쪽 인물
        import make_night_page as P
        spec = ds.load("authored-david-nathan-covenant")
        nathan, david = spec["figures"]
        self.assertNotIn("gaze", nathan)
        self.assertEqual(P.facing_q(nathan, spec), ("나단이 누구와 마주 보는가(얼굴·상체)가 틀린 그림", "화면 왼쪽을 향한다 — 다윗 쪽"))

    def test_pair_plate_only_treatment_and_label(self):
        import make_night_page as P
        ids = ["moment", "background[0]", "figures[0].identity", "figures[0].pose", "figures[0].prop", "figures[0].facing", "guard"]
        qs, pqs = [{"id": i} for i in ids], [{"id": i, "p": 1} for i in ids if P.treat(i)]
        for label in ("가", "나"):
            out = P.pair_plate(qs, pqs, label)
            self.assertEqual(len(out), len(ids) + 3)
            plate = [i for i, q in enumerate(out) if q.get("grp") == "plate"]
            self.assertEqual([out[i]["id"] for i in plate], ["moment", "figures[0].pose", "figures[0].facing"])
            for i in plate:   # 같은 문항의 칸 묶음 화면과 바로 붙고, 「가」가 먼저
                j = i + 1 if label == "가" else i - 1
                self.assertEqual((out[j]["id"], out[j]["grp"]), (out[i]["id"], "whole"))
                self.assertEqual(out[i]["lab"], f"묶음 {label}")
                self.assertEqual(out[min(i, j)]["lab"], "묶음 가")

    def test_every_cast_named(self):   # task 391 — 판정 화면에 영어 id가 나오지 않게, cast 정본 전부가 이름표에
        import make_night_page as P
        ids = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HERE, "cast", "*.json"))}
        self.assertEqual(sorted(ids - set(P.NAME)), [])

    def test_plate_label_fixed_per_scene(self):
        import make_night_page as P
        import params
        labels = {s: P.plate_label(s) for s in params.WHOLE_WIDE_SCENES}
        self.assertEqual(labels, {s: P.plate_label(s) for s in params.WHOLE_WIDE_SCENES})
        self.assertLessEqual(set(labels.values()), {"가", "나"})


if __name__ == "__main__":
    unittest.main()
