#!/usr/bin/env python3
"""`recheck.py` 단위 테스트 (task 392). host python3 · 표준 unittest만 — 호출·토크나이저 없이 원장·금지 낱말·해시·승인 출처만 본다."""
import copy
import json
import unittest

import approve
import recheck
import scene_state as ss
from test_scene_state import spec


class Ledger(unittest.TestCase):
    def setUp(self):
        self.L = recheck.ledger()

    def test_format(self):
        need = {"id", "layer", "scope", "check", "source", "since"}
        self.assertGreaterEqual(len(self.L["rules"]), 28)
        for r in self.L["rules"]:
            self.assertLessEqual(need, set(r), r.get("id"))
            self.assertIn(r["layer"], ("spec", "derive", "generate", "edit", "judge", "human"), r["id"])
            self.assertIn(r["scope"], ("all", "list", "one", "doc", "rejected"), r["id"])
        self.assertEqual(len({r["id"] for r in self.L["rules"]}), len(self.L["rules"]))

    def test_version_is_content_hash(self):
        """규칙을 고치고 `recheck.py ledger`를 안 돌리면 판이 낡는다 — 그림 기록의 rules_version이 거짓이 된다."""
        self.assertEqual(self.L["version"], recheck.ledger_version(self.L))
        L2 = copy.deepcopy(self.L)
        L2["rules"][0]["note"] += "."
        self.assertNotEqual(recheck.ledger_version(L2), self.L["version"])

    def test_every_function_rule_has_runner(self):
        recheck.spec_rules(self.L)   # 실행기 없는 함수 규칙이면 SystemExit

    def test_generate_check_function_not_silently_dropped(self):
        """generate 층은 SPEC_CHECKS에 없으면 spec_rules가 SystemExit 없이 조용히 뺀다 — 검사 함수(*_errors)를 단 생성 규칙은
        실행기에 등록돼 있어야 함(task 409 회고: perspective_errors가 빠질 뻔함). 관문 자체(require_pass)·폐기 규칙은 제외."""
        miss = [r["id"] for r in self.L["rules"] if r["layer"] == "generate" and not r.get("retired")
                and r["check"].endswith("_errors") and r["check"] not in recheck.SPEC_CHECKS]
        self.assertEqual(miss, [])


class BannedWords(unittest.TestCase):
    def test_catches_word_anywhere_in_spec_text(self):
        s = spec()
        s["moment"] = {"why": "창을 던지는 동작은 모델 prior에 없다", "verse": "18:10"}
        hits = recheck.banned_words(s)
        self.assertIn("moment.why: prior", hits)
        self.assertIn("moment.why: 모델", hits)

    def test_skips_stage_and_judge_text(self):
        s = spec()
        s["stages"][0]["prompt"] = "no prior here"
        s["judge"] = {"note": "모델"}
        self.assertEqual(recheck.banned_words(s), [])


class PropInPrompt(unittest.TestCase):
    def test_korean_only_prop_fails_english_prop_carried_passes(self):
        """한국어뿐인 prop은 영문이 없어 실패, 영문 지물이 파생 프롬프트에 있으면 통과 — 「none」은 지물 없음."""
        import check_scenes
        s = spec()
        s["figures"] = [{"cast": "goliath", "prop": "큰 방패"}, {"cast": "saul", "prop": "a spear"},
                        {"cast": "samuel", "prop": "a torn robe corner"}, {"cast": "david", "prop": "none"}]
        errs = check_scenes.prop_in_prompt_errors(s, "saul holding a spear, the hem of samuel's robe")
        self.assertEqual(len(errs), 1)
        self.assertIn("goliath", errs[0])
        self.assertIn("영문 없음", errs[0])
        self.assertTrue(check_scenes.prop_in_prompt_errors(s | {"figures": s["figures"][1:2]}, "saul standing"))

    def test_rule_wired_for_all_specs(self):
        r = next(x for x in recheck.ledger()["rules"] if x["id"] == "derive.prop-in-prompt")
        self.assertEqual(r["scope"], "all")
        self.assertIn(r, recheck.spec_rules(recheck.ledger()))


class Retired(unittest.TestCase):
    def test_retired_rule_left_out_of_recheck(self):
        L = copy.deepcopy(recheck.ledger())
        ids = {r["id"] for r in recheck.spec_rules(L)}
        self.assertNotIn("derive.clip-77-tokens", ids)
        L["rules"][0]["retired"] = "시험"
        self.assertNotIn(L["rules"][0]["id"], {r["id"] for r in recheck.spec_rules(L)})


class Hashes(unittest.TestCase):
    def test_one_char_changes_spec_hash(self):
        a = spec()
        b = copy.deepcopy(a)
        b["moment"]["why"] += "."
        self.assertNotEqual(ss.spec_hash(a), ss.spec_hash(b))

    def test_approval_record_does_not_change_spec_hash(self):
        a = spec()
        b = approve.night_pick(copy.deepcopy(a), 11, "base", "/x/s11.png", "user", "p")
        self.assertEqual(ss.spec_hash(a), ss.spec_hash(b))

    def test_night_pick_stamps_provenance(self):
        f = approve.night_pick(spec(), 11, "base", "/x/s11.png", "user", "a prompt")["approved"]["final"]
        self.assertEqual(f["prompt_hash"], ss.prompt_hash("a prompt"))
        self.assertEqual(f["rules_version"], recheck.ledger()["version"])
        self.assertEqual(f["spec_hash"], ss.spec_hash(spec()))

    def test_no_prompt_says_why(self):
        f = approve.local_edit(spec(), 5, "x.png", [{"id": "k"}], "user")["approved"]["final"]
        self.assertIsNone(f["prompt_hash"])
        self.assertTrue(f["prompt_hash_why"])


class Situation(unittest.TestCase):
    def test_missing_and_present(self):
        s = spec()
        self.assertTrue(recheck.has_situation(s))
        s["situation"] = {"text": "상황", "same_time": {}}
        self.assertEqual(recheck.has_situation(s), [])


class Majority(unittest.TestCase):
    def test_two_of_three(self):
        self.assertEqual(recheck._maj([{"a": "틀림"}, {"a": "틀림"}, {"a": "맞음"}]), {"a": "틀림"})
        self.assertEqual(recheck._maj([{"a": "틀림"}, {"a": "맞음"}, {"a": "맞음"}]), {"a": "맞음"})


if __name__ == "__main__":
    unittest.main()


class ApprovedSource(unittest.TestCase):
    """task 412 — 국소 편집 승인의 바탕이 plain-words 회차가 아니라 gibeah-step23 시도(steps[0].src)여도 출처를 찾음(recheck.py images가 멈췄음)."""

    def test_gibeah_step23_base(self):
        f = {"path": "local-edit", "image": "samples/gibeah-step23/m17e/approved-authored-saul-gibeah-spear.png",
             "steps": [{"end": "paste", "src": "m15/s7.png"}]}
        r = recheck.source("authored-saul-gibeah-spear", f)
        self.assertEqual(r["from"], "gibeah-step23 m15 s7 + 국소 편집")
        self.assertTrue(r["prompt"])
        self.assertIsNone(r["boxes"])

    def test_bundle_without_prompt_says_why(self):
        """task 433 — 출생 곁 장면 묶음(birth-inset)은 생성 프롬프트를 기록하지 않음 → stamp가 why_prompt 없이 멈췄음."""
        f = {"path": "night-pick", "seed": 11, "kind": "comp", "image": "samples/birth-inset/try2-424/comp-s11.png"}
        r = recheck.source("authored-solomon-jerusalem-birth", f)
        self.assertIsNone(r["prompt"])
        self.assertTrue(r["why_prompt"])
