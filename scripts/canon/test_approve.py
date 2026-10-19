#!/usr/bin/env python3
"""`approve.night_pick` 단위 테스트 (task 368). host python3 · 표준 unittest만 — 명세는 dict로 지어 넣는다."""
import unittest

import approve
import scene_state as ss
from test_scene_state import spec


class NightPick(unittest.TestCase):
    def test_writes_final(self):
        s = approve.night_pick(spec(), 11, "edit", "/x/s11.png", "user")
        f = s["approved"]["final"]
        self.assertEqual((f["path"], f["seed"], f["kind"], f["image"], f["by"]), ("night-pick", 11, "edit", "/x/s11.png", "user"))

    def test_not_stale_without_stage_approvals(self):
        s = approve.night_pick(spec(), 42, "base", "/x/s42.png", "user")
        self.assertNotIn("final", ss.stale(s, {"attempts": []}))

    def test_ladder_final_still_stale(self):
        s = spec()
        s["approved"] = {"final": {"attempt": "a001", "seed": 11}}
        self.assertIn("final", ss.stale(s, {"attempts": []}))

    def test_bad_kind(self):
        with self.assertRaises(ValueError):
            approve.night_pick(spec(), 11, "both", "/x.png", "user")



class ConfirmPick(unittest.TestCase):
    """task 369 — 편집은 고른 장에만, 확인 답이 승인본을 정한다."""

    def test_edit_answer_takes_edit_image(self):
        f = approve.confirm_pick(spec(), 5, "편집본", "/x/base/s5.png", "/x/edit/s5.png", "user")["approved"]["final"]
        self.assertEqual((f["path"], f["seed"], f["kind"], f["image"]), ("night-pick", 5, "edit", "/x/edit/s5.png"))

    def test_base_answer_takes_base_image(self):
        f = approve.confirm_pick(spec(), 5, "바탕", "/x/base/s5.png", "/x/edit/s5.png", "user")["approved"]["final"]
        self.assertEqual((f["kind"], f["image"]), ("base", "/x/base/s5.png"))

    def test_bad_answer(self):
        with self.assertRaises(ValueError):
            approve.confirm_pick(spec(), 5, "둘 다", "/b.png", "/e.png", "user")



class PageNames(unittest.TestCase):
    """task 370 회고 eval — 집합(과제)마다 고르기·확인 페이지 파일 이름이 겹치지 않는다(이전 과제 페이지 덮어쓰기 방지)."""

    def test_confirm_and_pick_names_unique(self):
        import make_confirm_page as C
        import make_night_page as P
        self.assertLessEqual(set(C.CONFIRM_DST), set(P.DST))   # 확인 페이지가 있는 과제는 고르기 페이지도 있다
        names = list(P.DST.values()) + list(C.CONFIRM_DST.values())
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(C.CONFIRM_DST[369], "whole-fix-confirm.html")   # 369 재현 이름 그대로


if __name__ == "__main__":
    unittest.main()
