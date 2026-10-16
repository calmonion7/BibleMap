#!/usr/bin/env python3
"""2511 + Lightning 4스텝 LoRA 첫 1장 시험(task#359 뒤 후속 — 판정 아님, 속도·조작 확인만).

  VENV=~/.local/biblemap-imggen/.venv314/bin/python
  $VENV try_ref_edit_lightning.py <plain|cfg1> [양자화=8] [장면=gilgal] [시드=11]   # 지시문 바꾸기: REF_EDIT_PROMPT·REF_EDIT_TAG 환경 변수
    plain = mflux CLI 그대로(스텝마다 트랜스포머 2회), cfg1 = mflux_qwen_edit_cfg1.py 래퍼(부정 계산 건너뜀)

지시문·참조·몸 상자·되붙임·mask_diff는 gen_ref_edit_2511과 같다. 결과는 samples/ref-edit-2511/metrics.json `lightning`에 붙인다."""
import os, re, signal, subprocess, sys, time

import params
import gen_ref_edit as G
import gen_ref_edit_2511 as R

LORA = os.path.expanduser("~/.cache/huggingface/hub/models--lightx2v--Qwen-Image-Edit-2511-Lightning")
STEPS, GUIDANCE = 4, 1.0


def lora_path():
    for d, _, fs in os.walk(LORA):
        for f in fs:
            if f == "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors":
                return os.path.join(d, f)
    sys.exit("[RefEditLightning] LoRA 파일 없음")


def run(mode, q, scene, sd):
    who = params.REF_EDIT_SCENES[scene][0]
    base0 = src = G.base_path(scene, sd)
    mk = G.make_mask(scene, who, base0, os.path.join(R.OUT, "mask", scene, f"{who}-s{sd}.png"))
    side = R.side(scene, who, base0)
    tag = os.environ.get("REF_EDIT_TAG", "")
    raw = os.path.join(R.OUT, "lightning", "raw", f"{mode}{tag}-q{q}-{scene}-s{sd}-{who}.png")
    out = os.path.join(R.OUT, "lightning", f"{mode}{tag}-q{q}-{scene}-s{sd}.png")
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    head = ([os.path.join(G.MFLUX, "python"), os.path.join(G.HERE, "mflux_qwen_edit_cfg1.py")] if mode == "cfg1"
            else [os.path.join(G.MFLUX, R.CLI)])
    cmd = ["/usr/bin/time", "-l", *head, "--model", R.NAME, "-q", str(q), *(["--low-ram"] if q == 8 else []),
           "--lora", lora_path(), "1.0", "--image-paths", src, *G.refs(who),
           "--prompt", (os.environ.get("REF_EDIT_PROMPT") or params.REF_EDIT_2511_PROMPT).format(side=side), "--seed", str(sd),
           "--steps", str(STEPS), "--guidance", str(GUIDANCE), "--width", str(G.W), "--height", str(G.H), "--output", raw]
    t = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        so, err = p.communicate(timeout=params.REF_EDIT_2511_MAX_SEC * 2)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        so, err = p.communicate()
        rc, err = -9, "timeout " + err
    sec = round(time.time() - t, 1)
    peak = re.search(r"(\d+)\s+peak memory footprint", err)
    steps = re.findall(r"(\d+)/%d \[[^\]]*?([\d.]+)s/it" % STEPS, err)
    e = {"prompt": "env" if os.environ.get("REF_EDIT_PROMPT") else "params", "mode": mode, "quantize": q, "scene": scene, "who": who, "seed": sd, "steps": STEPS, "guidance": GUIDANCE,
         "sec": sec, "peak_gb": round(int(peak.group(1)) / 2**30, 2) if peak else None,
         "s_per_it": [float(x[1]) for x in steps], "status": "ok" if rc == 0 and os.path.exists(raw) else "error", **mk}
    if e["status"] == "ok":
        R.paste(raw, src, mk["mask"], out)
        e.update(raw=raw, out=out, mask_diff=R.mask_diff(out, src, mk["mask_box"]))
    else:
        e["error"] = (so[-600:] + "\n" + err[-1500:]).strip()
    m = R.load_m()
    m.setdefault("lightning", []).append(e)
    R.save_m(m)
    print(f"[RefEditLightning] {mode} q{q} {scene} s{sd} {e['status']} {sec}s peak {e['peak_gb']}GB mask_diff {e.get('mask_diff')}", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0], int(a[1]) if len(a) > 1 else 8, a[2] if len(a) > 2 else "gilgal", int(a[3]) if len(a) > 3 else 11)
