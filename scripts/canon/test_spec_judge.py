"""task 378 — 명세 판정자(batch/judge_spec.py)와 이상한 점 결합 후보 규칙(judge_learn.pick_candidates) 단언. GPU·claude 호출 없음.

  python3 -m unittest test_spec_judge
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import judge_learn as JL
import judge_spec as S

VERSES = json.load(open(S.CS.VERSES, encoding="utf-8"))


class Window(unittest.TestCase):
    def test_chapter_of_moment(self):
        s = S.scene("authored-david-gath-achish")
        self.assertEqual(S.chapters(s), [21])
        w = dict(S.window(s, VERSES))
        self.assertIn("침을 수염에 흘리매", w["21:13"])
        self.assertIn("21:1", w)   # 순간 절만이 아니라 장 전체

    def test_range_over_chapters(self):
        s = {"verses": {"range": "삼상 19:18-20:2"}, "moment": {"verse": "19:18"}}
        self.assertEqual(S.chapters(s), [19, 20])

    def test_refs(self):
        self.assertEqual(S.refs("17:26-29"), ["17:26", "17:27", "17:28", "17:29"])
        self.assertEqual(S.refs("삼하 2:14·2:15"), ["2:14", "2:15"])
        self.assertEqual(S.refs("21:13 후반"), ["21:13"])
        self.assertEqual(S.refs(""), [])


class Validate(unittest.TestCase):
    win = dict(S.window(S.scene("authored-david-gath-achish"), VERSES))

    def test_quote_in_verse(self):
        f = {"kind": "축약", "verse": "21:13", "quote": "침을 수염에  흘리매"}   # 띄어쓰기 무시
        self.assertEqual(S.validate(f, self.win), (True, ""))

    def test_made_up_quote(self):
        f = {"kind": "빠짐", "verse": "21:13", "quote": "침을 땅에 뱉으매"}
        self.assertEqual(S.validate(f, self.win), (False, "지어낸 인용"))

    def test_quote_from_other_verse(self):
        f = {"kind": "빠짐", "verse": "21:12", "quote": "침을 수염에 흘리매"}
        self.assertFalse(S.validate(f, self.win)[0])

    def test_verse_outside_window(self):
        f = {"kind": "빠짐", "verse": "22:1", "quote": "다윗이"}
        self.assertEqual(S.validate(f, self.win), (False, "창 밖 절"))

    def test_mismatch_needs_two_fields(self):
        self.assertTrue(S.validate({"kind": "어긋남", "field": ["moment.why", "figures[0].pose"]}, self.win)[0])
        self.assertTrue(S.validate({"kind": "어긋남", "field": "moment.why ↔ figures[0].pose"}, self.win)[0])
        self.assertFalse(S.validate({"kind": "어긋남", "field": "moment.why"}, self.win)[0])

    def test_unknown_kind(self):
        self.assertFalse(S.validate({"kind": "기타", "verse": "21:13", "quote": "침을"}, self.win)[0])


class Parse(unittest.TestCase):
    def test_json_in_text(self):
        f = S.parse('검토 결과:\n```json\n{"findings": [{"kind": "빠짐", "verse": "17:22"}]}\n```')
        self.assertEqual(f, [{"kind": "빠짐", "verse": "17:22"}])

    def test_empty_list_is_answer(self):
        self.assertEqual(S.parse('{"findings": []}'), [])

    def test_broken(self):
        self.assertIsNone(S.parse("모르겠음"))
        self.assertIsNone(S.parse('{"findings": "없음"}'))


class Match(unittest.TestCase):
    fx = S.fixed()
    T = {t["id"]: t for t in fx["truth"]}

    def test_fixed_block(self):
        self.assertEqual(len(self.fx["truth"]), 5)
        self.assertEqual(len(self.fx["mutants"]), 5)
        self.assertEqual((len(self.fx["oddity"]["pos"]), len(self.fx["oddity"]["neg"])), (12, 33))

    def test_verse_and_word(self):
        f = {"kind": "빠짐", "verse": "17:22", "quote": "다윗과 및 그와 함께 한 모든 백성이", "제안": "따르는 백성을 무리로"}
        self.assertTrue(S.matches(f, self.T["c"]))
        self.assertFalse(S.matches({**f, "kind": "순간"}, self.T["c"]))       # 종류 밖
        self.assertFalse(S.matches({**f, "verse": "17:1"}, self.T["c"]))      # 절 밖
        self.assertFalse(S.matches({**f, "quote": "요단을 건너", "제안": "강"}, self.T["c"]))   # 낱말 없음

    def test_field_pair(self):
        f = {"kind": "어긋남", "field": ["moment.why", "crowds"], "제안": "형제들을 무리 칸에"}
        self.assertTrue(S.matches(f, self.T["e"]))
        self.assertFalse(S.matches({**f, "field": ["moment.why", "figures[0].pose"]}, self.T["e"]))

    def test_word_regex_over_quote_and_suggestion(self):
        f = {"kind": "축약", "verse": "21:13", "quote": "침을 수염에 흘리매", "제안": ""}
        self.assertTrue(S.matches(f, self.T["f"]))


class Mutants(unittest.TestCase):
    def test_each_mutant_removes_its_element(self):
        for m in S.fixed()["mutants"]:
            orig = S.scene(m["scene"])
            mut = S.mutate(orig, m["id"])
            self.assertTrue(S.leaks(orig, m["forbid"]), m["id"])     # 원본엔 있었고
            self.assertEqual(S.leaks(mut, m["forbid"]), [], m["id"])   # 사본엔 없다
            self.assertEqual(orig, S.scene(m["scene"]))               # 원본은 그대로
            self.assertLess(len(mut["verse_elements"]), len(orig["verse_elements"]), m["id"])
            self.assertEqual(mut["verses"], orig["verses"])            # 성경 본문 인용은 그대로

    def test_missing_edit_target_fails_loudly(self):
        s = S.scene("authored-david-ark-jerusalem")
        s["moment"]["why"] = "바뀐 글"
        with self.assertRaises(AssertionError):
            S.mutate(s, "m1")


OK, NO = "맞음", "틀림"


def seed(moment, wrong=0):
    return {"moment": moment, **{f"q{i}": NO for i in range(wrong)}}


class Oddity(unittest.TestCase):
    ans = {"x": {11: seed(OK, 0), 42: seed(OK, 1), 7: seed(NO, 0)}}

    def test_off_is_376_rule(self):
        c = JL.pick_candidates(self.ans)["x"]
        self.assertEqual(c["cand"], 11)
        self.assertNotIn("reason", c)

    def test_on_skips_odd_seed(self):
        c = JL.pick_candidates(self.ans, {"x": {11: NO, 42: OK, 7: OK}})["x"]
        self.assertEqual((c["cand"], c["reject"], c["reason"]), (42, False, None))

    def test_on_missing_oddity_answer_counts_odd(self):
        c = JL.pick_candidates(self.ans, {"x": {11: None, 42: OK, 7: OK}})["x"]
        self.assertEqual(c["cand"], 42)

    def test_reject_reasons(self):
        odd = JL.pick_candidates(self.ans, {"x": {11: NO, 42: NO, 7: OK}})["x"]
        self.assertEqual((odd["cand"], odd["reject"], odd["reason"]), (None, True, "이상한 점"))
        mom = JL.pick_candidates({"x": {11: seed(NO), 42: seed(NO)}}, {"x": {11: OK, 42: OK}})["x"]
        self.assertEqual((mom["reject"], mom["reason"]), (True, "장면 뜻"))


def scene(answer, cand=None, revived=None, memo="", wrong=None):
    return {"cand": {"answer": answer, "cand": cand, "revived": revived, "memo": memo}, "items": {q: {"wrong": w} for q, w in (wrong or {}).items()}}


class RegenRules(unittest.TestCase):
    fx = {"recur": [{"id": "a", "scene": "x", "qids": ["crowds"], "words": "혼자|무리"},
                    {"id": "b", "scene": "y", "qids": ["moment"], "words": "형제"},
                    {"id": "c", "scene": "z", "qids": [], "words": "칼"}],
          "rules": {"recur_max": 1, "usable_min": 2, "revive_max": 0}}

    def test_adopt(self):
        sc = {"x": scene("쓸 만함", 5), "y": scene("쓸 만함", 7), "z": scene("없음", 3, memo="좋음")}
        line, r, recur = JL.regen_rules(sc, self.fx)
        self.assertEqual((line, recur), ("판정: 두 겹 판정 채택", []))

    def test_recur_by_mark_memo_and_agree(self):
        sc = {"x": scene("쓸 만함", 5, wrong={"crowds": [5]}), "y": scene("없음", 7, memo="형제가 없다"), "z": scene("동의")}
        line, r, recur = JL.regen_rules(sc, self.fx)
        self.assertEqual(recur, ["a", "b", "c"])
        self.assertEqual(line, "판정: 보류 (어긴 규칙 1, 2)")

    def test_mark_on_sample_seed_is_not_recur(self):
        sc = {"x": scene("쓸 만함", 5, wrong={"crowds": [23]}), "y": scene("쓸 만함", 7), "z": scene("쓸 만함", 1)}
        self.assertEqual(JL.regen_rules(sc, self.fx)[2], [])

    def test_revived_counts_even_if_none(self):   # 376 cand_rules와 같은 정의
        sc = {"x": scene("쓸 만함", 5), "y": scene("쓸 만함", 7), "z": scene("없음", 3, revived=11)}
        self.assertEqual(JL.regen_rules(sc, self.fx)[0], "판정: 보류 (어긴 규칙 3)")


if __name__ == "__main__":
    unittest.main()
