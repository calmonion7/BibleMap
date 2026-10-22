#!/usr/bin/env python3
"""장면 × 단계 누적 규칙(task 399~) 단위 테스트. host python3 · 표준 unittest — 걸림·안 걸림 사례마다 하나씩.
관문 실측 한 건만 venv314 토큰 검사를 탄다(그 밖은 명세 사본만 본다)."""
import copy
import json
import os
import unittest
from unittest import mock

import check_scenes
import recheck

HERE = os.path.dirname(os.path.abspath(__file__))
GIBEAH = "authored-saul-gibeah-spear"


def gibeah():
    with open(os.path.join(HERE, "scenes", f"{GIBEAH}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def verses():
    with open(check_scenes.VERSES, encoding="utf-8") as fh:
        return json.load(fh)


class SpecGate(unittest.TestCase):
    """generate.spec-gate — 명세 규칙에 걸리면 새 그림을 만들지 않는다."""

    def test_refuses_failing_spec(self):
        with mock.patch.object(recheck, "spec_failures", return_value=(["spec.verse-elements"], {"spec.verse-elements": ["verse_elements 없음"]})):
            with self.assertRaises(SystemExit) as cm:
                recheck.require_pass(GIBEAH)
        self.assertIn("명세 규칙 불통과", str(cm.exception.code))

    def test_not_measured_is_not_pass(self):
        """못 잼(none)도 통과가 아니다 — 토큰을 못 재면 512 넘침을 모르고 그리게 된다."""
        with mock.patch.object(recheck, "_eval", return_value=({"derive.512-tokens": "none", "spec.required-fields": "pass"}, {})), \
             mock.patch.object(recheck, "_context", return_value=({}, "없음")):
            self.assertEqual(recheck.spec_failures(GIBEAH), ["derive.512-tokens"])

    def test_generator_calls_gate_before_gpu(self):
        import batch.gibeah_redraw as G
        with mock.patch.object(recheck, "require_pass", side_effect=SystemExit("명세 규칙 불통과: x")) as gate, \
             mock.patch("subprocess.run") as run:
            with self.assertRaises(SystemExit):
                G.gen()
        gate.assert_called_once_with(GIBEAH)
        run.assert_not_called()   # 바쁨 검사(pgrep)·생성 어느 것도 안 돈다

    def test_gibeah_passes_now(self):
        """단계 ① 통과 실측(task 399) — 재저작한 기브아 명세는 걸리는 규칙이 없다."""
        self.assertEqual(recheck.spec_failures(GIBEAH), [])


class StageFromScripture(unittest.TestCase):
    """spec.stage-from-scripture — 인물마다 생애 단계 근거([직접]|[추론] + 「인용」 + 장:절)."""

    def test_missing_stage_why_fails(self):
        s = gibeah()
        del s["figures"][1]["stage_why"]
        self.assertEqual(len(recheck.stage_why_errors(s)), 1)

    def test_authored_mark_is_not_enough(self):
        """[저작]은 근거가 아니다 — 나이는 본문 단서로 유추한다."""
        s = gibeah()
        s["figures"][1]["stage_why"] = "[저작] 「소년」 17:33 — 정한 값"
        self.assertTrue(recheck.stage_why_errors(s))

    def test_quote_and_ref_required(self):
        s = gibeah()
        s["figures"][0]["stage_why"] = "[추론] 재위 중이라 장년"
        self.assertTrue(recheck.stage_why_errors(s))

    def test_gibeah_figures_pass(self):
        self.assertEqual(recheck.stage_why_errors(gibeah(), verses()), [])

    def test_quote_must_match_scripture(self):
        """2차 검토 — 삼하 2:10 「비로소」가 빠진 인용이 추론의 하한을 흔들었다. 인용은 본문 글자 그대로."""
        s = gibeah()
        s["figures"][0]["stage_why"] = s["figures"][0]["stage_why"].replace("이스보셋이 비로소 이스라엘", "이스보셋이 이스라엘")
        self.assertTrue(any("본문에 없음" in e for e in recheck.stage_why_errors(s, verses())))

    def test_quote_needs_book_ref(self):
        s = gibeah()
        s["figures"][1]["stage_why"] = s["figures"][1]["stage_why"].replace("삼상 17:56 「", "17:56 「")
        self.assertTrue(any("대조 못 함" in e for e in recheck.stage_why_errors(s, verses())))


class ActionPlaceOnFigure(unittest.TestCase):
    """spec.action-place-on-figure — 「자리」 요소는 인물 칸이 나른다."""

    def test_place_on_background_fails(self):
        s = gibeah()
        el = next(e for e in s["verse_elements"] if e["kind"] == "자리")
        el["field"], el["en"] = "whole_background", "a bare wall behind David"
        self.assertEqual(len(check_scenes.place_on_figure_errors(s)), 1)

    def test_place_on_figure_passes(self):
        self.assertEqual(check_scenes.place_on_figure_errors(gibeah()), [])

    def test_no_elements_is_not_measured(self):
        s = gibeah()
        del s["verse_elements"]
        self.assertIsNone(check_scenes.place_on_figure_errors(s))

    def test_place_is_a_kind(self):
        s = copy.deepcopy(gibeah())
        self.assertEqual([e for e in check_scenes.verse_element_errors(s, recheck.ds.route_prompt(s)) if "kind" in e], [])


class ThrownGuide(unittest.TestCase):
    """generate.thrown-guide — 던짐 순간은 허공 물체 꼴이 있는 가이드로."""

    def test_throw_without_guide_fails(self):
        s = gibeah()
        del s["guide"]
        self.assertEqual(len(recheck.thrown_guide_errors(s)), 1)

    def test_guide_without_air_object_fails(self):
        s = gibeah()
        s["guide"]["shape"]["spear"] = "person"
        self.assertEqual(len(recheck.thrown_guide_errors(s)), 1)

    def test_no_throw_verb_needs_nothing(self):
        s = gibeah()
        del s["guide"]
        s["moment"]["verse"] = "18:9"
        self.assertEqual(recheck.thrown_guide_errors(s), [])

    def test_gibeah_passes(self):
        self.assertEqual(recheck.thrown_guide_errors(gibeah()), [])

    def test_generator_refuses_stale_guide(self):
        import batch.gibeah_redraw as G
        s = gibeah()
        s["regions"]["spear"] = [0.2, 0.3, 0.4, 0.33]   # 명세가 바뀌었는데 가이드 파일은 그대로
        with mock.patch.dict(G.FX, {"guide": "samples/gibeah-step23/guide.png"}):
            with self.assertRaises(SystemExit):
                G.guide_ok(s)

    def test_generator_refuses_missing_guide(self):
        import batch.gibeah_redraw as G
        with mock.patch.dict(G.FX, {"guide": None}):
            with self.assertRaises(SystemExit):
                G.guide_ok(gibeah())


class LexiconLink(unittest.TestCase):
    """spec.lexicon-link — 사전 낱말이 걸린 지물은 사전 look 문구로."""

    def test_lyre_without_lexicon_text_fails(self):
        s = gibeah()
        s["figures"][1]["gesture"]["en"] = "twisting aside, holding a lute"
        self.assertTrue(check_scenes.lexicon_look_errors(s, recheck.ds.route_prompt(s)))

    def test_gibeah_passes(self):
        s = gibeah()
        self.assertEqual(check_scenes.lexicon_look_errors(s, recheck.ds.route_prompt(s)), [])


class GuideBackdrop(unittest.TestCase):
    """generate.guide-backdrop — 실내 장면 가이드는 방 바탕."""

    def test_indoor_without_room_backdrop_fails(self):
        s = gibeah()
        s["guide"].pop("backdrop")
        self.assertEqual(len(recheck.guide_backdrop_errors(s)), 1)

    def test_outdoor_needs_nothing(self):
        s = gibeah()
        s["guide"].pop("backdrop")
        s["whole_background"]["en"] = "a dry riverbank under an open sky"
        self.assertEqual(recheck.guide_backdrop_errors(s), [])

    def test_gibeah_passes(self):
        self.assertEqual(recheck.guide_backdrop_errors(gibeah()), [])


class GuideBodyMass(unittest.TestCase):
    """generate.guide-body-mass — 가이드 사람 꼴은 기본 꼴(person)만큼 몸 덩어리가 있어야 한다.
    a3: 가는 몸통·막대 다리 꼴이면 카드 체격 문구(넓은 어깨·통 몸통)가 화면 끝에 셋째 인물로 그려졌다(8/8)."""

    def test_person_like_shapes_keep_mass(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        from PIL import Image, ImageDraw

        def area(fn):
            im = Image.new("L", (400, 800), 0)
            fn(ImageDraw.Draw(im), 100, 100, 300, 700, 255)
            return sum(im.histogram()[1:])
        base = area(M.person)
        for k, fn in M.SHAPES.items():
            if k.startswith("person"):
                self.assertGreaterEqual(area(fn) / base, 0.9, k)


class GuideBodyBuild(unittest.TestCase):
    """generate.guide-body-build — 사람 꼴이 있는 가이드는 몸 너비를 카드 체격에서."""

    def test_person_guide_without_card_body_fails(self):
        s = gibeah()
        s["guide"].pop("body")
        self.assertEqual(len(recheck.guide_body_errors(s)), 1)

    def test_broad_card_draws_wider_body(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        s = gibeah()
        wide = sum(M.make(s).convert("L").histogram()[200:])
        s["guide"].pop("body")
        self.assertGreater(wide, sum(M.make(s).convert("L").histogram()[200:]))

    def test_gibeah_passes(self):
        self.assertEqual(recheck.guide_body_errors(gibeah()), [])


if __name__ == "__main__":
    unittest.main()
