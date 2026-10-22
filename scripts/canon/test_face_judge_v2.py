#!/usr/bin/env python3
"""`make_face_judge_v2` 단위 테스트 (task 393). host python3 · 표준 unittest + PIL — 레포 밖 그림(~/.local/biblemap-imggen)이 없으면 건너뜀."""
import json
import os
import statistics
import unittest

from PIL import Image

import make_face_judge_v2 as V
import params

HAVE = os.path.exists(V.SCENE) and os.path.exists(V.HEADS)


@unittest.skipUnless(HAVE, "기브아 LoRA v3 그림 없음")
class MatchedQuality(unittest.TestCase):
    """화질 맞춤 정본은 흐림이 판정할 머리와 같은 단계여야 한다 — v1 편향(선명한 정본 대 흐린 크롭)을 없애는 것이 이 화면의 뜻."""

    @classmethod
    def setUpClass(cls):
        boxes = json.load(open(V.HEADS))
        canon = {w: Image.open(os.path.join(V.HERE, "frozen", f"{w}.png")) for w in params.LORA_V3_WHO}
        cls.matched, cls.raw = [], []
        for arm in V.ARMS:
            for s in params.LORA_V3_SCENE_SEEDS:
                im = Image.open(os.path.join(V.SCENE, f"{arm}-s{s}.png"))
                for w, b in boxes[f"{arm}-s{s}"].items():
                    c, side = V.detail_crop(f"{arm}-s{s}-{w}", im, b)
                    h = V.hf(V.up(c))
                    m = V.matched_to(canon[w], h)[0]
                    cls.matched.append(V.hf(m) / h)
                    cls.raw.append(V.hf(V.up(canon[w].convert("RGB").resize((V.SIDE, V.SIDE), Image.LANCZOS))) / h)
                    assert m.width == V.up(c).width == V.SIDE

    def test_matched_within_30pct(self):
        self.assertEqual(len(self.matched), 48)
        self.assertTrue(0.7 <= statistics.median(self.matched) <= 1.3, statistics.median(self.matched))
        self.assertGreaterEqual(sum(0.7 <= r <= 1.3 for r in self.matched), 0.9 * len(self.matched))

    def test_unmatched_canon_is_sharper(self):
        """v1처럼 정본을 그대로 보이면 크롭보다 훨씬 선명하다 — 맞춤이 실제로 차이를 만든다는 대조."""
        self.assertGreater(statistics.median(self.raw), 1.3)


class Scripture(unittest.TestCase):
    def test_every_screen_shows_verses(self):
        vs = V.scripture()
        self.assertEqual([r for r, _, _ in vs], ["18:6", "18:7", "18:8", "18:9", "18:10", "18:11"])
        self.assertEqual([r for r, _, now in vs if now], ["18:10"])
        t = V.page([{"id": "A:x", "q": "q", "hint": "h", "refs": [], "caps": [], "img": ""}], vs)
        render = t[t.index("function render()"):t.index("function done()")]
        self.assertIn("${VERSE}", render)   # 문항마다 그리는 함수 안 — 모든 화면 위에
        self.assertIn("삼상 18:6-11", t)
        self.assertIn("<b>", t)
        self.assertIn("판정 face-judge-v2", t)


if __name__ == "__main__":
    unittest.main()
