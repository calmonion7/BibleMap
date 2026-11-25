"""task 7194 — 고른 장(klein으로 지물을 넣은 장)을 통째로 같은 생성기(Z-Image) i2i로 낮은 세기로 다시 그려 붓 결을 한 장으로 잇는다.

klein 넣기는 크롭을 1024로 키워 다시 그려 그 부분만 붓 결·세부 크기가 달라 「확대화면을 붙여 넣은」 그림이 된다(성전 봉헌 사람 7192).
세기 0.3이면 인물·자세·무리 시선은 그대로 두고 붓 결만 이어짐 · 0.4~0.5는 뒤 배경이 바뀜(뾰족 지붕·유화풍 — 7194).

쓰는 법: ~/.local/biblemap-imggen/.venv314/bin/python batch/whole_i2i.py <장면 id> <바탕.png> <출력 폴더> [세기,… [시드,…]]
"""
import os
import shutil
import sys

C = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, C)
sys.path.insert(0, os.path.join(C, "batch"))


def main():
    import derive_scene as ds
    import run_scene
    from PIL import Image
    sid, base, out = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    strengths = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else [0.3]
    seeds = [int(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else [42, 7]
    os.makedirs(out, exist_ok=True)
    src = os.path.join(out, "src.png")
    if not os.path.exists(src):
        shutil.copy(base, src)
    w, h = Image.open(src).size
    prompt = ds.whole_prompt(ds.load(sid))
    jobs = [{"prompt": prompt, "seed": s, "w": w, "h": h, "src": src, "strength": st, "out": os.path.join(out, f"u-{st}-s{s}.png"), "loras": []}
            for st in strengths for s in seeds if not os.path.exists(os.path.join(out, f"u-{st}-s{s}.png"))]
    tmp = os.path.expanduser(f"~/.local/biblemap-imggen/{os.path.basename(out)}")
    os.makedirs(tmp, exist_ok=True)
    if jobs:
        print("[WholeI2I]", len(jobs), "장", run_scene.gen_zimage(jobs, tmp, "i2i"), flush=True)


if __name__ == "__main__":
    main()
