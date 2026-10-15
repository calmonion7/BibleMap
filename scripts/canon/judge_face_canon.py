#!/usr/bin/env python3
"""task#346 S1 — 얼굴 정본 후보 판정: ① 후보별 어휘 정본 부합 점수 → ② 인물별 상위 3장 중 상대 인물과 가장 구별되는 쌍 선택.

  python3 judge_face_canon.py [--dir ~/.local/biblemap-imggen/face-canon]      # <dir>/judge.json 저장
판정은 `claude -p`(cwd는 프로젝트 밖 — judge_vlm._claude)로 한다. 선택 결과만 stdout에 낸다.
"""
import argparse, glob, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "batch"))
import judge_vlm

TOP = 3
RUBRIC = ("기대 정본({cid}): {vocab}. 보조 인상: {look}.\n"
          "채점 0~10(소수 허용): vocab=시대·나이·머리·수염·복식이 정본과 맞는가(머리숱 없이 대머리면 hair 불일치로 크게 감점), "
          "style=손그린 연필·색연필 삽화풍인가, clean=얼굴 붕괴·비대칭·손상·글자·테두리 없이 이목구비가 선명한가, "
          "head=정면 머리 초상으로 머리 전체가 잘림 없이 들어오는가.")
PROMPT = ("너는 성경 삽화 얼굴 정본 후보의 엄격한 판정자다. Read 도구로 이미지 {img} 를 직접 보고 판정하라.\n{rubric}\n"
          '설명 없이 JSON 한 개만: {{"vocab":0,"style":0,"clean":0,"head":0,"reason":"한국어 한 문장"}}')
PAIR = ("너는 성경 삽화 판정자다. Read 도구로 이미지들을 직접 보라. 사울 후보(장년 왕) 3장: {s}. 다윗 후보(청년) 3장: {d}.\n"
        "사울 1장+다윗 1장 쌍 중, 서로 나이·얼굴형·수염·머리 모양이 가장 확연히 구별되면서 각자 정본 어휘(사울: 장년·검은 머리·짧은 검은 수염 / "
        "다윗: 청년·검은 곱슬머리·짧은 수염)에 잘 맞는 쌍을 하나 고르라. "
        '설명 없이 JSON 한 개만: {{"saul":"<파일명>","david":"<파일명>","distinct":0,"reason":"한국어 두 문장"}}')
# task#348 — 사울·다윗 정본은 이미 확정. 새 인물은 상위 3장 중 확정된 사울 정본과 가장 확연히 구별되는 1장을 고른다.
VS = ("너는 성경 삽화 판정자다. Read 도구로 이미지들을 직접 보라. 확정된 사울 정본(장년 왕): {ref}. {cid} 후보 3장: {c}.\n"
      "후보 중 사울 정본과 나이·얼굴형·수염·머리 모양이 가장 확연히 구별되면서 정본 어휘({vocab})에 잘 맞는 1장을 고르라. "
      '설명 없이 JSON 한 개만: {{"pick":"<파일명>","distinct":0,"reason":"한국어 두 문장"}}')


def ask(prompt, imgs):
    cmd = ["claude", "-p", prompt, "--output-format", "text", "--allowedTools", "Read"]
    for d in sorted({os.path.dirname(os.path.abspath(i)) for i in imgs}):
        cmd += ["--add-dir", d]
    for _ in range(2):
        out = subprocess.run(cmd, capture_output=True, text=True, cwd=tempfile.gettempdir(), timeout=300).stdout
        d = judge_vlm._json(out)
        if d:
            return d
    return None


def vocab(cid):
    c = json.load(open(os.path.join(HERE, "cast", f"{cid}.json"), encoding="utf-8"))
    return "; ".join(f"{k}: {c[k]}" for k in ("era", "age", "hair", "beard", "headwear", "costume") if c.get(k))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/.local/biblemap-imggen/face-canon"))
    ap.add_argument("--who", nargs="+", default=["saul", "david"])
    a = ap.parse_args()
    import gen_face_canon as g
    res = {"cands": {}, "pair": None}
    for cid in a.who:
        for p in sorted(glob.glob(os.path.join(a.dir, cid, "s*.png"))):
            d = ask(PROMPT.format(img=p, rubric=RUBRIC.format(cid=cid, vocab=vocab(cid), look=g.look(cid))), [p])
            if d:
                d["score"] = round(sum(d[k] for k in ("vocab", "style", "clean", "head")) / 4, 2)
            res["cands"][p] = d
            print(cid, os.path.basename(p), d, flush=True)
    top = {}
    for cid in a.who:
        ok = [(p, d) for p, d in res["cands"].items() if f"/{cid}/" in p and d]
        top[cid] = [p for p, _ in sorted(ok, key=lambda x: -x[1]["score"])[:TOP]]
    res["top"] = top
    if a.who == ["saul", "david"]:
        res["pair"] = ask(PAIR.format(s=", ".join(top["saul"]), d=", ".join(top["david"])), top["saul"] + top["david"])
        out = "judge.json"
    else:
        ref = os.path.join(HERE, "frozen", "saul.png")
        res["pair"] = {cid: ask(VS.format(ref=ref, cid=cid, c=", ".join(top[cid]), vocab=vocab(cid)), [ref] + top[cid]) for cid in a.who}
        out = f"judge-{'-'.join(a.who)}.json"
    json.dump(res, open(os.path.join(a.dir, out), "w"), ensure_ascii=False, indent=1)
    print("PAIR", json.dumps(res["pair"], ensure_ascii=False))
