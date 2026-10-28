#!/usr/bin/env python3
"""LoRA 화풍 지키기(task 447, notes/LORA-STYLE.md 고정 절) — v4 어댑터는 그대로, 생성 쪽 두 수단을 기브아 창 시드 11 한 장으로.
  $VENV gen_lora_style.py scene            # C·L·K5·K3(앞 k스텝만 LoRA) → R(L → LoRA 없이 img2img 0.35) · 토큰 기록
  $VENV gen_lora_style.py heads            # OWLv2 머리 상자 → 원래 화소 3배 머리 둘레
  python3 gen_lora_style.py page | record '<답>'
그림은 레포 밖 ~/.local/biblemap-imggen/lora-style/, 수치는 samples/lora-style/metrics.json. 생성 프로세스는 한 번에 하나."""
import json, os, re, subprocess, sys

from PIL import Image

import gen_lora_v4 as V4

HERE = V4.HERE
OUT = os.path.join(V4.ROOT, "lora-style")
SAMP = os.path.join(HERE, "samples", "lora-style")
METRICS = os.path.join(SAMP, "metrics.json")
PAGE = os.path.join(V4.ROOT, "pages", "lora-style.html")
SEED = 11
MAP = {"saul-elder": ("saul_bm", "saul-v4"), "david-youth": ("davidy_bm", "david-youth-v4")}   # 장면 cast → (트리거, 어댑터)
NAME = {"saul-elder": "사울", "david-youth": "다윗"}
KSTEPS = {"L": 9, "K5": 5, "K3": 3}   # LoRA를 거는 앞 스텝 수(9스텝 중)
R_STRENGTH = 0.35
HEAD_FRAME = 3   # 머리 둘레 = 머리 전체 상자 긴 변 × 3 정사각
ASKED = ("K3", "K5", "R", "L")        # 사람 화면 갈래(C는 기준)


def load():
    return json.load(open(METRICS, encoding="utf-8")) if os.path.exists(METRICS) else {}


def save(m):
    os.makedirs(SAMP, exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def png(arm):
    return os.path.join(OUT, "scene", f"{arm}-s{SEED}.png")


def scene_prompt(lora):
    """route_prompt(지금 명세)에서 LoRA 인물 cast 서술 앞에만 트리거 낱말 — gen_lora_v4.scene_prompt와 같고 매핑만 saul-elder."""
    spec = V4.ds.load(V4.SID)
    p = V4.ds.route_prompt(spec)
    if lora:
        for f in spec["figures"]:
            d = V4.ds.cast_describe(V4.ds._cast_in_scene(f)).rsplit(", in ", 1)[0]
            assert p.count(d) == 1, (f["cast"], p.count(d))
            p = p.replace(d, f"{MAP[f['cast']][0]}, {d}")
    return p


def scene():
    import check_scenes
    n = check_scenes.zimage_tokens()
    loras = [a for _, a in MAP.values()]
    base = {"seed": SEED, "w": 1216, "h": 640}
    gen = [base | {"arm": "C", "prompt": scene_prompt(False), "loras": [], "out": png("C")}]
    gen += [base | {"arm": a, "prompt": scene_prompt(True), "loras": loras, "scale": 1.0, "k": k, "out": png(a)} for a, k in KSTEPS.items()]
    r = [base | {"arm": "R", "prompt": scene_prompt(False), "loras": [], "src": png("L"), "strength": R_STRENGTH, "out": png("R")}]
    rows = [{"arm": j["arm"], "seed": SEED, "tokens": n(j["prompt"]), "out": j["out"]} for j in gen + r]
    m = load()
    m["scene"] = rows
    save(m)
    over = [x for x in rows if x["tokens"] > 512]
    if over:
        sys.exit(f"[LoraStyle] 토큰 > 512 — 생성 안 함(벽): {sorted({x['tokens'] for x in over})}")
    log = {}
    for jobs, name in ((gen, "gen"), (r, "r")):
        log |= {x["out"]: x for x in run_jobs(jobs, os.path.join(OUT, f"{name}-jobs.json"))}
    m = load()
    for x in m["scene"]:
        x |= {k: log[x["out"]][k] for k in ("secs", "active", "lora_steps") if x["out"] in log}
    save(m)
    print("[LoraStyle] " + " · ".join(f"{x['arm']} {x['tokens']}토큰 {x.get('secs')}s LoRA {x.get('lora_steps')}" for x in m["scene"]), flush=True)


def run_jobs(jobs, path):
    """LoRA 없는 작업 먼저 → venv 워커 enc·gen(gen_lora_v4.run_jobs와 같은 두 프로세스) → 로그 목록."""
    jobs = sorted([j for j in jobs if not os.path.exists(j["out"])], key=lambda j: bool(j["loras"]))
    if jobs:
        os.makedirs(os.path.dirname(jobs[0]["out"]), exist_ok=True)
        json.dump(jobs, open(path, "w"), ensure_ascii=False, indent=1)
        print(f"[LoraStyle] 생성 {len(jobs)}장", flush=True)
        for mode in ("enc", "gen"):
            subprocess.run([sys.executable, os.path.abspath(__file__), "worker-" + mode, path], check=True)
    return json.load(open(path + ".log.json")) if os.path.exists(path + ".log.json") else []


def worker(mode, path):
    """gen_lora_v4.worker에 단계 나눔만 더함 — 앞 k스텝 뒤 콜백에서 어댑터 세기를 0으로. LoRA 건 스텝을 실제로 세어 기록."""
    if mode == "enc":
        return V4.worker(mode, path)
    import time
    import torch
    torch.set_grad_enabled(False)
    import run_scene as rs
    from diffusers import GGUFQuantizationConfig, ZImageImg2ImgPipeline, ZImagePipeline, ZImageTransformer2DModel
    from diffusers.models.model_loading_utils import load_gguf_checkpoint
    from huggingface_hub import hf_hub_download
    jobs = json.load(open(path))
    sd = load_gguf_checkpoint(hf_hub_download(rs.ZI_GGUF, "z_image_turbo-Q8_0.gguf"))
    for k in ("cap_pad_token", "x_pad_token"):     # ZIMAGE.md: GGUF 로드 우회 2줄
        sd[k] = sd[k].reshape(1, -1)
    tr = ZImageTransformer2DModel.from_single_file(sd, quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
                                                   config=rs.ZI_BASE, subfolder="transformer", torch_dtype=torch.bfloat16)
    cls = ZImageImg2ImgPipeline if "src" in jobs[0] else ZImagePipeline
    pipe = cls.from_pretrained(rs.ZI_BASE, transformer=tr, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16).to("mps")
    pipe.set_progress_bar_config(disable=True)
    loaded, log = set(), []
    for j, e in zip(jobs, torch.load(path + ".emb.pt")):
        for n in j["loras"]:
            if n not in loaded:
                pipe.load_lora_weights(os.path.join(V4.ROOT, "lora", f"{n}.safetensors"), adapter_name=n)
                loaded.add(n)
        on = []   # LoRA가 걸린 채 끝난 스텝 번호(1부터)

        def step_end(p, i, t, kw, j=j, on=on):
            if j["loras"] and len(on) < j["k"]:
                on.append(i + 1)
                if len(on) == j["k"]:
                    p.set_adapters(j["loras"], adapter_weights=[0.0] * len(j["loras"]))
            return kw

        if j["loras"]:
            pipe.set_adapters(j["loras"], adapter_weights=[j["scale"]] * len(j["loras"]))
        elif loaded:
            pipe.disable_lora()
        kw = {"prompt_embeds": [x.to("mps", torch.bfloat16) for x in e], "width": j["w"], "height": j["h"], "num_inference_steps": 9,
              "guidance_scale": 0.0, "generator": torch.Generator("mps").manual_seed(j["seed"]), "callback_on_step_end": step_end}
        if "src" in j:
            kw |= {"image": Image.open(j["src"]).convert("RGB"), "strength": j["strength"]}
        t = time.time()
        pipe(**kw).images[0].save(j["out"])
        log.append({"out": j["out"], "secs": round(time.time() - t, 1), "active": pipe.get_active_adapters() if j["loras"] else [], "lora_steps": on})
        print(f"  [LoraStyle] {os.path.relpath(j['out'], V4.ROOT)} {log[-1]['secs']}s {log[-1]['active']} LoRA 스텝 {on}", flush=True)
        json.dump(log, open(path + ".log.json", "w"), ensure_ascii=False)


def heads():
    """OWLv2 후보 중 가장 큰 상자(머리털까지 든 머리 전체 — 갈래마다 일관됨, 2026-10-28 실측) → 긴 변 × HEAD_FRAME 정사각을 원래 화소로.
    face_ab_heads.heads()는 점수 1위를 써서 C 다윗만 머리 전체·나머지는 얼굴만 잡혔다(0.07 대 0.08 — 기준이 엇갈림)."""
    import face_ab_heads as fh
    m = load()
    m["heads"] = {}
    for x in m["scene"]:
        im = Image.open(x["out"]).convert("RGB")
        f = [b for b, s in fh._faces(im) if s >= 0.05]
        m["heads"][x["arm"]] = {}
        for w, (lo, hi) in {"david-youth": (0, 0.5), "saul-elder": (0.5, 1)}.items():   # 기브아 창: 다윗 왼쪽(수금)·사울 오른쪽(창)
            b = max((b for b in f if lo * im.width <= (b[0] + b[2]) / 2 < hi * im.width), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            s = round(max(b[2] - b[0], b[3] - b[1]) * HEAD_FRAME)
            x0 = min(max(0, round((b[0] + b[2] - s) / 2)), im.width - s)
            y0 = min(max(0, round((b[1] + b[3] - s) / 2)), im.height - s)
            m["heads"][x["arm"]][w] = [round(v) for v in b] + [s]
            os.makedirs(os.path.join(OUT, "heads"), exist_ok=True)
            im.crop((x0, y0, x0 + s, y0 + s)).save(os.path.join(OUT, "heads", f"{x['arm']}-s{SEED}-{w}.png"))
        print(x["arm"], m["heads"][x["arm"]], flush=True)
    save(m)


def page():
    import random
    import make_face_judge_v2 as F
    qs, key = [], {}
    for arm in ASKED:
        for w in MAP:
            c, a = (Image.open(os.path.join(OUT, "heads", f"{x}-s{SEED}-{w}.png")) for x in ("C", arm))
            # 머리 하나에 든 화소를 같게: 갈래 크롭을 C 크롭 화소 수로 줄인 뒤 둘 다 같은 배율로 640px(2026-10-28 v3).
            # v2의 hf 맞춤은 갈래만 75~86%로 줄였다 2배 키워 「기준이 화질이 높아」 — 선명도 숫자가 같아도 해상도가 달랐다.
            n = c.width
            c, a = F.up(c), F.up(a.resize((n, n), Image.LANCZOS))
            qs.append({"arm": arm, "who": w, "tag": "화풍", "wide": True, "q": f"{NAME[w]} 머리 둘레 — 아래 그림이 위(기준)와 같은 화풍인가요?",
                       "hint": "같은 장면·같은 시드에서 머리 크기와 화소 수를 맞춰 같은 배율로 키웠습니다. 연필 선 모양·색연필 결·색 진함이 같은지만 봅니다(같은 사람인지는 묻지 않습니다).",
                       "yes": "같은 화풍", "no": "다른 화풍", "refs": [F.uri(c, 900)], "caps": ["기준 — 인물 학습 없이 그린 그림"], "img": F.uri(a, 900),
                       "hf": [round(F.hf(a), 2), round(F.hf(c), 2), n]})
    random.Random(1447).shuffle(qs)
    for i, q in enumerate(qs, 1):   # 갈래 이름은 화면·답에 안 나오게 문항 번호로만
        key[f"Q{i}"] = [q.pop("arm"), q.pop("who")]
        q["id"] = f"Q{i}"
    verses = [[r, t, r == "18:11"] for r, t, _ in F.scripture() if r in ("18:10", "18:11")]
    html = (F.page(qs, verses).replace("<title>얼굴 판정 v2</title>", "<title>LoRA 화풍 판정</title>")
            .replace("판정 face-judge-v2", "판정 lora-style").replace("18:6-11", "18:10-11")
            .replace(".refs figure.one { max-width: 320px; margin: 0 auto }", ".refs figure.one { margin: 0 }"))   # 기준·판정 그림 같은 화면 크기
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    open(PAGE, "w", encoding="utf-8").write(html)
    m = load()
    m["page"] = {"path": PAGE, "n": len(qs), "key": key, "mb": round(os.path.getsize(PAGE) / 1e6, 2)}
    save(m)
    print(PAGE, len(qs), "문항", m["page"]["mb"], "MB")


def tally(ans, key):
    """→ (갈래별 {인물: 답}, 화풍 통과 갈래) — 고정 절 채택 규칙: 두 머리 모두 「같은 화풍」(yes)이면 통과."""
    by = {}
    for q, (arm, w) in key.items():
        by.setdefault(arm, {})[w] = ans.get(q)
    return by, [a for a in ASKED if all(v == "yes" for v in by.get(a, {}).values()) and len(by.get(a, {})) == len(MAP)]


def record(text):
    ans = json.loads(re.search(r"\{.*?\}", text.split("판정 lora-style", 1)[-1], re.S).group(0))
    m = load()
    by, ok = tally(ans, m["page"]["key"])
    tools = [a for a in ok if a != "L"]
    v = f"화풍 통과 {', '.join(tools)} → 다음 작업 얼굴 판정 후보" if tools else "이 수단 미채택(K3·K5·R 통과 0) → 참조 어댑터 외부 조사"
    if "L" in ok:
        v += " · L도 통과 — 445(2/2 다름)와 어긋남: 판정이 너그러움 / 시드 탓"
    m["verdict"] = {"answers": by, "pass": ok, "line": v}
    save(m)
    open(os.path.join(SAMP, "verdict.txt"), "w", encoding="utf-8").write(text.strip() + "\n")
    print(f"판정: {v}\n{json.dumps(by, ensure_ascii=False)}")


if __name__ == "__main__":
    a = sys.argv[1]
    if a.startswith("worker-"):
        worker(a[7:], sys.argv[2])
    elif a == "record":
        record(sys.argv[2])
    else:
        {"scene": scene, "heads": heads, "page": page}[a]()
