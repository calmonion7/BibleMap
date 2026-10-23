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

    def test_other_depth_needs_nothing(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = s["regions"]["david-youth"][3] - 0.78 * (s["regions"]["saul"][3] - s["regions"]["saul"][1])
        s["guide"]["depth"]["david-youth"] = 0.7
        self.assertEqual(recheck.height_ratio_errors(s), [])

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
    """generate.figure-scale — 무리 없는 가까운 장면의 인물 구역은 화면 높이 0.6 이상(task 403 d1)."""

    def test_small_figure_fails(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = 0.46
        self.assertEqual(len(recheck.figure_scale_errors(s)), 1)

    def test_crowd_scene_needs_nothing(self):
        s = gibeah()
        s["regions"]["david-youth"][1] = 0.46
        s["guide"]["shape"]["wall"] = "crowd"
        self.assertEqual(recheck.figure_scale_errors(s), [])

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
        (L, T, side), box = GL.prop_box(gibeah()["regions"]["spear"], 1216, 640, "front")
        self.assertTrue(box[0] <= 110 and box[2] <= 300)   # d3 창 왼끝 110 ~ 가운데
        self.assertGreaterEqual(box[0], round(0.09 * 1216))   # d4e: 벽 구역(0~0.09) 안으로 들어가지 않음

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

if __name__ == "__main__":
    unittest.main()
