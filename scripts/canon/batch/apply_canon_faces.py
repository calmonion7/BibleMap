#!/usr/bin/env python3
"""규칙 spec.cast-canon-face 수리 — 사람 답(make_canon_face_page.py 화면의 「판정 task canon-faces」)을 정본에 반영(2026-10-27).

  python3 batch/apply_canon_faces.py '<판정 task canon-faces + JSON 한 줄>' [--dir ~/.local/biblemap-imggen/face-canon-v3]

시드를 고른 사람: 옛 frozen/<id>.png는 retired-vN/<id>.png(비어 있는 가장 낮은 N)로 옮기고, 고른 정면을 frozen/<id>.png로,
카드 canon_face(prompt_sha 포함)를 적는다. keep·none·미답은 손대지 않고 목록으로만 낸다(규칙은 계속 걸림).
"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import gen_face_canon as gfc

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--dir", default=os.path.expanduser("~/.local/biblemap-imggen/face-canon-v3"))
    a = ap.parse_args()
    v = json.loads(a.text.split("\n", 1)[1].strip().splitlines()[0])
    memo = v.pop("_memo", "")
    left = {}
    for cid, pick in v.items():
        if not pick.startswith("s"):
            left[cid] = pick
            continue
        src = os.path.join(a.dir, cid, f"{pick}-front.png")
        dst = os.path.join(HERE, "frozen", f"{cid}.png")
        retired = None
        if os.path.exists(dst):
            n = 1
            while os.path.exists(os.path.join(HERE, "frozen", f"retired-v{n}", f"{cid}.png")):
                n += 1
            retired = f"frozen/retired-v{n}/{cid}.png"
            os.makedirs(os.path.dirname(os.path.join(HERE, retired)), exist_ok=True)
            shutil.move(dst, os.path.join(HERE, retired))
        shutil.copyfile(src, dst)
        p = os.path.join(HERE, "cast", f"{cid}.json")
        c = json.load(open(p, encoding="utf-8"))
        c["canon_face"] = {"engine": "z-image-turbo", "seed": int(pick[1:]), "views": ["front", "34"], "file": f"frozen/{cid}.png",
                           "script": "scripts/canon/gen_face_canon.py", "prompt": "gen_face_canon.prompt(id, view) — cast-vocab-2 카드·얼굴 층에서 파생",
                           "prompt_sha": gfc.prompt_sha(cid), "size": "768x768", "task": "canon-faces (2026-10-27, 규칙 spec.cast-canon-face)",
                           **({"retired": retired} if retired else {}),
                           "approved": f"2026-10-27 사용자 판정 화면에서 {pick}" + (f" · 메모 「{memo}」" if memo else "")}
        open(p, "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=2) + "\n")
        print(f"[CanonFace] {cid} ← {pick}" + (f" (옛 판 {retired})" if retired else ""))
    if left:
        print("[CanonFace] 손대지 않음:", json.dumps(left, ensure_ascii=False))
    if memo:
        print(f"[CanonFace] 메모: {memo}")
