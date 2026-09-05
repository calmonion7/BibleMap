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
FRESH = "authored-david-adullam-cave"   # 시도도 승인도 없는 장면 — 곁파일이 아예 없다
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


def call(port, path, body=None):
    import urllib.error, urllib.request
    r = urllib.request.Request(f"http://127.0.0.1:{port}/api{path}", method="POST" if body else "GET",
                               data=json.dumps(body).encode() if body else None,
                               headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(r)), 200
    except urllib.error.HTTPError as e:
        return json.load(e), e.code


def delete(port, path):
    import urllib.error, urllib.request
    r = urllib.request.Request(f"http://127.0.0.1:{port}/api{path}", method="DELETE")
    try:
        urllib.request.urlopen(r)
        return 200
    except urllib.error.HTTPError as e:
        return e.code


def check_queue(port):
    """같은 시드는 같은 그림이다 — 두 번째 요청은 막히고, 줄에 선 것은 뺄 수 있어야 한다."""
    bad = []
    _, c1 = call(port, f"/scenes/{SCENE}/attempts", {"stage": "S2", "seeds": [11]})
    if c1 != 200:
        bad.append(f"첫 시도 등록이 실패했다({c1})")
    dup, c2 = call(port, f"/scenes/{SCENE}/attempts", {"stage": "S2", "seeds": [11]})
    if c2 == 200:
        bad.append("같은 단계·같은 시드가 두 번 줄에 섰다 — 중복 차단이 안 먹는다")
    elif "같은 시드는 같은 그림" not in (dup.get("error") or ""):
        bad.append(f"중복 차단 문구가 다르다: {dup.get('error')!r}")

    # 다른 시드는 줄을 서고, 그것을 뺄 수 있어야 한다
    q2, _ = call(port, f"/scenes/{SCENE}/attempts", {"stage": "S2", "seeds": [42]})
    q, _ = call(port, "/queue")
    pend = [j["id"] for j in q["pending"]]
    if not pend:
        bad.append("두 번째 시드가 줄에 서지 않았다")
    else:
        call(port, "/queue/cancel", {"job": pend[0]})
        q, _ = call(port, "/queue")
        if any(j["id"] == pend[0] for j in q["pending"]):
            bad.append("대기 취소가 먹지 않았다")

    # 도는 것 멈추기
    q, _ = call(port, "/queue")
    if q["running"]:
        rid = q["running"]["id"]
        t0 = time.time()
        call(port, "/queue/cancel", {"job": rid})
        for _ in range(80):
            q, _ = call(port, "/queue")
            if not q["running"]:
                break
            time.sleep(0.1)
        else:
            bad.append("도는 작업이 멈추지 않았다")
        # **끝난 것과 멈춘 것을 구별한다.** 그냥 기다렸다가 끝난 것을 「멈췄다」로 세면
        # 취소가 없어도 이 검사는 통과한다.
        done = next((j for j in q["recent"] if j["id"] == rid), None)
        if not done or done["status"] != "cancelled":
            bad.append(f"도는 작업이 취소로 기록되지 않았다: {done and done['status']}")
        if time.time() - t0 > 1.2:
            bad.append(f"취소가 곧바로 듣지 않았다({time.time() - t0:.1f}s)")
    return bad


def open_scene(pg, title):
    pg.locator(".card", has_text=title).get_by_role("button", name="열기").click()


def main():
    from playwright.sync_api import sync_playwright

    tmp = tempfile.mkdtemp(prefix="scene-tool-uat-")
    scenes, attempts = os.path.join(tmp, "scenes"), os.path.join(tmp, "attempts")
    os.makedirs(scenes), os.makedirs(attempts)
    shutil.copy(os.path.join(CANON, "scenes", f"{SCENE}.json"), scenes)
    shutil.copy(os.path.join(CANON, "scenes", f"{FRESH}.json"), scenes)
    shutil.copy(os.path.join(CANON, "tool", "glossary.json"), os.path.join(tmp, "glossary.json"))
    side = os.path.join(CANON, "attempts", f"{SCENE}.json")
    if os.path.exists(side):
        shutil.copy(side, attempts)
    os.makedirs(SHOTS, exist_ok=True)

    port = free_port()
    env = {**os.environ, "SCENE_TOOL_DEV": "1", "SCENE_TOOL_FAKE_GEN": "1",
           "SCENE_TOOL_SCENES_DIR": scenes, "SCENE_TOOL_ATTEMPTS_DIR": attempts,
           "SCENE_TOOL_PORT": str(port), "SCENE_TOOL_USERS": "",
           "SCENE_TOOL_FAKE_DELAY": "1.5",   # 취소를 잴 수 있게 가짜 실행기를 늦춘다
           "SCENE_TOOL_OUT_DIR": os.path.join(tmp, "out"),   # 실제 산출 트리를 덮지 않게
           "SCENE_TOOL_FAKE_AI": "1",   # AI를 부르지 않는다(느리고 값이 든다) — 배선만 검사한다
           "SCENE_TOOL_GLOSSARY": os.path.join(tmp, "glossary.json"),   # 실제 용어집을 더럽히지 않게
           "SCENE_TOOL_FAKE_AI_DELAY": "2.5"}   # 「도는 도중 화면 이동」을 실제로 재현하려면 늦어야 한다
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
            open_scene(pg, "사울 — 길갈에서 왕이 되다")
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
            open_scene(pg, "사울 — 길갈에서 왕이 되다")
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

            # 4-del) 그림 지우기 — 승인된 장은 못 지우고(버튼 꺼짐·서버도 거절), 다른 장은 지우면
            #        줄·파일·곁파일 기록이 함께 사라진다. 지울 장은 가짜 실행기로 하나 더 만든다.
            side_path = os.path.join(attempts, f"{SCENE}.json")
            before = len(json.load(open(side_path))["attempts"])
            pg.click("#one")
            for _ in range(200):
                if len(json.load(open(side_path))["attempts"]) > before:
                    break
                time.sleep(0.1)
            else:
                fails.append("지울 장을 만들지 못했다 — 두 번째 시도가 곁파일에 없다")
            pg.wait_for_timeout(1500)
            pg.reload(wait_until="networkidle")
            open_scene(pg, "사울 — 길갈에서 왕이 되다")
            pg.click("button.chip:has-text('S1')")
            pg.wait_for_selector("button[data-del]", timeout=10000)
            victim = json.load(open(side_path))["attempts"][-1]      # 방금 만든 것 — 승인되지 않았다
            vimg = os.path.join(REPO, victim["images"]["11"]["canvas"])
            if not os.path.exists(vimg):
                fails.append(f"지울 장의 파일이 없다 — 시험 전제가 깨졌다: {vimg}")
            if not pg.locator("button[data-del][disabled]").count():
                fails.append("승인된 장의 「지우기」가 꺼져 있지 않다")
            ap1 = next(s for s in json.load(open(os.path.join(scenes, f"{SCENE}.json")))["stages"]
                       if s["id"] == "S1")["approved"]
            code = delete(port, f"/scenes/{SCENE}/attempts/{ap1['attempt']}/{ap1['seed']}")
            if code != 400:
                fails.append(f"승인된 장 삭제를 서버가 거절하지 않았다 (HTTP {code})")
            pg.once("dialog", lambda d: d.accept())
            pg.locator("button[data-del]:not([disabled])").last.click()
            pg.wait_for_timeout(1500)
            if any(a["id"] == victim["id"] for a in json.load(open(side_path))["attempts"]):
                fails.append(f"지운 시도 {victim['id']}가 곁파일에 남아 있다")
            if os.path.exists(vimg):
                fails.append(f"지운 장의 파일이 남아 있다: {vimg}")
            if pg.get_by_text(f"{victim['id']} · 시드 11").count():
                fails.append("지운 장이 화면에 남아 있다")

            # 4a) AI 문구 생성 — 지시를 넣고 누르면 문구·부정어가 폼에 채워진다(가짜 AI)
            pg.fill("#ask", "제단만 남기고 사람은 빼라")
            before_pr = pg.input_value("#pr")
            pg.click("#gen")
            # 이제 번호를 받고 물어보는 방식이라 첫 조회(1.5초) 뒤에야 채워진다.
            pg.wait_for_function(
                "() => document.querySelector('#why') && document.querySelector('#why').textContent.trim().length > 0",
                timeout=30000)
            pg.wait_for_timeout(300)
            if pg.input_value("#pr") == before_pr:
                fails.append("AI 생성이 문구를 바꾸지 못했다")
            if not pg.inner_text("#why").strip():
                fails.append("AI 생성이 설명 줄을 남기지 않았다")
            if not pg.inner_text("#ko-pr").strip():
                fails.append("AI 생성 뒤 한글 뜻이 다시 붙지 않았다")

            # 4a-2) **AI가 지은 문구에는 물음표가 남지 않아야 한다.** 용어집은 손으로 채운 것이라
            #       새 표현은 뜻이 없다 — 지은 쪽이 뜻도 함께 내놓고 서버가 용어집에 쌓는다.
            if pg.locator("#ko-pr .unk, #ko-ng .unk").count():
                fails.append("AI 생성 뒤에도 모르는 낱말이 남았다: "
                             + pg.locator("#ko-pr .unk, #ko-ng .unk").first.inner_text())
            if pg.locator("#fill").is_visible():
                fails.append("모르는 낱말이 없는데 번역 버튼이 보인다")

            # 4a-3) **손으로 고친 표현**은 아무도 뜻을 모른다 — 그때 번역 버튼이 나타나 채운다.
            pg.fill("#pr", pg.input_value("#pr").rstrip(".") + ", a strange new phrase here.")
            pg.wait_for_selector("#ko-pr .unk", timeout=10000)
            if pg.locator("#fill").is_hidden():
                fails.append("손으로 넣은 모르는 낱말에 번역 버튼이 안 나온다")
            pg.click("#fill")
            pg.wait_for_function("() => document.querySelectorAll('.ko .unk').length === 0", timeout=60000)
            if pg.locator("#fill").is_visible():
                fails.append("번역 뒤에도 번역 버튼이 남아 있다")

            # 4a-4) **저장된 문구는 누르기 전에 번역된다.** 버튼을 눌러야 한글이 붙는다면
            #       도구가 할 일을 사람에게 미루는 것이다. 단계를 열면 알아서 채워야 한다.
            pg.fill("#pr", pg.input_value("#pr").rstrip(".") + ", yet another unseen wording.")
            pg.click("#save")
            # **번역이 도는 도중에 단계를 옮긴다.** 사람이 실제로 하는 일이고, 여기서 결과가
            #  붙을 자리를 잃으면 돌아와도 물음표가 남는다(실측 2026-09-05).
            pg.wait_for_timeout(400)
            pg.click("button.chip:has-text('S2')")
            pg.wait_for_timeout(400)
            pg.click("button.chip:has-text('S1')")
            try:
                pg.wait_for_function(
                    "() => document.querySelectorAll('.ko .unk').length === 0", timeout=60000)
            except Exception:
                fails.append("단계를 열었는데 모르는 낱말이 스스로 번역되지 않았다: "
                             + pg.locator(".ko .unk").first.inner_text())

            # 4b) 구역 고르개 — 그림 위에서 끌면 좌표 넷이 채워진다
            pg.locator(".pick").scroll_into_view_if_needed()
            pg.wait_for_timeout(300)
            r = pg.locator(".pick").bounding_box()
            pg.mouse.move(r["x"] + r["width"] * 0.25, r["y"] + r["height"] * 0.20)
            pg.mouse.down()
            pg.mouse.move(r["x"] + r["width"] * 0.60, r["y"] + r["height"] * 0.75, steps=8)
            pg.mouse.up()
            pg.wait_for_timeout(300)
            got = [float(pg.input_value(f'[data-c="{i}"]')) for i in range(4)]
            want = [0.25, 0.20, 0.60, 0.75]
            if any(abs(g - w) > 0.03 for g, w in zip(got, want)):
                fails.append(f"구역 고르개가 끌기를 좌표로 옮기지 못했다: {got} (기대 {want})")
            if pg.locator(".pick .box").is_hidden():
                fails.append("고른 구역 상자가 그림 위에 안 보인다")

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

            # 6) **시도가 하나도 없는 장면.** 곁파일이 없어 `sceneSeed`가 비어 있고, 승인이 없어
            #    「장면 완료」가 꺼져 있다. 폰 실측에서 여기가 깨졌다(시드 null → 500 → 모든 버튼이
            #    되살아나 완료가 눌림 → null 참조). 목록으로 돌아가 처음부터 밟는다.
            pg.click("text=← 목록")
            pg.wait_for_selector("text=다윗과 무리 — 아둘람 굴", timeout=10000)
            open_scene(pg, "다윗과 무리 — 아둘람 굴")
            pg.wait_for_selector("#sd", timeout=10000)
            sd = pg.input_value("#sd")
            if not sd.strip().isdigit():
                fails.append(f"시도 없는 장면의 시드 칸이 숫자가 아니다: {sd!r}")
            if not pg.locator("button:has-text('장면 완료')").last.is_disabled():
                fails.append("승인이 없는데 「장면 완료」가 눌린다")
            # 6b) **실패한 뒤에도 꺼진 버튼은 꺼져 있어야 한다.** 일부러 잘못된 구역(x0>x1)으로
            #     저장을 시켜 400을 받은 뒤, 승인이 없는 「장면 완료」가 여전히 꺼져 있는지 본다.
            #     폰 실측에서 이것이 뚫려 두 번째 오류(null 참조)가 났다.
            pg.fill('[data-c="0"]', "0.9")
            pg.fill('[data-c="2"]', "0.1")
            pg.click("#save")
            pg.wait_for_selector(".card.err", timeout=10000)
            if not pg.locator("button:has-text('장면 완료')").last.is_disabled():
                fails.append("저장 실패 뒤 「장면 완료」가 되살아났다 — 꺼진 버튼은 꺼진 채여야 한다")
            pg.reload(wait_until="networkidle")
            open_scene(pg, "다윗과 무리 — 아둘람 굴")
            pg.wait_for_selector("#sd", timeout=10000)

            fresh_side = os.path.join(attempts, f"{FRESH}.json")
            pg.click("#one")
            for _ in range(200):
                if os.path.exists(fresh_side):
                    break
                time.sleep(0.1)
            else:
                fails.append("시도 없는 장면에서 「1장 그리기」가 시도를 남기지 못했다")
            pg.wait_for_timeout(1500)
            if pg.locator(".card.err").count():
                fails.append("시도 없는 장면에서 오류 카드가 떴다: "
                             + pg.locator(".card.err").first.inner_text()[:120])
            b.close()

        # 7) 큐 — 같은 시드 중복 차단 · 대기 취소 · 도는 것 멈추기 (브라우저 없이 API로)
        fails += check_queue(port)
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
