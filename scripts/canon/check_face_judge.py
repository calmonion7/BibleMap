#!/usr/bin/env python3
"""task#346 S2 — VLM 「같은 사람인가」 판정자 교정.

다른 인물 정본 쌍은 기각, 정본의 가벼운 변형(좌우 반전·밝기·축소)은 통과해야 한다.
출력: `REJECT_OTHER: PASS|FAIL`, `ACCEPT_VARIANT: PASS|FAIL`(변형 종류별 통과도 따로 집계). 둘 다 PASS면 exit 0.
다른 단계가 쓰는 함수: same_person(path_a, path_b) -> {"same": bool, "reason": str}

Usage: check_face_judge.py [--canon-dir DIR] [--whos saul david] [--others jonathan samuel abner ...]
"""
import argparse, json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageEnhance, ImageOps

import params

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = ("Read 도구로 이미지 두 장 {a} 와 {b} 를 보라. 성경 삽화 속 얼굴이다. 두 그림이 같은 한 사람(같은 얼굴 구조: 눈·코·입 비율, "
          "수염·머리 모양, 나이대)인지 엄격히 판정하라. 그림 크기·밝기·좌우 방향 차이는 무시하고 얼굴 자체만 본다. "
          '설명 없이 JSON 한 개만: {{"same": true|false, "reason": "한국어 한 문장"}}')


def same_person(path_a, path_b):
    a, b = os.path.abspath(path_a), os.path.abspath(path_b)
    for _ in range(2):
        out = subprocess.run(["claude", "-p", PROMPT.format(a=a, b=b), "--output-format", "text", "--allowedTools", "Read",
                              "--add-dir", os.path.dirname(a), "--add-dir", os.path.dirname(b)],
                             capture_output=True, text=True, cwd=tempfile.gettempdir(), timeout=300).stdout
        m = re.search(r"\{.*\}", out, re.S)
        try:
            d = json.loads(m.group(0))
            if "same" in d:
                return d
        except (ValueError, AttributeError):
            pass
    return {"same": None, "reason": "판정 출력 파싱 실패"}


VARIANTS = {
    "flip": lambda im: ImageOps.mirror(im),
    "bright": lambda im: ImageEnhance.Brightness(im).enhance(1.3),
    "shrink": lambda im: im.resize((max(32, im.width // 3), max(32, im.height // 3)), Image.LANCZOS),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon-dir", default=os.path.join(HERE, "frozen"))
    ap.add_argument("--whos", nargs="+", default=["saul", "david"])
    ap.add_argument("--others", nargs="+", default=["jonathan", "samuel", "abner", "joab", "nathan", "absalom"])
    a = ap.parse_args()
    P = lambda k: os.path.join(a.canon_dir, f"{k}.png")
    tmp = tempfile.mkdtemp(prefix="facejudge-")
    jobs = []  # (종류, 라벨, 경로a, 경로b)
    for w in a.whos:
        for o in a.others:
            if o != w and os.path.exists(P(o)):
                jobs.append(("other", f"{w} vs {o}", P(w), P(o)))
        for name, fn in VARIANTS.items():
            vp = os.path.join(tmp, f"{w}-{name}.png")
            fn(Image.open(P(w)).convert("RGB")).save(vp)
            jobs.append((name, f"{w} vs {w}-{name}", P(w), vp))
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: same_person(j[2], j[3]), jobs))
    for j, r in zip(jobs, res):
        print(f"  [{j[0]}] {j[1]}: same={r['same']} — {r['reason']}")
    oth = [r["same"] is False for j, r in zip(jobs, res) if j[0] == "other"]
    var = [r["same"] is True for j, r in zip(jobs, res) if j[0] != "other"]
    for name in VARIANTS:  # 좋음 기준 통과 — 변형 종류별 따로 집계
        v = [r["same"] is True for j, r in zip(jobs, res) if j[0] == name]
        print(f"  변형 {name} 통과 {sum(v)}/{len(v)}")
    ro, rv = sum(oth) / max(1, len(oth)), sum(var) / max(1, len(var))
    po, pv = ro >= params.FACE_JUDGE_REJECT_MIN, rv >= params.FACE_JUDGE_ACCEPT_MIN
    print(f"다른 인물 기각률 {sum(oth)}/{len(oth)}={ro:.2f} (임계 FACE_JUDGE_REJECT_MIN={params.FACE_JUDGE_REJECT_MIN})")
    print(f"변형 통과율 {sum(var)}/{len(var)}={rv:.2f} (임계 FACE_JUDGE_ACCEPT_MIN={params.FACE_JUDGE_ACCEPT_MIN})")
    print(f"REJECT_OTHER: {'PASS' if po else 'FAIL'}")
    print(f"ACCEPT_VARIANT: {'PASS' if pv else 'FAIL'}")
    return 0 if po and pv else 1


if __name__ == "__main__":
    sys.exit(main())
