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


gibeah_cached = gibeah()


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
        for knee in (False, True):   # b2: 무릎 아래 다리 꼴도 몸 덩어리 유지
            M.BODY["knee"] = knee
            try:
                for k, fn in M.SHAPES.items():
                    if k.startswith("person"):
                        self.assertGreaterEqual(area(fn) / base, 0.9 if not knee else 0.85, (k, knee))
            finally:
                M.BODY["knee"] = False


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
        s["guide"].pop("control", None), s["guide"].pop("split", None)   # 깊이 모드 규칙(h1부터 기브아는 스텝별 — 다른 장면은 깊이 한 장)
        s["guide"].pop("pose", None)   # c7부터 넓은 체격 사울은 뼈대 — 깊이 몸 너비를 재려고 깊이 꼴로
        wide = sum(M.make(s).convert("L").histogram()[200:])
        s["guide"].pop("body")
        self.assertGreater(wide, sum(M.make(s).convert("L").histogram()[200:]))

    def test_gibeah_passes(self):
        self.assertEqual(recheck.guide_body_errors(gibeah()), [])


class GuidePose(unittest.TestCase):
    """task 403 c7 — guide.pose 인물은 깊이 꼴(person_follow) 대신 OpenPose 뼈대(색 있는 팔다리) — 깊이 꼴은 관절 각도·다리 길이를 못 줌(c1~c6).
    task 404 f1 — 뼈대 아래 깊이 몸은 뼈대 관절을 따른다(generate.pose-body-mass): 옛 깊이 꼴 실루엣과 겹침이 작아야 함."""

    def test_pose_region_has_skeleton_and_skeleton_body(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        s = gibeah()
        s["guide"].pop("control", None), s["guide"].pop("split", None)   # 깊이 모드 규칙(h1부터 기브아는 스텝별 — 다른 장면은 깊이 한 장)
        x0, y0, x1, y1 = (round(v * d) for v, d in zip(s["regions"]["saul"], (M.W, M.H, M.W, M.H)))
        crop = M.make(s).crop((x0, y0, x1, y1))
        px = list(crop.getdata())
        color = sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) > 60)   # 뼈대 색
        self.assertGreater(color, 500)
        body = {i for i, (r, g, b) in enumerate(px) if min(r, g, b) > 230}
        s["guide"].pop("pose")
        old = {i for i, (r, g, b) in enumerate(M.make(s).crop((x0, y0, x1, y1)).getdata()) if min(r, g, b) > 230}
        self.assertGreater(len(old), 0.15 * len(px))                            # 뼈대 없으면 옛 깊이 꼴
        self.assertLess(len(body & old) / len(body | old), 0.6)                  # 뼈대 몸은 옛 꼴과 다른 모양(관절을 따름)


class PoseBodyMass(unittest.TestCase):
    """generate.pose-body-mass — 뼈대 인물도 카드 너비 깊이 몸(task 404 f1 — 뼈대만이면 「barrel torso」 부풀림, 사울 비율 c11 1/8 vs c5 5/8)."""

    def test_body_present_and_card_width(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        s = gibeah()
        s["guide"].pop("control", None), s["guide"].pop("split", None)   # 깊이 모드 규칙(h1부터 기브아는 스텝별 — 다른 장면은 깊이 한 장)
        x0, y0, x1, y1 = (round(v * d) for v, d in zip(s["regions"]["saul"], (M.W, M.H, M.W, M.H)))
        def body(spec):
            return sum(1 for r, g, b in M.make(spec).crop((x0, y0, x1, y1)).getdata() if min(r, g, b) > 230)
        broad = body(s)
        self.assertGreater(broad, 0.05 * (x1 - x0) * (y1 - y0))                   # 몸 덩어리가 있다
        s["figures"][0].setdefault("cast_override", {}).setdefault("card", {})["silhouette"] = {"class": "slight", "text": "slight"}
        self.assertLess(body(s), broad)                                          # 카드 너비를 따른다


class HeightRatio(unittest.TestCase):
    """generate.height-ratio — 같은 깊이 두 인물 키 비 = 0.87 ** 등급 차 ± 0.04(task 404 f1)."""

    def test_youth_too_small_fails(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = s["regions"]["david-youth"][3] - 0.78 * (s["regions"]["saul"][3] - s["regions"]["saul"][1])   # 0.87 − 0.09
        self.assertEqual(len(recheck.height_ratio_errors(s)), 1)

    def test_farther_foot_from_horizon_passes(self):
        """task 409 — 거리는 depth 꼬리표가 아니라 발 y: 다윗 발을 위로(멀리) 옮기고 지평선에서 계산한 키로 그리면 통과,
        같은 발 y에 depth 꼬리표만 다르게 둔 작은 다윗은 이제 걸린다(옛 검사는 depth가 다르면 건너뜀)."""
        import scale as S
        s = gibeah()
        hy = S.scene_horizon(s)
        s["regions"]["david-youth"][3] = 0.8
        s["regions"]["david-youth"][1] = 0.8 - S.screen_height(0.8, hy, S.height_rel("average"))
        self.assertEqual(recheck.height_ratio_errors(s), [])
        t = gibeah()
        t["regions"]["david-youth"][1] = t["regions"]["david-youth"][3] - 0.78 * (t["regions"]["saul"][3] - t["regions"]["saul"][1])
        t["guide"]["depth"]["david-youth"] = 0.7
        self.assertEqual(len(recheck.height_ratio_errors(t)), 1)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.height_ratio_errors(gibeah()), [])


class DodgeClear(unittest.TestCase):
    """generate.dodge-clear — 피하는 사람의 머리 높이로 곧장 날아가는 물체 금지."""

    def test_object_at_head_height_fails(self):
        s = gibeah()
        y0 = s["regions"]["david-youth"][1]   # 지금 다윗 구역의 머리 높이에 창을 놓는다(구역이 바뀌어도 같은 사례)
        s["regions"]["spear"] = [0.27, y0 + 0.01, 0.50, y0 + 0.04]
        self.assertEqual(len(recheck.dodge_clear_errors(s)), 1)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.dodge_clear_errors(gibeah()), [])

    def test_object_far_above_fails(self):
        """b3: 창이 한참 위로 지나면 「겨누지도 않음」 — 피함은 아슬아슬한 빗나감이어야."""
        s = gibeah()
        y0 = s["regions"]["david-youth"][1]
        s["regions"]["spear"] = [0.09, y0 - 0.2, 0.34, y0 - 0.17]
        self.assertEqual(len(recheck.dodge_clear_errors(s)), 1)


class FlightHeight(unittest.TestCase):
    """generate.flight-height — 나는 물체 높이 = 던지는 뼈대 어깨(task 412, 사람 m16e 「던질 때 팔의 높이」)."""

    def test_gibeah_passes(self):
        self.assertEqual(recheck.flight_height_errors(gibeah()), [])

    def test_spear_at_hand_height_fails(self):
        s = gibeah()
        s["regions"]["spear"][1], s["regions"]["spear"][3] = 0.478, 0.503   # m16e — 던진 손목과 어깨 사이
        self.assertEqual(len(recheck.flight_height_errors(s)), 1)

    def test_no_flight_needs_nothing(self):
        s = gibeah()
        s["guide"].pop("flight")
        self.assertEqual(recheck.flight_height_errors(s), [])

    def test_near_miss_is_one_head(self):
        """빗나감 한도 = 피하는 사람 머리 하나(기준표 youth 0.1429 × 구역 키) — 옛 고정 0.05를 대신함."""
        import scale as S
        s = gibeah()
        y0, y1 = s["regions"]["david-youth"][1], s["regions"]["david-youth"][3]
        self.assertAlmostEqual(recheck._near_miss(s, "david-youth"), S.head_ratio("youth") * (y1 - y0))


class GuideCostumeLegs(unittest.TestCase):
    """generate.guide-costume-legs — 무릎 길이 차림이면 가이드 꼴에 무릎 아래 다리."""

    def test_knee_costume_without_legs_fails(self):
        s = gibeah()
        s["guide"].pop("legs")
        self.assertEqual(len(recheck.guide_legs_errors(s)), 1)

    def test_long_costume_needs_nothing(self):
        s = gibeah()
        s["guide"].pop("legs")
        for f in s["figures"]:
            f["costume"]["en"] = f["costume"]["en"].replace("knee-length", "ankle-length")
        self.assertEqual(recheck.guide_legs_errors(s), [])

    def test_gibeah_passes(self):
        self.assertEqual(recheck.guide_legs_errors(gibeah()), [])


class YouthNoun(unittest.TestCase):
    """derive.youth-noun — youth(15~20) 인물은 파생 명사가 young man, child만 boy(task 403 r4)."""

    def test_who_by_age_class(self):
        import derive_scene as ds
        c = {"era": "an ancient Israelite", "sex": "male", "card": {"ageBand": {"class": "youth"}}}
        self.assertEqual(ds._who(c), "an ancient Israelite young man")
        c["card"]["ageBand"]["class"] = "child"
        self.assertEqual(ds._who(c), "an ancient Israelite boy")
        c["sex"], c["card"]["ageBand"]["class"] = "female", "youth"
        self.assertEqual(ds._who(c), "an ancient Israelite young woman")

    def test_boy_in_prompt_with_youth_fails(self):
        import derive_scene as ds
        with mock.patch.object(ds, "route_prompt", return_value="an ancient Israelite boy, a commander"):
            self.assertEqual(len(recheck.youth_noun_errors(gibeah())), 1)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.youth_noun_errors(gibeah()), [])

    def _with_youth_age(self, text):
        import derive_scene as ds
        s = gibeah()
        f = next(f for f in s["figures"] if f["cast"] == "david-youth")
        card = copy.deepcopy(ds.load_cast("david-youth")["card"])
        card["ageBand"]["text"] = text
        f["cast_override"] = {**f.get("cast_override", {}), "card": card}
        return s

    def test_under_15_allows_boy(self):
        """task 419 — boy 금지는 카드 나이 15세 이상만(14세 david-boy는 삼상 17:33 「너는 소년이요」)."""
        import derive_scene as ds
        with mock.patch.object(ds, "route_prompt", return_value="an ancient Israelite boy"):
            self.assertEqual(recheck.youth_noun_errors(self._with_youth_age("about 14, smooth round cheeks")), [])
            self.assertEqual(len(recheck.youth_noun_errors(self._with_youth_age("about 15, smooth face"))), 1)

    def test_unreadable_age_not_measured(self):
        self.assertIsNone(recheck.youth_noun_errors(self._with_youth_age("a smooth youthful face")))


class PoseSkeleton(unittest.TestCase):
    """generate.pose-skeleton — 몸짓에 던짐 동사가 있는 인물은 guide.pose 뼈대(task 403 c7)."""

    def test_thrower_without_pose_fails(self):
        s = gibeah()
        s["guide"].pop("pose")
        self.assertEqual(len(recheck.pose_skeleton_errors(s)), 1)

    def test_no_throw_needs_nothing(self):
        s = gibeah()
        s["guide"].pop("pose")
        for f in s["figures"]:
            f["gesture"]["ko"] = "벽 앞에 서서 수금을 탐"
        self.assertEqual(recheck.pose_skeleton_errors(s), [])

    def test_gibeah_passes(self):
        self.assertEqual(recheck.pose_skeleton_errors(gibeah()), [])


class FigureScale(unittest.TestCase):
    """generate.figure-scale — 가까운 장면의 인물 구역은 무리 단계 범위 안(task 403 d1 · task 409 — 독대 0.60~0.70)."""

    def test_small_figure_fails(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = 0.46
        self.assertEqual(len(recheck.figure_scale_errors(s)), 1)

    def test_crowd_scene_uses_stage(self):
        """task 409 — 무리 꼴이 있다고 건너뛰지 않고 장면 사람 수의 무리 단계 범위로 잰다: 무리 10명(작은 무리 0.45~0.60)이면 사울 0.68은 너무 가깝다."""
        s = gibeah()
        s["guide"]["shape"]["wall"] = "crowd"
        s["crowds"] = [{"count": 10}]
        errs = recheck.figure_scale_errors(s)
        self.assertTrue(any(e.startswith("saul:") and "small" in e for e in errs), errs)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.figure_scale_errors(gibeah()), [])


class SecondPoint(unittest.TestCase):
    """derive.no-second-point — 그리는 사전 문구에 pointed·spike 없음(task 403 d1, c14 s5 뒤끝 화살촉)."""

    def test_pointed_butt_fails(self):
        words = {"words": [{"id": "spear", "look": {"L2": {"en": "one large point at the front and a short pointed iron butt-spike"}}}]}
        with mock.patch.object(recheck.ds, "route_prompt", return_value="x, one large point at the front and a short pointed iron butt-spike, y"), \
                mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(words))):
            self.assertEqual(len(recheck.second_point_errors(gibeah_cached)), 1)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.second_point_errors(gibeah()), [])


class ObjectCrisp(unittest.TestCase):
    """generate.object-crisp — 허공 물체 꼴은 흐림 뒤에 또렷하게(task 403 d2 — d1 흐린 촉 → 창 방향 뒤집힘·화살촉)."""

    def test_spear_tip_not_blurred(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        s = gibeah()
        s["guide"].pop("control", None), s["guide"].pop("split", None)   # 깊이 모드 규칙(h1부터 기브아는 스텝별 — 다른 장면은 깊이 한 장)
        v = round(255 * s["guide"]["depth"]["spear"])
        x0, y0, x1, y1 = (round(a * d) for a, d in zip(s["regions"]["spear"], (M.W, M.H, M.W, M.H)))
        tip = M.make(s).crop((x0, y0 - 20, x0 + (x1 - x0) // 3, y1 + 20)).convert("L")
        self.assertGreater(sum(1 for px in tip.getdata() if px == v), 100)   # 흐리면 같은 값 화소가 거의 없음

    def test_air_shapes_agree(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        self.assertEqual(M.AIR_SHAPES, recheck.AIR_SHAPES)


class SmallPropEdit(unittest.TestCase):
    """edit.small-prop-orient — 작은 허공 지물 편집 상자는 명세 구역에서(사람 눈 아님), 지시는 사전 문구 + 왼쪽 촉(task 403 d3e)."""

    def test_box_is_back_end_of_region(self):
        import gen_local_edit as GL
        x0, y0, x1, y1 = gibeah()["regions"]["spear"]
        (L, T, side), box = GL.prop_box([x0, y0, x1, y1], 1216, 640)
        self.assertGreaterEqual(box[0], (x0 + x1) / 2 * 1216 - 1)                 # 뒤끝(오른쪽 반)만
        self.assertGreaterEqual(box[2], (x1 + 0.08) * 1216)                       # 생성은 구역보다 길게(d3 창 오른끝 515 vs 구역 413)
        self.assertTrue(box[1] <= y0 * 640 - 15 and box[3] >= y1 * 640 + 15)      # 세로 여유
        self.assertTrue(L <= box[0] and T <= box[1] and L + side >= box[2] and T + side >= box[3] and L + side <= 1216 and T + side <= 640)
        self.assertLess(side, 400)                                                             # 작은 크롭

    def test_front_box_is_front_end(self):
        import gen_local_edit as GL
        s = gibeah()
        x0, _, x1, _ = s["regions"]["spear"]
        (L, T, side), box = GL.prop_box([x0, 0.5, x1, 0.52], 1216, 640, "front")
        self.assertTrue(box[0] <= x0 * 1216 and box[2] <= (x0 + x1) / 2 * 1216 + 1)   # 창 왼끝 ~ 가운데
        self.assertGreaterEqual(box[0], round((x0 - GL.PROP_PAD_FRONT) * 1216) - 1)  # d4e: 바깥 여유는 PROP_PAD_FRONT만(벽 안으로 안 들어감)
        (L, T, side), box = GL.prop_box([0.105, 0.5, 0.34, 0.52], 1216, 640, "front")
        self.assertGreaterEqual(box[0], round(0.09 * 1216))                          # 벽 옆 창(d4e 자리)도 벽 구역(0~0.09) 밖

    def test_front_prompt_uses_lexicon_head(self):
        import gen_local_edit as GL
        p = GL.prop_prompt("a straight wooden shaft with one large leaf-shaped iron point at the front and a small iron cap", "front")
        self.assertIn("large leaf-shaped iron point", p)
        self.assertIn("left end", p)
        self.assertNotIn("right end", p)
        self.assertIn("no", p.lower())
        self.assertIn("crossguard", p)                       # d4e: 날개·코등이 금지를 말함
        self.assertIn("no barbs", p)                         # f6e: 잎 모양을 꼴로 풀어 말함(미늘 화살촉 방지)
        self.assertIn("widest in the middle", p)
        self.assertIn("grey iron blade", p)                  # f6e2: 재질을 말하지 않으면 푸른 진짜 잎

    def test_prompt_one_instruction_no_boy(self):
        import gen_local_edit as GL
        p = GL.prop_prompt("one large leaf-shaped iron point at the front and a small iron cap on the back end")
        self.assertIn("right end", p)
        self.assertNotIn("left", p)              # 지시 하나(뒤끝만)
        self.assertNotRegex(p, r"\bboy\b")
        self.assertNotIn("the people", p)        # d3e2: 크롭 밖 사람을 말하면 창 쥔 사람을 그림
        self.assertIn("no person", p)

class GuideHeadRatio(unittest.TestCase):
    """generate.guide-head-ratio — 가이드 사람 꼴 머리 지름 ≤ 구역 높이 × 0.14(task 403 d4 — 숙인 꼴 0.18은 선 꼴로 옮겨져 아이 비율)."""

    def test_head_diameter(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        self.assertEqual(set(M.HEAD_R), {"person", "person_duck"})
        for name, r in M.HEAD_R.items():
            self.assertLessEqual(2 * r, 0.14, name)

class YouthHeight(unittest.TestCase):
    """generate.youth-height — 청년 구역 높이 ≥ 같은 장면 어른 × 0.8(task 403 d5)."""

    def test_small_youth_fails(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = s["regions"]["david-youth"][3] - 0.7 * (s["regions"]["saul"][3] - s["regions"]["saul"][1])   # 어른의 0.7
        self.assertEqual(len(recheck.youth_height_errors(s)), 1)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.youth_height_errors(gibeah()), [])


class SingleImageReps(unittest.TestCase):
    """judge.single-image-reps — 한 장 시도(시드 하나, 새 그림)는 5표(task 404 f1e·f2e: 거의 같은 그림이 3표로 수금·던진 몸짓 뒤집힘)."""

    def test_f_attempts_ask_five(self):
        import re
        t = open(os.path.join(HERE, "notes", "GIBEAH-STEP23.md"), encoding="utf-8").read()
        for k, j in re.findall(r"```json fixed (f\d+e?\d*)\n(.*?)\n```", t, re.S):
            fx = json.loads(j)
            if len(fx["seeds"]) == 1 and not fx.get("images_from"):
                self.assertGreaterEqual(fx["reps"], 5, k)


class PoseHold(unittest.TestCase):
    """generate.pose-hold(폐기 2026-10-23 f5) — 뼈대 꼴 duck_clutch만 남김: 두 손목이 가슴에 모임(다시 쓸 때를 위해)."""

    def test_duck_clutch_wrists_at_chest(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        p = M.POSES["duck_clutch"]
        for w in (4, 7):
            self.assertTrue(p[1][1] < p[w][1] < p[8][1])
        self.assertLess(abs(p[4][0] - p[7][0]), 0.06)


class PoseSkirt(unittest.TestCase):
    """generate.guide-costume-legs(뼈대 인물에도, task 404 f4) — 무릎 길이 차림이면 뼈대 몸에 엉덩이 ~ 무릎 치마 덩어리."""

    def test_knee_skirt_adds_mass_between_legs(self):
        import sys
        from PIL import Image, ImageDraw
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        def between_legs(knee):   # 엉덩이 가운데 바로 아래(두 넓적다리 사이)가 차는가
            img = Image.new("L", (400, 600), 0)
            M.pose_body(ImageDraw.Draw(img), (50, 0, 350, 600), "throw_follow", 255, 0.4, knee)
            pts, h = M.pose_points((50, 0, 350, 600), "throw_follow")
            hx, hy = (pts[8][0] + pts[11][0]) / 2, (pts[8][1] + pts[11][1]) / 2
            ky = (pts[9][1] + pts[12][1]) / 2
            return img.getpixel((round(hx), round(hy + (ky - hy) * 0.7)))
        self.assertTrue(between_legs(True))
        self.assertFalse(between_legs(False))


class DodgeClearPose(unittest.TestCase):
    """generate.dodge-clear — 뼈대 인물은 뼈대의 실제 머리 자리로 잼(task 404 f4)."""

    def test_spear_far_above_skeleton_head_fails(self):
        s = gibeah()
        s["guide"]["pose"]["david-youth"] = "duck_clutch"   # 숙인 뼈대 머리는 구역 위끝보다 아래
        self.assertEqual(len(recheck.dodge_clear_errors(s)), 1)

class PoseOnlyControl(unittest.TestCase):
    """generate.pose-only-control(폐기 2026-10-23 g2e) — make_pose_only만 남김: control pose면 깊이 회색 없이 뼈대 + 허공 물체."""

    def test_pose_only_guide_has_no_depth_grey(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        s = gibeah()
        s["guide"]["control"] = "pose"
        px = list(M.make(s).getdata())
        grey = sum(1 for r, g, b in px if r == g == b and 20 < r < 235)
        color = sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) > 60)
        self.assertLess(grey, 0.002 * len(px))
        self.assertGreater(color, 500)

class SplitControl(unittest.TestCase):
    """generate.split-control — 뼈대 가이드는 스텝별: 1단계 뼈대만(깊이 회색 없음), 2단계 깊이(뼈대 색 없음, 몸 덩어리 있음)(task 404 h1)."""

    def test_pose_without_split_fails(self):
        s = gibeah()
        s["guide"].pop("split")
        self.assertEqual(len(recheck.split_control_errors(s)), 1)

    def test_stages(self):
        """1단계 = 방 바탕 + 뼈대(사람 깊이 몸 없음, m4) · 2단계 = 깊이(뼈대 색 없음, 몸 덩어리 있음)."""
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        s = gibeah()
        one, two = M.make(s, 1), M.make(s, 2)
        color = lambda px: sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) > 60)
        x0, y0, x1, y1 = (round(v * d) for v, d in zip(s["regions"]["saul"], (M.W, M.H, M.W, M.H)))
        body = lambda im: sum(1 for r, g, b in im.crop((x0, y0, x1, y1)).getdata() if r == g == b and r > 230)
        self.assertGreater(color(list(one.getdata())), 500)
        self.assertLess(body(one), 0.02 * (x1 - x0) * (y1 - y0))        # 1단계엔 사울 깊이 몸 없음
        self.assertGreater(body(two), 0.05 * (x1 - x0) * (y1 - y0))     # 2단계엔 있음
        self.assertEqual(color(list(two.getdata())), 0)
        grey = sum(1 for r, g, b in one.getdata() if r == g == b and 20 < r < 235)
        self.assertGreater(grey, 0.3 * M.W * M.H)                        # 1단계에도 방 바탕(m4 — 검은 바탕 액자 방지)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.split_control_errors(gibeah()), [])


class HeldPropEdit(unittest.TestCase):
    """edit.small-prop-orient(쥔 지물로 넓힘, task 404 h2) — 상자는 뼈대 두 손목 가운데에서, 지시는 사전 L2 + 손 유지."""

    def test_box_around_wrists(self):
        import gen_local_edit as GL
        (L, T, side), box = GL.held_box([(0.2, 0.5), (0.22, 0.52)], 1216, 640)
        self.assertTrue(box[0] < 0.21 * 1216 < box[2] and box[1] < 0.51 * 640 < box[3])
        self.assertLess(box[2] - box[0], 0.2 * 1216)   # 작은 크롭(큰 부위 아님)

    def test_prompt_keeps_hands(self):
        import gen_local_edit as GL
        p = GL.held_prompt("a hollow wooden sound box with two curved arms joined by a crossbar")
        self.assertIn("crossbar", p)
        self.assertIn("Keep his hands", p)
        self.assertIn("Remove the long neck", p)              # h2e2: 목을 없애는 것이 지시의 머리
        self.assertIn("U-shaped frame", p)                    # n1: 두 팔이 다 보이는 틀(m1e 「다윗 악기가 맞나?」)

    def test_rect_mask_covers_spear_end(self):
        """h2e2: 둥근 사각 마스크는 상자 끝(창 촉 자리)까지 덮음 — 타원은 끝이 좁아 원본 촉이 남음."""
        import gen_local_edit as GL
        crop, box = (0, 0, 400), (50, 180, 350, 220)
        for shape, full in (("rect", True), ("ellipse", False)):
            m = GL.mask(crop, box, shape)
            self.assertEqual(m.getpixel((345, 214)) > 200, full, shape)   # 오른끝 아래 모서리 가까이


class FigureScalePose(unittest.TestCase):
    """generate.figure-scale(뼈대 보강, task 404 h4) — 뼈대 인물은 보이는 키(머리 꼭대기 ~ 발) ≥ 0.55."""

    def test_small_crouch_fails(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = s["regions"]["david-youth"][3] - 0.55   # 보이는 키 0.43 < 0.45
        self.assertTrue(any("david-youth" in e for e in recheck.figure_scale_errors(s)))

    def test_gibeah_passes(self):
        self.assertEqual(recheck.figure_scale_errors(gibeah()), [])


    def test_too_big_fails(self):
        """n1(사람 m1e 「사람사이즈를 조금 줄여야」) — 구역 높이 0.70 위 한도."""
        s = gibeah()
        s["regions"]["saul"][1] = s["regions"]["saul"][3] - 0.84   # m1e 크기
        self.assertTrue(any("saul" in e and "가깝게" in e for e in recheck.figure_scale_errors(s)))


class FlightPosition(unittest.TestCase):
    """generate.flight-position — 촉은 guide.flight 지점, 그려질 뒤끝(사전 크기 × 던지는 사람 키)은 손목 앞(task 405 — 사람 「창은 3분의2쯤」 일반화)."""

    def test_spear_at_head_fails(self):
        s = gibeah()
        s["regions"]["spear"] = [0.105, 0.478, 0.34, 0.503]   # m1e처럼 머리 위까지 날아옴
        self.assertTrue(recheck.flight_errors(s))

    def test_missing_flight_fails(self):
        s = gibeah()
        s["guide"].pop("flight")
        self.assertEqual(len(recheck.flight_errors(s)), 1)

    def test_people_too_close_fails(self):
        s = gibeah()
        s["regions"]["saul"] = [0.56, 0.12, 0.78, 0.98]   # 크고 가까운 사울(m1e) — 사전 크기 창이 손에 남음
        self.assertTrue(any("손목" in e or "지점" in e for e in recheck.flight_errors(s)))

    def test_gibeah_passes(self):
        self.assertEqual(recheck.flight_errors(gibeah()), [])

    def test_thrower_holding_thrown_prop_fails(self):
        """task 399 회고 — 던진 창을 사울 prop(「a spear」)으로 두면 손에 남은 꼴로 그려지고 판정자도 속음 → prop none."""
        s = gibeah()
        next(f for f in s["figures"] if f["region"] == "saul")["prop"] = "a spear"
        self.assertTrue(any("던진 지물" in e for e in recheck.flight_errors(s)))

    def test_butt_divides_by_height_class(self):
        """task 411 — 사전 비는 어른 남자 키 비: 큰 사울(tall)의 창은 구역 키 ÷ 1.205(합성 paste_step과 같은 셈). 등급을 빼면 뒤끝이 손에 닿음."""
        from unittest import mock
        s = gibeah()
        with mock.patch.object(recheck.S, "standing", lambda spec: [("saul", 1.0)]):
            self.assertTrue(any("손목" in e for e in recheck.flight_errors(s)))


class WidenUnmeasured(unittest.TestCase):
    """task 413 — 걸릴 내용(사람·청년·무리·허공 물체)이 있는데 잴 칸(guide 구역·던지는 뼈대)이 없으면 빈 통과가 아니라 못 잼(None)·실패."""

    def test_no_guide_people_is_unmeasured(self):
        import derive_scene as ds
        s = copy.deepcopy(ds.load("authored-david-goliath-gath"))   # 사람 3 · 청년 다윗 · 무리 2
        s.pop("guide", None)   # task 415 회고: 살아 있는 명세가 재저작되어도 「guide 없음」을 사본으로 고정
        for f in (recheck.figure_scale_errors, recheck.youth_height_errors, recheck.height_ratio_errors, recheck.perspective_errors):
            self.assertIsNone(f(s), f.__name__)

    def test_no_people_is_not_applicable(self):
        s = gibeah()
        s.pop("guide")
        s["figures"], s["crowds"] = [], []
        for f in (recheck.figure_scale_errors, recheck.youth_height_errors, recheck.height_ratio_errors, recheck.perspective_errors):
            self.assertEqual(f(s), [], f.__name__)

    def test_spear_shape_without_thrower_fails(self):
        s = gibeah()
        s["guide"]["pose"] = {k: v for k, v in s["guide"]["pose"].items() if v != "throw_follow"}
        self.assertTrue(any("던지는 뼈대" in e for e in recheck.flight_errors(s)))


class SeatedHeight(unittest.TestCase):
    """generate.seated-height — 앉은 꼴(sit) 인물 구역 높이 = 지평선에서 셈한 서 있는 화면 키 × 키 등급 × body.seated(task 414 기브아 수금 사울)."""

    def harp(self):
        import derive_scene as ds
        return copy.deepcopy(ds.load("authored-david-gibeah-harp"))

    def test_harp_passes(self):
        self.assertEqual(recheck.seated_height_errors(self.harp()), [])

    def test_seated_as_tall_as_standing_fails(self):
        s = self.harp()
        s["regions"]["saul"][1] = s["regions"]["saul"][3] - 0.70   # 앉았는데 서 있는 사울 키만큼
        self.assertTrue(any("saul" in e for e in recheck.seated_height_errors(s)))

    def lone(self, top):
        """수금 사본에서 다윗을 빼고 앉은 사울만 — 홀로 앉은 사람 장면(task 416 밧세바 꼴)."""
        s = self.harp()
        s["figures"] = [f for f in s["figures"] if f["region"] == "saul"]
        del s["guide"]["shape"]["david-boy"]
        s["regions"]["saul"][1] = top
        return s

    def test_no_standing_uses_seated_focus(self):
        """task 416 — 서 있는 사람이 없으면 못 잼(옛 기대)이 아니라 앉은 초점의 서 있을 때 키로 지평선을 정해 잼."""
        s = self.harp()
        s["guide"]["shape"]["david-boy"] = "sit"
        self.assertIsInstance(recheck.seated_height_errors(s), list)
        self.assertNotEqual(recheck.S.scene_horizon(s), recheck.S.v("perspective.horizon_default"))

    def test_lone_seated_scale(self):
        """task 416 — 홀로 앉은 사람: 견줄 이가 없어 seated-height 통과, 크기는 figure-scale이 서 있을 때 키(구역 ÷ body.seated)를 독대 범위로 잼."""
        foot = self.harp()["regions"]["saul"][3]
        ok, near = self.lone(foot - 0.49), self.lone(foot - 0.64)   # 0.49 ÷ 0.75 = 0.65 · 0.64 ÷ 0.75 = 0.85 > 0.70
        self.assertEqual(recheck.seated_height_errors(ok), [])
        self.assertEqual(recheck.figure_scale_errors(ok), [])
        self.assertTrue(any(e.startswith("saul:") for e in recheck.figure_scale_errors(near)))

    def test_shape_registered(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch"))
        import make_guide as M
        self.assertLessEqual(recheck.SEATED_SHAPES, set(M.SHAPES))


class HeldHold(unittest.TestCase):
    """derive.held-hold — 쥔 꼴은 사전 look.hold가 정본(task 413): 수금 hug 편집 지시는 승인 m17e s7과 바이트 같고, 아기 hug는 수금 문구가 섞이지 않음."""

    M17E_S7 = "Place a wooden lyre in his arms, nearly twice as tall as his head, clutched upright against his chest with both forearms wrapped around its sound box, its top crossbar below his chin, not touching his mouth or face: a small hollow wooden sound box, smaller than a man's torso, with two curved arms rising from the box, joined by a top crossbar, strings from box to crossbar, the two curved arms rising on the left and right of the sound box both clearly visible above his forearms, forming a U-shaped frame. It does not hang from his hands. Only one lyre. Keep his face, hair, clothes, body and legs exactly the same — only his arms and hands may move to hold the lyre — the lighting and the same soft pencil and colored-pencil illustration style."

    def test_lyre_hug_reproduces_m17e(self):
        import gen_local_edit as GL
        import scale as S
        look = recheck._lexicon()["kinnor-lyre"]["look"]
        hr = dict(S.standing(gibeah()))["david-youth"]
        p = GL.held_prompt(look["L2"]["en"], look["hold"]["mode"], GL.held_head_en(look["size"], "youth", hr), look["hold"])
        self.assertEqual(p, self.M17E_S7)

    def test_baby_hug_has_no_lyre(self):
        import gen_local_edit as GL
        look = recheck._lexicon()["baby"]["look"]
        p = GL.held_prompt(look["L2"]["en"], look["hold"]["mode"], "about as long as his forearm", look["hold"])
        self.assertIn(look["hold"]["en"], p)
        self.assertNotIn("lyre", p)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.held_hold_errors(gibeah()), [])

    def test_missing_hold_fails(self):
        L = copy.deepcopy(recheck._lexicon())
        L["spear"]["look"].pop("hold")
        with mock.patch.object(recheck, "_lexicon", lambda: L):
            self.assertTrue(any("spear" in e for e in recheck.held_hold_errors(gibeah())))

    def test_hug_prop_without_hold_phrase_fails(self):
        import derive_scene as ds
        s = copy.deepcopy(ds.load("authored-solomon-jerusalem-two-mothers"))   # prop 「an infant」 — 사전 baby hug
        g = s["figures"][2]["gesture"]   # task 415 재저작으로 명세는 통과 — 품에 안은 꼴 문구를 지운 사본으로 잰다
        g["en"] = g["en"].replace(", cradled in both arms against the chest", "")
        self.assertTrue(any("baby" in e for e in recheck.held_hold_errors(s)))


class PropSizeRelative(unittest.TestCase):
    """derive.prop-size-relative — 장면이 잇는 사전 지물은 look.size가 있고 L2에 크기 문구(task 405 — 사람 「사람을 줄였으면 창도 줄여야」)."""

    def test_missing_size_fails(self):
        words = recheck._lexicon()
        words["spear"]["look"].pop("size")
        with mock.patch.object(recheck, "_lexicon", return_value=words):
            self.assertTrue(any("spear" in e for e in recheck.prop_size_errors(gibeah())))

    def test_size_phrase_not_in_l2_fails(self):
        words = recheck._lexicon()
        words["spear"]["look"]["size"]["parts"]["point"]["en"] = "as big as a head"
        with mock.patch.object(recheck, "_lexicon", return_value=words):
            self.assertTrue(any("as big as a head" in e for e in recheck.prop_size_errors(gibeah())))

    def test_gibeah_passes(self):
        self.assertEqual(recheck.prop_size_errors(gibeah()), [])

class EditBoxClearOfBody(unittest.TestCase):
    """edit.small-prop-orient(m3) — 편집 상자는 오른쪽 뼈대 인물 몸 앞에서 끝남(m2e 창 뒤끝 편집이 사울 팔을 흐림)."""

    def test_xmax_clips_back_box(self):
        import gen_local_edit as GL
        (_, _, _), box = GL.prop_box([0.413, 0.48, 0.648, 0.5], 1216, 640, "back", None, 0.70)
        self.assertLessEqual(box[2] + 20, round(0.70 * 1216))   # 마스크(+20px)까지 몸 앞
        (_, _, _), box = GL.prop_box([0.413, 0.48, 0.648, 0.5], 1216, 640, "back")
        self.assertGreater(box[2], round(0.70 * 1216))           # 자르지 않으면 넘어감(m2e)


class EmptyHandOpen(unittest.TestCase):
    """derive.empty-hand-open — 빈손 몸짓 인물의 파생 문구에 주먹 낱말이 없음(task 405 m2e~m5e 던진 몸짓 틀림 52표 중 「주먹」 47)."""

    def test_curled_hand_fails(self):
        import derive_scene as ds
        with mock.patch.object(ds, "route_prompt", return_value="his empty throwing arm swinging down, his hand loosely curled"):
            self.assertEqual(len(recheck.empty_hand_fist_errors(gibeah())), 1)

    def test_no_empty_hand_needs_nothing(self):
        import derive_scene as ds
        g = gibeah()
        for f in g["figures"]:
            f["gesture"]["ko"] = f["gesture"]["ko"].replace("빈손", "")
        with mock.patch.object(ds, "route_prompt", return_value="a clenched fist"):
            self.assertEqual(recheck.empty_hand_fist_errors(g), [])

    def test_gibeah_passes(self):
        self.assertEqual(recheck.empty_hand_fist_errors(gibeah()), [])


class HeldPropAdd(unittest.TestCase):
    """edit.held-prop-add — 쥔 지물은 바탕 문구에서 빼고 편집으로 넣음(task 405 m6·m7 바탕 류트 약 6/8 → 목·줄감개가 편집 밖에 남음)."""

    def test_strip_held_removes_lyre_clause(self):
        import derive_scene as ds
        import gen_local_edit as GL
        words = recheck._lexicon()
        look = words["kinnor-lyre"]["look"]
        p = GL.strip_held(ds.route_prompt(gibeah()), look["L1"]["en"], look["L2"]["en"], "his empty hands clasped in front of his chest")
        self.assertNotIn("lyre", p.lower())
        self.assertIn("his empty hands clasped in front of his chest", p)
        self.assertIn("standing with his back against the stone wall", p)

    def test_add_mode_places_instrument(self):
        import gen_local_edit as GL
        self.assertTrue(GL.held_prompt("x", "add").startswith("Place a small wooden lyre"))
        self.assertTrue(GL.held_prompt("x").startswith("Remove the long neck"))


class NoInflatingBuild(unittest.TestCase):
    """derive.no-inflating-build — 거인 아닌 인물 체격 문구에 barrel·massive·huge 없음(task 405 m8e 사람 「사울 비율」)."""

    def test_barrel_fails(self):
        import derive_scene as ds
        with mock.patch.object(ds, "route_prompt", return_value="broad shoulders, thick barrel torso"):
            self.assertEqual(len(recheck.inflating_build_errors(gibeah())), 1)

    def test_gibeah_passes(self):
        self.assertEqual(recheck.inflating_build_errors(gibeah()), [])


class EditSizeInCrop(unittest.TestCase):
    """edit.size-in-crop — 앞 촉 편집 지시의 크기는 사전 parts.point.edit_en(크롭 안 자루에 견줌), 손에 견주지 않음(m8e 「창촉이 큰것 같음」)."""

    def test_front_prompt_uses_shaft_size(self):
        import gen_local_edit as GL
        look = recheck._lexicon()["spear"]["look"]
        part = look["size"]["parts"]["point"]["edit_en"]
        p = GL.prop_prompt(look["L2"]["en"], "front", part)
        self.assertIn("as wide as the wooden shaft", p)
        self.assertNotIn("wider than a hand", p)

    def test_paint_tip_sizes_from_measured_spear(self):
        import tempfile
        from PIL import Image, ImageDraw
        import gen_local_edit as GL
        im = Image.new("RGB", (1216, 640), (236, 226, 200))
        ImageDraw.Draw(im).line([(500, 320), (840, 320)], fill=(150, 100, 60), width=8)
        ImageDraw.Draw(im).polygon([(500, 320), (540, 290), (590, 320), (540, 350)], fill=(120, 120, 120))   # 머리만 한 큰 촉
        d = tempfile.mkdtemp()
        src, out = os.path.join(d, "s.png"), os.path.join(d, "p.png")
        im.save(src)
        m = GL.measure_prop(src, [0.423, 0.478, 0.662, 0.503], 1216, 640, 0.70)
        self.assertEqual(m[0], 500)
        box = GL.paint_tip(src, out, m, 0.12, 2.0, 1216, 640)
        self.assertLessEqual(box[0], 500)
        self.assertGreaterEqual(box[2], 590)                 # 옛 큰 촉 자리를 지움
        p = Image.open(out).convert("RGB")
        self.assertTrue(all(abs(a - b) <= 3 for a, b in zip(p.getpixel((560, 300)), (236, 226, 200))))   # 큰 촉 위쪽은 벽 색으로 지워짐
        self.assertNotEqual(p.getpixel((520, 320)), (236, 226, 200))        # 작은 촉(길이 340 × 0.12 ≈ 41)은 칠해짐

    def test_paint_cap_only_when_spear_ends_apart(self):
        import tempfile
        from PIL import Image, ImageDraw
        import gen_local_edit as GL
        im = Image.new("RGB", (1216, 640), (236, 226, 200))
        ImageDraw.Draw(im).line([(500, 320), (800, 320)], fill=(150, 100, 60), width=8)
        ImageDraw.Draw(im).polygon([(790, 312), (820, 320), (790, 328)], fill=(120, 120, 120))   # 뾰족한 뒤끝
        d = tempfile.mkdtemp()
        src, out = os.path.join(d, "s.png"), os.path.join(d, "p.png")
        im.save(src)
        m = GL.measure_prop(src, [0.423, 0.478, 0.662, 0.503], 1216, 640, 0.80)
        self.assertTrue(m[5]["sep"])
        box = GL.paint_cap(src, out, m, 0.035, 1.4, 1216, 640)
        self.assertIsNotNone(box)
        p = Image.open(out).convert("RGB")
        self.assertTrue(all(abs(a - b) <= 3 for a, b in zip(p.getpixel((818, 320)), (236, 226, 200))))   # 뾰족한 끝은 지워짐
        ImageDraw.Draw(im).line([(800, 320), (980, 320)], fill=(150, 100, 60), width=8)                   # 오른쪽 인물과 이어짐
        im.save(src)
        self.assertIsNone(GL.paint_cap(src, out, GL.measure_prop(src, [0.423, 0.478, 0.662, 0.503], 1216, 640, 0.80), 0.035, 1.4, 1216, 640))


class EditPropSheetPaste(unittest.TestCase):
    """edit.prop-sheet-paste — 작은 허공 지물은 빈 종이 한 장에 사전 부위 크기 가이드로 따로 그려 단면으로 고르고, 기준표 길이로 줄여 곱하기 합성(task 407 r22 —
    장면 안에서는 촉 크기를 가이드·끝 편집으로 못 맞춤: m13 촉 창의 0.2·뒤집힘 3/8, m11e 이음매·스티커)."""

    def parts(self):
        return recheck._lexicon()["spear"]["look"]["size"]["parts"]

    def sheet(self, parts):
        import tempfile
        from PIL import ImageOps
        import gen_local_edit as GL
        p = os.path.join(tempfile.mkdtemp(), "s.png")
        ImageOps.invert(GL.sheet_guide(parts)).convert("RGB").save(p)   # 종이 위 어두운 창 꼴
        return p

    def test_lexicon_sheet_measures_lexicon_parts(self):
        import gen_local_edit as GL
        score, m = GL.sheet_measure(self.sheet(self.parts()), self.parts())
        self.assertIsNotNone(score, m)
        self.assertAlmostEqual(m["tip"], self.parts()["point"]["ratio"], delta=0.03)
        self.assertAlmostEqual(m["tip_w"], self.parts()["point"]["width"], delta=0.2)

    def test_big_tip_sheet_fails(self):
        import copy
        import gen_local_edit as GL
        big = copy.deepcopy(self.parts())
        big["point"].update(ratio=0.3, width=4.0)   # m9 바탕 가이드 leaf 촉 크기
        score, m = GL.sheet_measure(self.sheet(big), self.parts())
        self.assertIsNone(score)
        self.assertIn("tip", m["why"])

    def test_paste_changes_only_its_box(self):
        import numpy as np
        import gen_local_edit as GL
        sheet = self.sheet(self.parts())
        _, sm = GL.sheet_measure(sheet, self.parts())
        a = np.full((640, 1216, 3), (236, 226, 200), np.uint8)
        b = a.copy()
        box = GL.paste_prop(b, sheet, sm, (514, 314), 242)
        out = np.ones((640, 1216), bool)
        out[box[1]:box[3], box[0]:box[2]] = False
        self.assertTrue((a[out] == b[out]).all())                       # 상자 밖 그대로
        row = (b[314].astype(int).sum(axis=1) < 600).nonzero()[0]
        self.assertAlmostEqual(row[0], 514, delta=3)                      # 촉 끝이 명세 자리
        self.assertAlmostEqual(row[-1] - row[0], 242, delta=4)            # 기준표 길이

    def test_tail_stop_before_arm(self):
        import numpy as np
        import gen_local_edit as GL
        a = np.full((640, 1216, 3), (236, 226, 200), np.uint8)
        a[311:318, 500:900] = (150, 100, 60)       # 손 앞 경계(820) 너머로 이어진 자루
        a[290:345, 950:1000] = (200, 140, 110)     # 띠를 덮는 팔
        m = (500, 820, 314.5, 7, 14.0, {"sep": False})
        self.assertLessEqual(GL._tail_stop(a, m, 1216, 294, 335), 905)

    def test_strip_air_keeps_empty_hand(self):
        """r23 — 바탕 문구에서 창 구절만 빠지고 빈손·몸짓 문구(derive.empty-hand-open)는 남음."""
        import derive_scene as ds
        import gen_local_edit as GL
        p = GL.strip_air(ds.route_prompt(gibeah()), "spear")
        self.assertNotIn("spear", p)
        self.assertIn("his fingers open and spread", p)
        self.assertIn("his empty throwing arm", p)
        self.assertTrue(p.endswith("facing toward the left edge of the picture."))

    def test_held_size_from_scale_table(self):
        """r23 — 수금 넣기 크기 = 사전 ratio 0.25 ÷ 기준표 팔 길이 0.44 ≈ 0.57 → 팔 길이의 절반쯤(크롭 안에 보이는 것에 견줌)."""
        import gen_local_edit as GL
        size = recheck._lexicon()["kinnor-lyre"]["look"]["size"]
        self.assertEqual(GL.held_size_en(size), "about half as tall as his whole arm is long")
        self.assertIn("about half as tall", GL.held_prompt("x", "add", GL.held_size_en(size)))

    def test_held_target_from_scale_table(self):
        """task 411 — 쥔 수금 칠할 상자 높이 = 사전 0.25 × 인물 구역 키 ÷ 키 등급(m15e 수금이 사전의 절반) · 위끝은 턱(top_min) 아래."""
        import gen_local_edit as GL
        size = recheck._lexicon()["kinnor-lyre"]["look"]["size"]
        b = GL.held_target([(0.25, 0.64), (0.26, 0.64)], size, 0.59, 1.0, 1216, 640)
        self.assertAlmostEqual(b[3] - b[1], 0.25 * 0.59 * 640, delta=1)
        self.assertAlmostEqual((b[2] - b[0]) / (b[3] - b[1]), GL.LYRE_ASPECT, delta=0.03)
        self.assertEqual(GL.held_target([(0.25, 0.64), (0.26, 0.64)], size, 0.59, 1.0, 1216, 640, top_min=403)[1], 403)

    def test_held_head_en_and_paint_prompt(self):
        """task 411 p1 — 크기는 크롭 안 머리에 견줌(0.25 ÷ youth 머리 0.1429 = 1.75) · 칠하기 지시에 「small wooden lyre」 없음(klein 작은 꼴) · 수금 하나."""
        import gen_local_edit as GL
        size = recheck._lexicon()["kinnor-lyre"]["look"]["size"]
        en = GL.held_head_en(size, "youth", 1.0)
        self.assertEqual(en, "nearly twice as tall as his head")
        p = GL.held_prompt("a small hollow wooden sound box", "paint", en)
        self.assertIn(en, p)
        self.assertNotIn("small wooden lyre", p)
        self.assertIn("Only one lyre", p)
        self.assertIn("not touching his mouth", p)

    def test_hug_prompt_frees_arms(self):
        """task 412 — 수금 안는 꼴: 두 팔뚝으로 울림통을 감싸 가슴에 안음 · 매달지 않음 · 팔은 움직여도 됨(KEEP_HELD 「arms … the same」이면 턱 앞 맞잡은 손이 남아 수금이 떠 있음, m16e 사람 「수금 든 모습 이상함」)."""
        import gen_local_edit as GL
        size = recheck._lexicon()["kinnor-lyre"]["look"]["size"]
        p = GL.held_prompt("a small hollow wooden sound box", "hug", GL.held_head_en(size, "youth", 1.0), recheck._lexicon()["kinnor-lyre"]["look"]["hold"])
        self.assertIn("forearms wrapped around its sound box", p)
        self.assertIn("does not hang from his hands", p)
        self.assertIn("only his arms and hands may move", p)
        self.assertNotIn("his arms, face", p)

    def test_back_edge_is_tunic_right_end(self):
        import numpy as np
        import gen_local_edit as GL
        a = np.full((640, 1216, 3), (236, 226, 200), np.uint8)
        a[200:600, 980:1100] = (60, 40, 30)        # 튜닉
        self.assertEqual(GL.back_edge(a, (500, 820, 314.5, 7, 14.0, {}), 936, 1216), 1099)


class WallMaterial(unittest.TestCase):
    """derive.wall-material — 벽 문구는 재질 낱말로(task 405 m5e 벽 앞 틀림 「다윗 뒤는 매끈한 회벽」 ← 「a bare wall behind David」)."""

    def test_bare_wall_fails(self):
        import derive_scene as ds
        with mock.patch.object(ds, "route_prompt", return_value="walls of rough stone blocks, a bare wall behind David"):
            self.assertEqual(len(recheck.wall_material_errors(gibeah())), 1)

    def test_material_wall_passes(self):
        import derive_scene as ds
        with mock.patch.object(ds, "route_prompt", return_value="a bare stone wall, the rough stone wall right behind David"):
            self.assertEqual(recheck.wall_material_errors(gibeah()), [])

    def test_gibeah_passes(self):
        self.assertEqual(recheck.wall_material_errors(gibeah()), [])


def birth():
    import derive_scene as ds
    return copy.deepcopy(ds.load("authored-solomon-jerusalem-birth"))


class Inset(unittest.TestCase):
    """spec.inset(task 417) — 큰 장면 순간에 없는 다른 때는 곁 장면 명세로 따로, 구름은 인물 사이 위(사람 판정 「다른때로 읽힘」)."""

    def test_birth_passes(self):
        self.assertEqual(recheck.inset_errors(birth()), [])

    def test_cloud_beside_one_head_fails(self):
        """판 1 자리 — 인물 오른쪽 가운데·구름 왼쪽 위 구석: 판정 4(한 사람의 생각으로 읽힐 위험)."""
        s = birth()
        s["regions"]["nathan"], s["regions"]["david-prime"] = [0.42, 0.27, 0.56, 0.92], [0.66, 0.27, 0.8, 0.92]
        s["inset"]["region"] = [0.01, 0.02, 0.4, 0.58]
        self.assertTrue(any("사이" in e for e in recheck.inset_errors(s)))

    def test_cloud_over_figure_fails(self):
        s = birth()
        s["inset"]["region"] = [0.1, 0.02, 0.5, 0.56]
        self.assertTrue(any("겹친다" in e for e in recheck.inset_errors(s)))

    def test_missing_or_foreign_sub_spec_fails(self):
        s = birth()
        s["inset"]["spec"] = "authored-solomon-jerusalem-two-mothers"   # inset_of가 이 장면이 아님
        self.assertTrue(any("inset_of" in e for e in recheck.inset_errors(s)))
        s["inset"]["spec"] = "no-such-scene"
        self.assertTrue(any("없다" in e for e in recheck.inset_errors(s)))

    def test_inset_elements_read_sub_prompt(self):
        """field inset 구절 요소는 곁 장면 파생 문구에서 잰다(check_scenes) — 큰 장면 문구에는 밧세바가 없다."""
        import derive_scene as ds
        s = birth()
        self.assertEqual(check_scenes.verse_element_errors(s, ds.route_prompt(s)), [])
        e = next(e for e in s["verse_elements"] if e.get("field") == "inset")
        e["en"] = "a phrase the inset never says"
        self.assertTrue(any("곁 장면" in x for x in check_scenes.verse_element_errors(s, ds.route_prompt(s))))


class InsetFrameAspect(unittest.TestCase):
    """generate.inset-frame-aspect(task 417) — 곁 장면은 구름 틀 비율로 생성(넓은 화면엔 빈자리에 선 여인 2/2)."""

    def test_width_follows_frame(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import inset_try as B
        s = birth()
        x0, y0, x1, y1 = s["inset"]["region"]
        want = (x1 - x0) * B.W / ((y1 - y0) * B.H)
        w = B.inset_w(s)
        self.assertEqual(w % 16, 0)
        self.assertLess(abs(w / B.H - want), 16 / B.H)


class PoseHoldGesture(unittest.TestCase):
    """generate.pose-hold 넓힘(task 417) — 말을 주고받는 손짓(내밂·폄·모음)은 뼈대, 품에 안은 아기(hug)는 문구로."""

    def test_speaking_hand_without_pose_fails(self):
        s = birth()
        s["guide"].pop("pose")
        self.assertTrue(recheck.pose_hold_errors(s))

    def test_hug_not_flagged(self):
        import derive_scene as ds
        s = copy.deepcopy(ds.load("authored-solomon-jerusalem-birth-inset"))
        self.assertEqual(recheck.pose_hold_errors(s), [])


class SitFacing(unittest.TestCase):
    """task 417 — make_guide sit 꼴은 인물 screen_facing을 따름(오른쪽이면 상자 안 좌우 대칭)."""

    def test_right_is_mirror_of_left(self):
        import sys
        from PIL import Image, ImageChops, ImageDraw, ImageOps
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        def draw(right):
            img = Image.new("L", (400, 400), 0)
            M.BODY["sit_right"] = right
            M.sit(ImageDraw.Draw(img), 100, 50, 300, 350, 255)
            M.BODY["sit_right"] = False
            return img
        diff = ImageChops.difference(ImageOps.mirror(draw(False)), draw(True))
        self.assertLess(sum(1 for v in diff.getdata() if v > 128), 400 * 4)   # 정수 화소 반올림 띠만


class PlateCastOverride(unittest.TestCase):
    """task 418 — 판 경로 {cast:X}도 장면 cast_override를 따름(한 장 경로 _cast_in_scene과 같은 카드)."""

    def test_override_reaches_plate_prompt(self):
        import derive_scene as D
        s = copy.deepcopy(gibeah_cached)
        saul = next(f for f in s["figures"] if f["cast"] == "saul")
        saul["cast_override"]["card"]["ageBand"]["text"] = "about 99, test age"
        stage = next(x for x in D.stages(s) if x["region"] == "saul")
        self.assertIn("about 99, test age", stage["prompt"])
        self.assertIn("about 99, test age", D.plate_whole_prompt(s))

    def test_no_override_keeps_canon(self):
        import derive_scene as D
        s = copy.deepcopy(gibeah_cached)
        for f in s["figures"]:
            f.pop("cast_override", None)
        stage = next(x for x in D.stages(s) if x["region"] == "saul")
        self.assertIn(D.cast_describe(D.load_cast("saul")), stage["prompt"])


class TrimPaperMargin(unittest.TestCase):
    """generate.trim-paper-margin(task 422) — 둘레 고른 미색 종이 띠는 생성 뒤 잘라 원래 크기로. 그림이 가장자리까지면·안쪽 그린 틀이면 그대로."""

    @staticmethod
    def picture(w=320, h=200, band=0, frame=None):
        import random
        from PIL import Image, ImageDraw
        rnd = random.Random(1)
        img = Image.new("RGB", (w, h), (243, 234, 214))   # 화풍 머리 「warm cream paper」 빛
        d = ImageDraw.Draw(img)
        d.rectangle([band, band, w - band - 1, h - band - 1], fill=(205, 175, 125))   # 칠한 면(돌벽 빛)
        for _ in range(400):   # 색연필 결 같은 얼룩 — 줄마다 종이 빛이 아님
            x, y = rnd.randrange(band, w - band), rnd.randrange(band, h - band)
            d.rectangle([x, y, min(w - band - 1, x + 12), min(h - band - 1, y + 12)], fill=(rnd.randrange(90, 200), rnd.randrange(60, 160), rnd.randrange(30, 120)))
        if band:
            d.rectangle([band, band, w - band - 1, h - band - 1], outline=(150, 110, 70))
        if frame:
            d.rectangle([0, 0, w - 1, h - 1], outline=frame, width=6)
        return img

    def setUp(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import paper_margin
        self.P = paper_margin

    def test_band_is_trimmed_to_same_size(self):
        img = self.picture(band=12)
        self.assertEqual(self.P.measure(img), (12, 12, 12, 12))
        out = self.P.trim(img)
        self.assertEqual(out.size, img.size)
        self.assertEqual(self.P.measure(out), (0, 0, 0, 0))
        self.assertIs(self.P.trim(out), out)   # 생성·합성에서 두 번 불려도 같은 그림

    def test_no_band_is_untouched(self):
        img = self.picture(band=0)
        self.assertEqual(self.P.measure(img), (0, 0, 0, 0))
        self.assertIs(self.P.trim(img), img)

    def test_picture_to_edge_is_not_cut(self):
        """둘레 빛이 종이가 아니면(그림이 가장자리까지 — 회색 그린 틀 포함) 자르지 않는다 — 그린 틀·액자는 가드 문항 몫."""
        img = self.picture(band=0, frame=(110, 110, 110))
        self.assertIs(self.P.trim(img), img)


class AuthoredDetailRecord(unittest.TestCase):
    """judge.authored-detail-record(task 422) — 본문 근거 없는 [저작] 세부 문항(record)은 답만 적고 통과 셈에서 뺀다."""

    def setUp(self):
        import sys
        sys.path.insert(0, os.path.join(HERE, "batch"))

    def test_gating_drops_record_questions(self):
        import judge_items as J
        qs = [{"id": "m.david"}, {"id": "m.david-sash", "record": True}, {"id": "m.guard"}]
        self.assertEqual([q["id"] for q in J.gating(qs)], ["m.david", "m.guard"])

    def test_record_wrong_does_not_fail_seed(self):
        import inset_judge as I
        qs = {"M": [{"id": "m.core"}, {"id": "m.sash", "record": True}], "I": []}
        rounds = {str(r): {"answers": {"m.core": "맞음", "m.sash": "틀림"}} for r in (1, 2, 3)}
        m = {"answers": {"s11": {"M": rounds}}}
        with mock.patch.object(I, "QS", qs):
            self.assertEqual(I.fails(m, 11), [])
            rounds["1"]["answers"]["m.core"] = rounds["2"]["answers"]["m.core"] = "틀림"
            self.assertEqual(I.fails(m, 11), ["M/m.core"])


if __name__ == "__main__":
    unittest.main()
