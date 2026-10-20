#!/usr/bin/env python3
"""구절 시각 요소 검사(`check_scenes.verse_element_errors`) 회귀 테스트 (2026-10-20, task 375).

host python3 · 표준 unittest만. GPU 0 · 토크나이저 없음 — 512토큰 검사는 check_scenes 본 실행 몫.
짝 없는 요소 · 프롬프트에 없는 en · 「모델이 못 그림」류 제외 사유가 각각 실패해야 한다(notes/VERSE-ELEMENTS.md 고정 절).
"""
import glob
import json
import os
import unittest

import check_scenes as cs
import derive_scene as ds
import params

HERE = os.path.dirname(os.path.abspath(__file__))
VERSES = json.load(open(os.path.join(HERE, "..", "..", "data", "bible", "verses.json"), encoding="utf-8"))
QUOTE = "그들의 앞에서 그 행동을 변하여 미친 체 하고 대문짝에 그적거리며 침을 수염에 흘리매"
PROMPT = "oil painting. Left: a young man scratching marks on the gate doors, drool running down his beard."


def spec(*els):
    return {"verses": {"quotes": {"21:13": QUOTE}},
            "figures": [{"gesture": {"ko": "문짝에 그적거림", "en": "scratching marks on the gate doors", "verse": "21:13"}}],
            "stages": [{"id": "S3", "prompt": "{cast:david}, drool running down his beard, facing left."}],
            "verse_elements": list(els)}


def el(**kw):
    return {"verse": "21:13", "quote": "대문짝에 그적거리며", "kind": "행동", "ko": "문짝에 그적거림",
            "en": "scratching marks on the gate doors", "field": "figures[0].gesture", **kw}


class VerseElements(unittest.TestCase):
    def errs(self, *els):
        return cs.verse_element_errors(spec(*els), PROMPT)

    def test_pass(self):
        self.assertEqual(self.errs(el(), el(quote="침을 수염에 흘리매", en="drool running down his beard", field="stages[S3].prompt")), [])

    def test_out_inside_moment_ok(self):
        self.assertEqual(self.errs({"verse": "21:13", "quote": "그들의 앞에서", "kind": "무리", "ko": "블레셋 사람들 앞",
                                    "out": "21:13 「그들의 앞」은 아기스의 신하들 — 순간은 아기스 한 사람 앞이라 순간 밖"}), [])

    def test_unpaired(self):
        e = el()
        del e["field"], e["en"]
        self.assertTrue(self.errs(e))

    def test_both_field_and_out(self):
        self.assertTrue(self.errs(el(out="순간 밖")))

    def test_en_not_in_prompt(self):
        self.assertTrue(self.errs(el(en="clawing at the doors", field="figures[0].gesture")))

    def test_en_not_in_field(self):
        self.assertTrue(self.errs(el(en="drool running down his beard", field="figures[0].gesture")))

    def test_field_missing(self):
        self.assertTrue(self.errs(el(field="figures[3].gesture")))
        self.assertTrue(self.errs(el(field="stages[S9].prompt")))

    def test_quote_not_in_verse(self):
        self.assertTrue(self.errs(el(quote="문을 긁으며")))
        self.assertTrue(self.errs(el(verse="21:14")))

    def test_quote_against_bible(self):
        """명세 인용이 본문과 달라도(의역) quote가 실제 개역한글에 없으면 실패."""
        s = spec(el())
        s["verses"]["range"] = "삼상 21:10-15"
        verses = {"09021013": {"textKo": QUOTE + " "}}
        self.assertEqual(cs.verse_element_errors(s, PROMPT, verses), [])
        s = spec(el(quote="문을 긁으며"))
        s["verses"] = {"range": "삼상 21:10-15", "quotes": {"21:13": QUOTE + " 문을 긁으며"}}   # 명세 인용에만 덧붙인 말
        self.assertTrue(cs.verse_element_errors(s, PROMPT, verses))

    def test_kind(self):
        self.assertTrue(self.errs(el(kind="분위기")))

    def test_banned_reason(self):
        for why in ("모델 prior에 없어 정적 자세로", "못 그리므로 뺌", "그리기 어렵다", "기댄 자세로 대체"):
            e = el(out=why)
            del e["field"], e["en"]
            self.assertTrue(self.errs(e), why)

    def test_real_scenes_with_list(self):
        """목록을 단 실제 명세는 파생 프롬프트와 함께 통과한다(512토큰은 check_scenes 본 실행)."""
        for p in sorted(glob.glob(os.path.join(HERE, "scenes", "*.json"))):
            s = json.load(open(p, encoding="utf-8"))
            if "verse_elements" not in s:
                continue
            prompt = ds.whole_prompt(ds.load(s["id"])) if "whole_background" in s else ds.plate_whole_prompt(ds.load(s["id"]))
            self.assertEqual(cs.verse_element_errors(s, prompt, VERSES), [], s["id"])

    def test_targets(self):
        self.assertEqual(len(params.VERSE_ELEMENT_SCENES), 14)
        for sid in params.VERSE_ELEMENT_SCENES:
            self.assertTrue(os.path.exists(os.path.join(HERE, "scenes", f"{sid}.json")), sid)


if __name__ == "__main__":
    unittest.main()
