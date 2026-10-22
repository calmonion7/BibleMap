#!/usr/bin/env python3
"""`make_face_judge_v3` 단위 테스트 (task 395). host python3 · 표준 unittest + PIL — 레포 밖 그림(~/.local/biblemap-imggen)이 없으면 건너뜀."""
import json
import os
import statistics
import unittest

from PIL import Image

import make_face_judge_v3 as M
import make_face_judge_v2 as V
import params

HAVE = os.path.exists(M.PASTE) and len(os.listdir(M.HEADS_V3)) == 16 if os.path.exists(M.HEADS_V3) else False


@unittest.skipUnless(HAVE, "face-detail-v3 그림 없음")
class MatchedQuality(unittest.TestCase):
    """문항 A도 393 v2 규칙 — 정본 선명도를 판정할 머리에 맞추고, 정본·머리를 같은 크기로."""

    @classmethod
    def setUpClass(cls):
        boxes = json.load(open(V.HEADS))
        canon = {w: Image.open(os.path.join(V.HERE, "frozen", f"{w}.png")) for w in params.LORA_V3_WHO}
        cls.ratio = []
        for s in params.LORA_V3_SCENE_SEEDS:
            for arm in M.ARMS:
                for w in params.LORA_V3_WHO:
                    h = M.head(arm, s, w, boxes[f"C-s{s}"][w])
                    m = V.matched_to(canon[w], V.hf(h))[0]
                    assert m.width == h.width == V.SIDE
                    cls.ratio.append(V.hf(m) / V.hf(h))

    def test_matched_within_30pct(self):
        self.assertEqual(len(self.ratio), 32)
        self.assertTrue(0.7 <= statistics.median(self.ratio) <= 1.3, statistics.median(self.ratio))
        self.assertGreaterEqual(sum(0.7 <= r <= 1.3 for r in self.ratio), 0.9 * len(self.ratio))

    def test_question_counts(self):
        qs = M.questions()
        kinds = [q["id"].split(":")[0] for q in qs]
        self.assertEqual((kinds.count("A"), kinds.count("B1"), kinds.count("B2")), (32, 8, 8))
        self.assertEqual(sum(q["id"].startswith("A:V3:") for q in qs), 16)


class Page(unittest.TestCase):
    def test_verses_and_tag(self):
        t = M.page([], V.scripture())
        render = t[t.index("function render()"):t.index("function done()")]
        self.assertIn("${VERSE}", render)
        self.assertIn('figure class="judge"', render)   # 문항 A 같은 크기 칸
        self.assertIn("판정 face-detail-v3", t)
        self.assertNotIn("판정 face-judge-v2", t)


if __name__ == "__main__":
    unittest.main()
