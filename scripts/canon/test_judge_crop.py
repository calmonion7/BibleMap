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


    def test_judge_refuses_missing_images(self):
        """task 424 회고 — 생성 워커 SIGSEGV로 7장이 빠진 채 판정이 돌아 빈 그림 답이 쌓였다: 그림이 하나라도 없으면 묻지 않고 멈춘다."""
        from unittest import mock
        import inset_judge as I
        with mock.patch.object(I, "img", lambda kind, s: os.path.join(self.d, "없음.png")), mock.patch.object(I, "ask") as ask:
            with self.assertRaises(SystemExit):
                I.judge()
            ask.assert_not_called()

    def test_control_group_has_own_copy(self):
        """task 424 — 같은 장면·시드의 대조군(I0, 옛 그림)과 곁 장면(I, 새 그림)은 복사본 폴더가 달라야 함:
        한 폴더를 같이 쓰면 옛 그림이 더 오래돼 낡음으로 걸리지 않아 대조군이 새 그림 복사본을 봄."""
        import inset_judge as I
        old = os.path.join(self.d, "old.png")
        Image.new("RGB", (64, 32), "black").save(old)
        new = dict(task=I.task_of("I"), scene="x", seed=1, src=self.src, qs=[])
        ctl = dict(new, task=I.task_of("I0"), src=old)
        J.prepare(new, "t")
        _, files = J.prepare(ctl, "t")
        self.assertEqual(Image.open(files["full"]).getpixel((0, 0)), (0, 0, 0))
