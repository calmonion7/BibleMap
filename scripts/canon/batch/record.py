"""record.py <scene>: anim.html을 폰 390×844로 녹화 → <R>/<scene>.webm (route 서빙 — 포트 바인딩 없음).
장면 이름이 _로 시작하면(시험) <R>/<scene>/ 안에 쓴다."""
import os, sys, shutil, mimetypes
from playwright.sync_api import sync_playwright
scene = sys.argv[1]
WHOLE = "--whole" in sys.argv   # 한 장 파일럿: scene-whole-pilot, 프레임 3장 + 프레임 검사 로그
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".forge", "reports", "scene-whole-pilot" if WHOLE else "scene-batch-pilot"))
out = os.path.join(R, scene, scene + ".webm") if scene.startswith("_") else os.path.join(R, scene + ".webm")
def serve(route):
    path = os.path.join(R, route.request.url.split("http://pilot.local/", 1)[1].split("?")[0])
    route.fulfill(path=path, content_type=mimetypes.guess_type(path)[0] or "application/octet-stream")
vdir = os.path.join(R, scene, "_vid")
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, record_video_dir=vdir,
                            record_video_size={"width": 390, "height": 844})
        ctx.route("http://pilot.local/**", serve)
        p = ctx.new_page(); errs = []
        p.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        p.on("pageerror", lambda e: errs.append(str(e)))
        p.goto(f"http://pilot.local/{scene}/anim.html"); p.wait_for_timeout(10500)
        vp = p.video.path(); ctx.close(); shutil.move(vp, out); b.close()
    print(out, "오류:", errs)
    if WHOLE:
        import subprocess, json, logging
        from build_anim import build_whole
        log = logging.getLogger("[record]"); log.addHandler(logging.FileHandler(os.path.join(R, "_record.log"), encoding="utf-8")); log.setLevel(logging.INFO)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]))
        fd = os.path.join(R, scene, "frames"); os.makedirs(fd, exist_ok=True)
        for name, t in (("start", .3), ("mid", dur / 2), ("end", dur - .3)):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", out, "-frames:v", "1", os.path.join(fd, name + ".png")], check=True)
        bad = [f"{c['t']} {c['why']}" for c in json.load(open(os.path.join(R, scene, "anim.json")))["check"] if not c["ok"]]
        log.info("%s 길이 %.1fs 오류 %s 프레임 검사: %s", scene, dur, errs, "통과" if not bad and dur > 2 else "실패 — " + "; ".join(bad or ["길이"]))
finally:
    shutil.rmtree(vdir, ignore_errors=True)
