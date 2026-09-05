#!/usr/bin/env python3
"""장면 승인 도구 화면 스모크 — 폰 뷰포트 390×844 (2026-09-05, task 339 DoD 3).

**실제 명세를 건드리지 않는다**: 명세와 곁파일을 임시 폴더에 복사하고 서버를 그 폴더로 띄운다
(`SCENE_TOOL_SCENES_DIR`·`SCENE_TOOL_ATTEMPTS_DIR`). GPU도 쓰지 않는다(`SCENE_TOOL_FAKE_GEN=1`).

  python3 scripts/canon/tool/uat_scene_tool.py     # → exit 0

시나리오: 목록 → 장면 열기 → S1 시도 등록 → 완료 대기 → 승인 → 보드 「승인」 →
S1 문구 저장 → 보드가 S1과 아래를 「재검토」로. 스크린샷 3장.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(CANON))
SCENE = "authored-saul-gilgal-coronation"
SHOTS = os.path.join(REPO, ".forge", "reports", "canon-pilot", "scene-tool", "uat")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def wait_up(port, proc, secs=20):
    for _ in range(secs * 10):
        if proc.poll() is not None:
            raise RuntimeError(f"서버가 죽었다(종료코드 {proc.returncode})\n{proc.stdout.read() if proc.stdout else ''}")
        try:
            with socket.create_connection(("127.0.0.1", port), 0.3):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("서버가 20초 안에 뜨지 않았다")


def main():
    from playwright.sync_api import sync_playwright

    tmp = tempfile.mkdtemp(prefix="scene-tool-uat-")
    scenes, attempts = os.path.join(tmp, "scenes"), os.path.join(tmp, "attempts")
    os.makedirs(scenes), os.makedirs(attempts)
    shutil.copy(os.path.join(CANON, "scenes", f"{SCENE}.json"), scenes)
    side = os.path.join(CANON, "attempts", f"{SCENE}.json")
    if os.path.exists(side):
        shutil.copy(side, attempts)
    os.makedirs(SHOTS, exist_ok=True)

    port = free_port()
    env = {**os.environ, "SCENE_TOOL_DEV": "1", "SCENE_TOOL_FAKE_GEN": "1",
           "SCENE_TOOL_SCENES_DIR": scenes, "SCENE_TOOL_ATTEMPTS_DIR": attempts,
           "SCENE_TOOL_PORT": str(port), "SCENE_TOOL_USERS": ""}
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "server.py")], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    fails = []
    try:
        wait_up(port, proc)
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={"width": 390, "height": 844})
            pg.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")

            # 1) 목록
            pg.wait_for_selector("text=사울 — 길갈에서 왕이 되다", timeout=10000)
            pg.screenshot(path=os.path.join(SHOTS, "1-list.png"), full_page=True)
            if pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"):
                fails.append("목록에 가로 스크롤이 생겼다")

            # 2) 장면 열기
            pg.click("text=열기")
            pg.wait_for_selector("text=① 본문", timeout=10000)

            # 3) S1 시도 등록 → 완료 대기 (가짜 실행기)
            pg.click("button.chip:has-text('S1')")
            before = len(json.load(open(os.path.join(attempts, f"{SCENE}.json")))["attempts"])
            pg.click("#one")
            for _ in range(200):
                n = len(json.load(open(os.path.join(attempts, f"{SCENE}.json")))["attempts"])
                if n > before:
                    break
                time.sleep(0.1)
            else:
                fails.append("시도가 곁파일에 기록되지 않았다")
            pg.wait_for_timeout(1500)
            pg.reload(wait_until="networkidle")
            pg.click("text=열기")
            pg.wait_for_selector("button.chip:has-text('S1')", timeout=10000)
            pg.click("button.chip:has-text('S1')")

            # 4) 새 시도를 승인 → 보드에서 S1이 「승인」
            pg.wait_for_selector("button.p:has-text('이 장으로 승인')", timeout=10000)
            pg.locator("button.p:has-text('이 장으로 승인')").last.click()
            pg.wait_for_timeout(1200)
            spec = json.load(open(os.path.join(scenes, f"{SCENE}.json")))
            s1 = next(s for s in spec["stages"] if s["id"] == "S1")
            if not s1.get("approved") or s1["approved"]["by"] != "dev":
                fails.append(f"S1 승인이 기록되지 않았다: {s1.get('approved')}")
            pg.wait_for_selector("button.chip.s-승인:has-text('S1')", timeout=10000)
            pg.screenshot(path=os.path.join(SHOTS, "2-approved.png"), full_page=True)

            # 5) S1 문구 저장 → S1과 아래가 「재검토」
            pg.click("button.chip:has-text('S1')")
            pg.fill("#pr", "a wide dry open field, sparse dry grass, CHANGED BY UAT.")
            pg.click("#save")
            pg.wait_for_selector("button.chip.s-재검토:has-text('S1')", timeout=20000)
            stale = pg.eval_on_selector_all(
                "button.chip.s-재검토", "els => els.map(e => e.textContent.split(' ')[0])")
            for want in ("S1", "S2", "S3", "S4", "S5"):
                if want not in stale:
                    fails.append(f"{want}가 재검토로 뜨지 않았다 (재검토: {stale})")
            pg.screenshot(path=os.path.join(SHOTS, "3-stale.png"), full_page=True)
            if pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"):
                fails.append("장면 화면에 가로 스크롤이 생겼다")
            b.close()
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("낙제:\n  - " + "\n  - ".join(fails))
        return 1
    print(f"통과 · 스크린샷 3장 -> {os.path.relpath(SHOTS, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
