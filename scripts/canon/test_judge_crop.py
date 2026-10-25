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


class StaleCopy(unittest.TestCase):
    """task 422 회고 — 원본을 고치면(여백 자름) prepare가 옛 full.jpg·크롭을 다시 쓰지 않는다(판정자가 자르기 전 그림을 봤다)."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.src = os.path.join(self.d, "s.png")
        Image.new("RGB", (64, 32), "white").save(self.src)
        self.work, J.WORK = J.WORK, self.d

    def tearDown(self):
        J.WORK = self.work

    def test_newer_source_rebuilds_copy(self):
        it = {"task": "t", "scene": "x", "seed": 1, "src": self.src, "qs": [{"who": "a", "crop": {"1": [0, 0, 0.5, 0.5]}}]}
        _, files = J.prepare(it, "t")
        old = os.path.getmtime(files["full"])
        os.utime(files["full"], (old - 10, old - 10))
        os.utime(files["a"], (old - 10, old - 10))
        Image.new("RGB", (64, 32), "black").save(self.src)
        _, files = J.prepare(it, "t")
        self.assertEqual(Image.open(files["full"]).getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(Image.open(files["a"]).getpixel((0, 0)), (0, 0, 0))
