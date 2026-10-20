"""task 386 회고 — judge_items.prepare의 crop은 그림 크기 비율(0~1). 픽셀 값을 넘기면 바로 ValueError(전엔 decompression bomb로 죽음)."""
import os, sys, tempfile, unittest

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch"))
import judge_items as J


class CropUnits(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.src = os.path.join(self.d, "s.png")
        Image.new("RGB", (1216, 640), "white").save(self.src)
        self.work, J.WORK = J.WORK, self.d

    def tearDown(self):
        J.WORK = self.work

    def item(self, crop):
        return {"task": "t", "scene": "x", "seed": 1, "src": self.src, "qs": [{"who": "edit", "crop": {"1": crop}}]}

    def test_fraction_ok(self):
        d, files = J.prepare(self.item([0.25, 0.25, 0.2, 0.375]), "t")
        self.assertIn("edit", files)

    def test_pixels_rejected(self):
        with self.assertRaises(ValueError):
            J.prepare(self.item([310, 160, 240, 240]), "t")


if __name__ == "__main__":
    unittest.main()
