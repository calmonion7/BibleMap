#!/usr/bin/env python3
"""task#346 S2 — 얼굴 닮음 자: 큰 얼굴 우대 제거 + 척도 불변 검사.

머리 검출(claude -p VLM이 머리 상자를 읽는다 — 연필 스케치에서도 동작, 상업 허용 구독 도구)
→ 정본·후보 모두 같은 비율(params.FACE_SCALE_HEAD_MARGIN)로 크롭 → 정본을 후보 얼굴의 원래 픽셀 크기로
열화 → 같은 크기(224)로 정규화 → CLIP(bigG) 코사인 → 다른 인물 정본(같은 열화) 평균 코사인을 뺀 마진(열화 공통 상승분 상쇄).

척도 불변 검사: (a) 같은 그림을 얼굴 크기만 바꿔 넣었을 때 점수 폭 ≤ FACE_SCALE_SPREAD_MAX,
(b) 후보 풀에서 log(얼굴 크기)–점수 |r| ≤ FACE_SCALE_CORR_MAX. 통과 exit 0 / 실패 exit 1.

Usage: check_face_scale.py [--who david] [--canon PATH] [--pool 'GLOB' ...]
다른 단계가 쓰는 함수: face_score(canon_img, cand_img, cand_box, embedder), detect_head(path)
"""
import argparse, glob, hashlib, json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

import params

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(REPO, ".forge", "reports", "face-ab", "heads.json")
DEFAULT_POOL = [".forge/reports/scene-batch-pilot/*/cand/{who}-s*.png",
                ".forge/reports/scene-batch-pilot/_ab/*/*/cand/{who}-s*.png"]

PROMPT = ("Read 도구로 이미지 파일 {img} 를 보라. 이 그림에서 가장 크게 나온 사람 한 명의 머리(머리카락·턱 전체, 목 제외) "
          "상자를 이미지 전체를 0~1000으로 정규화한 좌표로 답하라. 사람이 없거나 머리가 안 보이면 null. "
          'JSON 한 개만 출력: {{"box": [x0, y0, x1, y1]}} 또는 {{"box": null}}')


def _cache():
    try:
        with open(CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def detect_head(path):
    """머리 상자 (x0,y0,x1,y1) 픽셀 또는 None. 내용 해시로 캐시(재호출 비용 절감)."""
    path = os.path.abspath(path)
    key = hashlib.md5(open(path, "rb").read()).hexdigest()
    c = _cache()
    if key not in c:
        out = subprocess.run(["claude", "-p", PROMPT.format(img=path), "--output-format", "text",
                              "--allowedTools", "Read", "--add-dir", os.path.dirname(path)],
                             capture_output=True, text=True, cwd=tempfile.gettempdir(), timeout=300).stdout
        m = re.search(r"\{.*\}", out, re.S)
        try:
            box = json.loads(m.group(0))["box"] if m else None
        except (ValueError, KeyError):
            box = None
        c = _cache()
        c[key] = box
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as fh:
            json.dump(c, fh)
    box = c[key]
    if not box or len(box) != 4:
        return None
    w, h = Image.open(path).size
    x0, y0, x1, y1 = box
    if not (x1 > x0 and y1 > y0):
        return None
    return (x0 * w / 1000, y0 * h / 1000, x1 * w / 1000, y1 * h / 1000)


def head_crop(im, box):
    """머리 상자를 마진 포함 정사각 크롭(경계 밖은 흰색 패딩). 반환: (크롭, 얼굴 한 변 px)."""
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0) * (1 + 2 * params.FACE_SCALE_HEAD_MARGIN)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    l, t = int(round(cx - side / 2)), int(round(cy - side / 2))
    s = max(1, int(round(side)))
    canvas = Image.new("RGB", (s, s), (255, 255, 255))
    canvas.paste(im.convert("RGB"), (-l, -t))
    return canvas, max(x1 - x0, y1 - y0)


def degrade(im, px):
    """px 한 변으로 줄였다가 224로 되돌린다 — 후보 얼굴의 원래 해상도를 정본에도 입힌다."""
    px = min(params.FACE_SCALE_DEGRADE_MAX_PX, max(4, int(round(px))))
    return im.resize((px, px), Image.LANCZOS).resize((224, 224), Image.BICUBIC)


def margin(cand_crop, px, canon_crop, other_crops, embedder):
    """정본과의 코사인에서 다른 인물 정본들(같은 열화)과의 평균 코사인을 뺀 마진.
    둘 다 후보 얼굴 해상도 px로 열화한다. 열화가 심할수록 모든 쌍이 닮아 보이는 공통 상승분을 마진이 상쇄한다."""
    import judge_metrics as jm
    a = embedder.embed(degrade(cand_crop, px))
    own = jm.cos(a, embedder.embed(degrade(canon_crop, px)))
    oth = [jm.cos(a, embedder.embed(degrade(o, px))) for o in other_crops]
    return own - float(np.mean(oth)) if oth else own


def face_score(canon_img, cand_img, cand_box, embedder, canon_box=None, others=()):
    """정본 얼굴 대비 후보 얼굴의 마진 점수와 얼굴 한 변 px. canon_box None이면 정본 전체가 얼굴 크롭.
    others: 다른 인물 정본 PIL 이미지들(전체가 얼굴 크롭)."""
    cc, face_px = head_crop(cand_img, cand_box)
    canon = head_crop(canon_img, canon_box)[0] if canon_box else canon_img.convert("RGB")
    return margin(cc, face_px, canon, [o.convert("RGB") for o in others], embedder), face_px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default="david")
    ap.add_argument("--canon", help="정본 PNG(기본 frozen/<who>.png)")
    ap.add_argument("--others", nargs="*", default=["jonathan", "samuel", "abner", "joab", "nathan", "absalom"],
                    help="마진 기준용 다른 인물 정본 키(frozen/<키>.png, 정본과 같은 폴더)")
    ap.add_argument("--pool", nargs="*", help="후보 풀 glob(레포 루트 기준)")
    a = ap.parse_args()
    canon_path = a.canon or os.path.join(HERE, "frozen", f"{a.who}.png")
    canon_img = Image.open(canon_path)
    canon_box = detect_head(canon_path)
    print(f"[정본] {canon_path} 머리 상자 {canon_box}")
    if canon_box is None:
        print("정본 머리 검출 실패"); return 1
    cdir = os.path.dirname(os.path.abspath(canon_path))
    others = [Image.open(os.path.join(cdir, f"{k}.png")).convert("RGB") for k in a.others
              if k != a.who and os.path.exists(os.path.join(cdir, f"{k}.png"))]
    files = sorted({f for g in (a.pool or [p.format(who=a.who) for p in DEFAULT_POOL])
                    for f in glob.glob(os.path.join(REPO, g))})
    with ThreadPoolExecutor(4) as ex:
        boxes = list(ex.map(detect_head, files))
    pool = [(f, b) for f, b in zip(files, boxes) if b]
    print(f"[검출] 후보 {len(files)}장 중 머리 검출 {len(pool)}장 (검출률 {len(pool)/max(1,len(files)):.0%})")

    import judge_metrics as jm
    emb = jm.Embedder()

    # (a) 같은 그림 얼굴 크기만 바꾸기 — 후보 풀 전체의 크기별 평균 점수 폭(한 장만 보면 그림 고유 잡음이 섞인다)
    spread = None
    if pool:
        canon_crop = head_crop(canon_img, canon_box)[0]
        crops = [head_crop(Image.open(f), b)[0] for f, b in pool]
        fixed = [float(np.mean([margin(cc.resize((s, s), Image.LANCZOS), s, canon_crop, others, emb) for cc in crops]))
                 for s in params.FACE_SCALE_SIZES]
        spread = max(fixed) - min(fixed)
        print(f"(a) 크기 {params.FACE_SCALE_SIZES} 풀 {len(crops)}장 평균 점수 {[round(x, 3) for x in fixed]}")
        print(f"(a) 점수 폭 측정 {spread:.3f} / 임계 FACE_SCALE_SPREAD_MAX={params.FACE_SCALE_SPREAD_MAX}")

    # (b) 후보 풀 얼굴 크기–점수 상관
    sc = [face_score(canon_img, Image.open(f), b, emb, canon_box, others) for f, b in pool]
    r = None
    if len(sc) >= params.FACE_SCALE_POOL_MIN:
        v, px = np.array([s[0] for s in sc]), np.log([s[1] for s in sc])
        r = float(np.corrcoef(px, v)[0, 1]) if px.std() > 0 and v.std() > 0 else 0.0
        print(f"(b) 풀 {len(sc)}장 얼굴 한 변 {min(np.exp(px)):.0f}~{max(np.exp(px)):.0f}px, 점수 {v.min():.3f}~{v.max():.3f}")
        print(f"(b) log(크기)–점수 r 측정 {r:.3f} / 임계 |r|<=FACE_SCALE_CORR_MAX={params.FACE_SCALE_CORR_MAX}")
    else:
        print(f"(b) 검출 {len(sc)}장 < FACE_SCALE_POOL_MIN={params.FACE_SCALE_POOL_MIN} — 검사 불성립")
    ok_a = spread is not None and spread <= params.FACE_SCALE_SPREAD_MAX
    ok_b = r is not None and abs(r) <= params.FACE_SCALE_CORR_MAX
    print(f"척도 불변: (a) {'PASS' if ok_a else 'FAIL'} (b) {'PASS' if ok_b else 'FAIL'}")
    return 0 if ok_a and ok_b else 1


if __name__ == "__main__":
    sys.exit(main())
