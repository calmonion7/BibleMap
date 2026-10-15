#!/usr/bin/env python3
"""task#346 S3 — 시트 기계 선별: CLIP 마진(check_face_scale.face_score) 1차 → VLM 같은 사람(check_face_judge.same_person) 2차.

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV select_face_sheet.py --who saul [--root ~/.local/biblemap-imggen/face-ab]

<root>/cand-<인물>/ 후보 → <root>/sheet-<인물>/NN.png + NN.txt(학습용 캡션) + select.json(점수·판정). 사람 선별 없음.
"""
import argparse, glob, json, os, shutil, tempfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

import params
import check_face_scale as cs
import check_face_judge as cj

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", required=True)
    ap.add_argument("--root", default=os.path.expanduser("~/.local/biblemap-imggen/face-ab"))
    a = ap.parse_args()
    frozen = os.path.join(HERE, "frozen")
    canon_path = os.path.join(frozen, f"{a.who}.png")
    canon = Image.open(canon_path)
    others = [Image.open(os.path.join(frozen, f"{k}.png")) for k in ("jonathan", "samuel", "abner", "joab", "nathan", "absalom")
              if os.path.exists(os.path.join(frozen, f"{k}.png"))]
    files = sorted(glob.glob(os.path.join(a.root, f"cand-{a.who}", "[0-9][0-9].png")))
    with ThreadPoolExecutor(4) as ex:
        boxes = list(ex.map(cs.detect_head, files))
    import judge_metrics as jm
    emb = jm.Embedder()
    rows = []
    for f, b in zip(files, boxes):
        if not b:
            print(f"[검출 실패] {os.path.basename(f)}"); continue
        s, px = cs.face_score(canon, Image.open(f), b, emb, others=others)
        rows.append({"file": f, "score": round(s, 4), "face_px": round(px), "box": b})
    rows.sort(key=lambda r: -r["score"])
    stage1 = rows[:params.FACE_SHEET_STAGE1]
    print(f"[1차] 검출 {len(rows)}/{len(files)}장 → 상위 {len(stage1)}장 (점수 {stage1[-1]['score']}~{stage1[0]['score']})")
    tmp = tempfile.mkdtemp(prefix="sheet-")

    def judge(r):
        crop = cs.head_crop(Image.open(r["file"]), tuple(r["box"]))[0].resize((512, 512))
        p = os.path.join(tmp, os.path.basename(r["file"]))
        crop.save(p)
        return cj.same_person(p, canon_path)
    with ThreadPoolExecutor(4) as ex:
        for r, d in zip(stage1, ex.map(judge, stage1)):
            r["same"], r["reason"] = d["same"], d["reason"]
            print(f"  {os.path.basename(r['file'])} 점수 {r['score']} 얼굴 {r['face_px']}px 같은사람 {d['same']} — {d['reason']}")
    final = [r for r in stage1 if r["same"]][:params.FACE_SHEET_STAGE2]
    out = os.path.join(a.root, f"sheet-{a.who}")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for i, r in enumerate(final, 1):
        shutil.copy(r["file"], os.path.join(out, f"{i:02d}.png"))
        shutil.copy(r["file"][:-4] + ".txt", os.path.join(out, f"{i:02d}.txt"))
        r["sheet"] = f"{i:02d}"
    json.dump({"all": rows, "stage1": len(stage1), "final": len(final)}, open(os.path.join(out, "select.json"), "w"), ensure_ascii=False, indent=1)
    print(f"[2차] 최종 {len(final)}장 → {out}")
