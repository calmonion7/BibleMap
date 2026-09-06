#!/usr/bin/env python3
"""`scene_state`의 재검토 규칙 단위 테스트 (2026-09-05, task 338).

host python3 · 표준 unittest만. GPU도 파일도 없다 — 명세와 곁파일을 dict로 지어 넣는다.
계획 DoD 3이 세운 일곱 경우를 그대로 옮겼다. 한 곳만 갈렸다(`test_s4_prompt_edit`) —
사유는 `scene_state` 머리말 「전파」 절.
"""
import copy
import unittest

import scene_state as ss

STAGES = [
    ("S1", "full", "full"), ("S2", "region", "c"), ("S3", "ridge", "c"),
    ("S4", "plate", "a"), ("S5", "plate", "b"),
]


def spec():
    return {
        "id": "t",
        "verses": {"range": "삼상 11:14-15", "quotes": {"11:14": "오라 우리가 길갈로 가서"}},
        "moment": {"verse": "11:15", "why": "왕으로 세우는 순간"},
        "background": [{"what": "돌 제단"}],
        "crowds": [{"what": "백성"}],
        "figures": [{"cast": "samuel"}, {"cast": "saul"}],
        "regions": {"full": [0.0, 0.0, 1.0, 1.0], "a": [0.12, 0.37, 0.285, 0.92],
                    "b": [0.6, 0.34, 0.762, 0.92], "c": [0.02, 0.15, 0.98, 0.33]},
        "stages": [{"id": i, "kind": k, "region": r, "prompt": f"p{i}", "neg": [f"n{i}"]}
                   for i, k, r in STAGES],
    }


def approved(sp):
    """모든 단계를 시도 a001~a005로 승인하고 사다리 셋과 final까지 적는다 → (spec, attempts)."""
    sp = copy.deepcopy(sp)
    ats, up = [], None
    for n, st in enumerate(sp["stages"], start=1):
        aid = f"a00{n}"
        ats.append({"id": aid, "stage": st["id"], "seeds": [11], "prompt": st["prompt"],
                    "neg": list(st["neg"]), "region": list(sp["regions"][st["region"]]),
                    "upstream": up, "by": "cli",
                    "images": {"11": {"canvas": f"/tmp/{aid}.png"}}})
        st["approved"] = {"attempt": aid, "seed": 11, "by": "cli", "on": "2026-09-05"}
        up = {"stage": st["id"], "attempt": aid, "seed": 11}
    h = ss.ladder_hashes(sp)
    sp["approved"] = {k: {"hash": h[k], "by": "cli", "on": "2026-09-05"} for k in ss.LADDER}
    sp["approved"]["final"] = {"attempt": "a005", "seed": 11, "by": "cli", "on": "2026-09-05"}
    return sp, {"scene": "t", "sceneSeed": 11, "attempts": ats}


class LadderHashes(unittest.TestCase):
    def test_stable_and_scoped(self):
        sp = spec()
        self.assertEqual(ss.ladder_hashes(sp), ss.ladder_hashes(copy.deepcopy(sp)))
        # 문구·구역 좌표는 사다리에 들어가지 않는다 — 단계의 입력이라 시도가 들고 있다.
        moved = copy.deepcopy(sp)
        moved["stages"][3]["prompt"] = "다른 문구"
        moved["regions"]["a"] = [0.0, 0.0, 0.5, 0.5]
        self.assertEqual(ss.ladder_hashes(sp)["split"], ss.ladder_hashes(moved)["split"])
        # 분할(단계 순서)이 바뀌면 ③이 바뀐다.
        reordered = copy.deepcopy(sp)
        reordered["stages"][3], reordered["stages"][4] = reordered["stages"][4], reordered["stages"][3]
        self.assertNotEqual(ss.ladder_hashes(sp)["split"], ss.ladder_hashes(reordered)["split"])


class Stale(unittest.TestCase):
    def test_no_approval_no_stale(self):
        self.assertEqual(ss.stale(spec(), {"attempts": []}), {})

    def test_all_approved_consistent(self):
        sp, at = approved(spec())
        self.assertEqual(ss.stale(sp, at), {})

    def test_s1_approval_replaced(self):
        """S1을 새 시도로 갈아 승인하면 S1은 정합, S2부터 전부 재검토."""
        sp, at = approved(spec())
        at["attempts"].append({**at["attempts"][0], "id": "a009"})
        sp["stages"][0]["approved"] = {"attempt": "a009", "seed": 11, "by": "cli", "on": "x"}
        bad = ss.stale(sp, at)
        self.assertEqual([k for k in bad if k.startswith("S")], ["S2", "S3", "S4", "S5"])
        self.assertIn("final", bad)

    def test_s4_prompt_edit(self):
        """S4 문구를 고치면 S4와 **그 아래**(S5)와 final.

        계획 DoD 3의 예시는 「S4·final만」이라 전파를 금하지만, 같은 목록의
        「S1 구역 좌표 수정 → S1과 아래 전부」는 전파를 요구한다 — 셋이 함께 설 수 없어
        과탐지 쪽(전파)을 택했다. `scene_state` 머리말 「전파」 절.
        """
        sp, at = approved(spec())
        sp["stages"][3]["prompt"] = "고친 문구"
        bad = ss.stale(sp, at)
        self.assertEqual([k for k in bad if k.startswith("S")], ["S4", "S5"])
        self.assertIn("이 그림을 그린 문구가 지금 명세와 다르다", bad["S4"])
        self.assertIn("final", bad)

    def test_s1_region_edit_cascades(self):
        sp, at = approved(spec())
        sp["regions"]["full"] = [0.0, 0.05, 1.0, 1.0]
        bad = ss.stale(sp, at)
        self.assertEqual([k for k in bad if k.startswith("S")], ["S1", "S2", "S3", "S4", "S5"])
        self.assertIn("이 그림을 그린 구역 좌표가 지금 명세와 다르다", bad["S1"])

    def test_description_edit_stales_everything(self):
        sp, at = approved(spec())
        sp["moment"]["why"] = "다른 순간을 고정한다"
        bad = ss.stale(sp, at)
        self.assertIn("description", bad)
        for sid in ("S1", "S2", "S3", "S4", "S5", "final"):
            self.assertIn(sid, bad)

    def test_reapprove_s2_clears_itself_only(self):
        """S1 교체로 S2~S5가 흔들린 뒤, S2를 새 upstream으로 재승인하면 S2만 풀린다."""
        sp, at = approved(spec())
        at["attempts"].append({**at["attempts"][0], "id": "a009"})
        sp["stages"][0]["approved"] = {"attempt": "a009", "seed": 11, "by": "cli", "on": "x"}
        at["attempts"].append({**at["attempts"][1], "id": "a010",
                               "upstream": {"stage": "S1", "attempt": "a009", "seed": 11}})
        sp["stages"][1]["approved"] = {"attempt": "a010", "seed": 11, "by": "cli", "on": "x"}
        bad = ss.stale(sp, at)
        self.assertNotIn("S2", bad)
        self.assertEqual([k for k in bad if k.startswith("S")], ["S3", "S4", "S5"])

    def test_missing_attempt_is_stale(self):
        sp, at = approved(spec())
        at["attempts"] = [a for a in at["attempts"] if a["id"] != "a003"]
        bad = ss.stale(sp, at)
        self.assertIn("S3", bad)
        self.assertIn("승인이 가리키는 시도 a003가 곁파일에 없다", bad["S3"])


class Board(unittest.TestCase):
    def test_status_labels(self):
        sp = spec()
        at = {"attempts": [{"id": "a001", "stage": "S1", "seeds": [11], "prompt": "pS1",
                            "neg": ["nS1"], "region": list(sp["regions"]["full"]),
                            "upstream": None, "images": {}}]}
        rows = {r["id"]: r["status"] for r in ss.board(sp, at)["stages"]}
        self.assertEqual(rows["S1"], "시도 있음")
        self.assertEqual(rows["S2"], "미시도")

        sp2, at2 = approved(spec())
        self.assertTrue(all(r["status"] == "승인" for r in ss.board(sp2, at2)["stages"]))
        sp2["stages"][3]["prompt"] = "고친 문구"
        rows2 = {r["id"]: r["status"] for r in ss.board(sp2, at2)["stages"]}
        self.assertEqual(rows2["S4"], "재검토")
        self.assertEqual(rows2["S3"], "승인")


if __name__ == "__main__":
    unittest.main()
