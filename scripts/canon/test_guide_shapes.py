#!/usr/bin/env python3
"""구도 가이드 새 꼴 회귀 테스트 (2026-10-31, task 457 fix-forward eval).

host python3 · 표준 unittest만. GPU 0 — 실제 장면 명세(scenes/*.json)에서 가이드 그림만 그린다.
task 457: 다윗 귀환 수리로 make_guide에 꼴 둘(river · kneel_bow_reach)을 더했다. 새 꼴은 그 장면만 쓰므로
다른 장면 가이드 바이트는 그대로여야 하고(더할 때 HEAD 코드와 5장면 10장 바이트 같음을 잼),
강 띠는 둘레 땅보다 어둡고 시므이 머리는 왼쪽(왕 쪽)에 그려져야 한다.
"""
import glob
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import derive_scene as ds  # noqa: E402
import make_guide as mg  # noqa: E402

NEW = {"river", "kneel_bow_reach"}
JORDAN = "authored-david-returns-jerusalem"


class GuideShapes(unittest.TestCase):
    def test_new_shapes_only_in_jordan(self):
        """새 꼴은 다윗 귀환 명세만 쓴다 — 다른 장면 가이드는 이 꼴을 거치지 않아 바이트가 바뀌지 않는다."""
        users = {}
        for p in sorted(glob.glob(os.path.join(HERE, "scenes", "*.json"))):
            shapes = set((json.load(open(p, encoding="utf-8")).get("guide") or {}).get("shape", {}).values())
            for s in shapes & NEW:
                users.setdefault(s, []).append(os.path.basename(p)[:-5])
        self.assertEqual(users, {s: [JORDAN] for s in NEW})

    def test_deterministic(self):
        spec = ds.load(JORDAN)
        self.assertEqual(mg.make(spec, 2).tobytes(), mg.make(spec, 2).tobytes())

    def test_river_darker_than_ground(self):
        """강 칸 아래쪽 줄에서 강 안(오른쪽 끝)이 강 밖 왼쪽 땅보다 어둡다(물·땅 경계가 깊이 그림에 실림)."""
        spec = ds.load(JORDAN)
        img = mg.make(spec, 2).convert("L")
        x0, y0, x1, y1 = spec["regions"]["river"]
        y = int((y1 - 0.01) * mg.H)
        self.assertLess(img.getpixel((int(0.99 * mg.W), y)), img.getpixel((int(0.02 * mg.W), y)))

    def test_kneel_bow_reach_head_left(self):
        """kneel_bow_reach는 머리·팔이 왼쪽 땅, 오른쪽 아래 끝은 비어 있다(정강이 막대를 접음 — 456 머리 뒤집힘)."""
        from PIL import Image, ImageDraw
        img = Image.new("L", (200, 100), 0)
        mg.kneel_bow_reach(ImageDraw.Draw(img), 0, 0, 200, 100, 255)
        self.assertEqual(img.getpixel((30, 92)), 255)    # 왼쪽 땅의 머리
        self.assertEqual(img.getpixel((197, 97)), 0)     # 오른쪽 끝에 뻗은 정강이 없음


    def test_horn_pour_mouth_low_right(self):
        """horn_pour(task 606 기혼)는 위 왼쪽에서 아래 오른쪽으로 굽어 내려옴 — 끝에서 구역 아래 끝까지 기름 줄기(문구만이면 뿔이 세워져 입이 위를 향함 601~605).
        task 631: 넓은 밑동이 위 왼쪽, 뾰족한 끝이 아래 오른쪽(사람 판정 620 「뿔 위아래 위치 바뀜」 — 넓은 입으로 붓지 않음)."""
        from PIL import Image, ImageDraw
        img = Image.new("L", (100, 100), 0)
        mg.horn_pour(ImageDraw.Draw(img), 0, 0, 100, 100, 255)
        self.assertEqual(img.getpixel((85, 75)), 255)    # 뾰족한 끝(아래 오른쪽)
        self.assertEqual(img.getpixel((85, 97)), 255)    # 끝 아래 기름 줄기
        self.assertEqual(img.getpixel((5, 95)), 0)       # 왼쪽 아래는 빔
        self.assertEqual(img.getpixel((5, 5)), 255)      # 넓은 밑동(위 왼쪽 — 반지름 0.2, 비스듬히 644)
        self.assertEqual(img.getpixel((95, 80)), 0)      # 끝은 가늘다(옛 넓은 입 반지름 0.2면 칠해짐)

    def test_bier_lying_body(self):
        """bier(task 618 사무엘의 죽음)는 낮은 판 위에 가로로 누운 몸 — 구역 가운데 위쪽은 몸, 위 끝은 빔, 판 아래 가운데는 빔(다리 사이)."""
        from PIL import Image, ImageDraw
        img = Image.new("L", (200, 100), 0)
        mg.bier(ImageDraw.Draw(img), 0, 0, 200, 100, 255)
        self.assertEqual(img.getpixel((100, 45)), 255)   # 누운 몸
        self.assertEqual(img.getpixel((100, 66)), 255)   # 나무 판
        self.assertEqual(img.getpixel((100, 5)), 0)      # 몸 위는 빔
        self.assertEqual(img.getpixel((100, 90)), 0)     # 판 아래 다리 사이는 빔

if __name__ == "__main__":
    unittest.main()
