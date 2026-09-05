#!/usr/bin/env python3
"""장면 승인 도구 — 로컬 웹 서버 (2026-09-05, task 339).

`127.0.0.1:8100`에만 붙는다. 바깥에서는 이 머신의 기존 Cloudflare Tunnel + Access를 지나 들어온다
(노트 `notes/SCENE-TOOL.md` 「바깥에서 열기」). 표준 라이브러리만 쓴다 — 백엔드 requirements에 아무것도
더하지 않는다. GPU 작업은 1/2의 `attempt.py`를 venv 파이썬 서브프로세스로 부른다.

  SCENE_TOOL_USERS=you@example.com python3 scripts/canon/tool/server.py

환경변수:
  SCENE_TOOL_USERS        쉼표로 허용 이메일. `Cf-Access-Authenticated-User-Email`이 이 목록에 없으면 403.
  SCENE_TOOL_DEV=1        헤더 없이 통과하고 `by=dev` (로컬 스모크 전용).
  SCENE_TOOL_FAKE_GEN=1   GPU 대신 자리표시 PNG를 곁파일 규약대로 써 넣는다 (스모크 전용).
  SCENE_TOOL_SCENES_DIR   명세 폴더를 갈아끼운다 (스모크가 실제 명세를 건드리지 않게).
  SCENE_TOOL_ATTEMPTS_DIR 곁파일 폴더를 갈아끼운다.
  SCENE_TOOL_VENV         venv 파이썬 경로.

**GPU 작업은 절대 겹치지 않는다** — 워커 스레드 하나, 큐 하나, 한 번에 하나. 생성 프로세스가 겹치면
처리량이 20배 떨어진 실측이 있다. 「재시도」를 연달아 눌러도 줄을 선다.
"""
import datetime
import hmac
import json
import mimetypes
import os
import posixpath
import queue
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.dirname(HERE)
sys.path.insert(0, CANON)
import params  # noqa: E402
import derive_scene as ds  # noqa: E402
import scene_state as ss  # noqa: E402
import approve as ap  # noqa: E402
import attempt as at  # noqa: E402
import compose as cp  # noqa: E402

REPO = params.REPO_ROOT
PORT = int(os.environ.get("SCENE_TOOL_PORT", "8100"))
USERS = [e.strip() for e in os.environ.get("SCENE_TOOL_USERS", "").split(",") if e.strip()]
DEV = os.environ.get("SCENE_TOOL_DEV") == "1"
FAKE = os.environ.get("SCENE_TOOL_FAKE_GEN") == "1"
FAKE_DELAY = float(os.environ.get("SCENE_TOOL_FAKE_DELAY", "0"))   # 스모크가 취소를 재려고 쓴다
VENV = os.environ.get("SCENE_TOOL_VENV", "/Users/calmonion/.local/biblemap-imggen/.venv314/bin/python")
BIND = os.environ.get("SCENE_TOOL_BIND", "127.0.0.1")
TOKEN = os.environ.get("SCENE_TOOL_TOKEN", "")

# 폴더를 갈아끼운다 — 1/2의 스크립트를 고치지 않고 **부르는 쪽에서** 상수를 바꾼다.
# eco: 실제 GPU 경로의 attempt.py는 서브프로세스라 이 패치를 못 본다. 스모크(FAKE)만 폴더를 옮기므로 충분하다.
SCENES_DIR = os.environ.get("SCENE_TOOL_SCENES_DIR") or os.path.join(CANON, "scenes")
# 산출 폴더도 갈아끼울 수 있어야 한다. 스모크의 가짜 실행기가 **실제 산출 트리에 써서**
# 사람이 만든 그림을 덮은 사고가 있었다(2026-09-05, adullam-cave a001).
OUT_DIR = os.environ.get("SCENE_TOOL_OUT_DIR") or os.path.join(params.OUT_ROOT, "scene-tool")
ATTEMPTS_DIR = os.environ.get("SCENE_TOOL_ATTEMPTS_DIR") or os.path.join(CANON, "attempts")
ds.SCENES_DIR = SCENES_DIR
ap.SCENES = SCENES_DIR
at.SIDE_DIR = ATTEMPTS_DIR
IMG_ROOT = os.path.join(REPO, ".forge", "reports")

Q = queue.Queue()
JOBS = []               # 최근 것이 앞. {id, scene, stage, seeds, status, log, at}
JOBS_LOCK = threading.Lock()
CUR = {"proc": None}    # 진행 중 생성 프로세스 — 취소하려면 이것을 잡고 있어야 한다
COMPOSE = {}            # 문구 짓기 결과 — 번호 → {status, ...}. GPU 큐와 별개다(GPU를 쓰지 않는다)
COMPOSE_LOCK = threading.Lock()
CUR_LOCK = threading.Lock()
LIVE = ("queued", "running")


# ---------- 데이터 ----------

def scene_ids():
    return sorted(f[:-5] for f in os.listdir(SCENES_DIR) if f.endswith(".json"))


def read(scene):
    return ap.load_spec(scene), at.load_side(scene)


def summary(scene):
    spec, side = read(scene)
    b = ss.board(spec, side)
    live = [r for r in b["stages"] if r["status"] != "건너뜀"]
    return {"id": scene, "title": spec.get("title", scene),
            "stages": len(live),
            "approved": sum(1 for r in live if r["status"] == "승인"),
            "stale": sum(1 for r in live if r["status"] == "재검토"),
            "done": bool((spec.get("approved") or {}).get("final")) and not b["final"]["stale"]}


def detail(scene):
    spec, side = read(scene)
    b = ss.board(spec, side)
    by_stage = {}
    for a in side.get("attempts", []):
        by_stage.setdefault(a["stage"], []).append(a)
    for r in b["stages"]:
        st = next(s for s in spec["stages"] if s["id"] == r["id"])
        r["prompt"] = st.get("prompt", "")
        r["neg"] = st.get("neg", [])
        r["coords"] = spec["regions"][st["region"]]
        r["from"] = st.get("from")
        r["tries"] = [{"id": a["id"], "seeds": a["seeds"], "prompt": a["prompt"],
                       "neg": a.get("neg", []), "region": a.get("region"),
                       "tokens": a.get("tokens"), "seconds": a.get("seconds"),
                       "by": a.get("by"), "images": a.get("images", {}),
                       "upstream": a.get("upstream")}
                      for a in by_stage.get(r["id"], [])]
    return {"id": scene, "title": spec.get("title", scene),
            "canvas": {"w": params.SCENE_SIZE[0], "h": params.SCENE_SIZE[1]},
            "verses": spec.get("verses"), "moment": spec.get("moment"),
            "background": spec.get("background", []), "crowds": spec.get("crowds", []),
            "figures": spec.get("figures", []),
            "ladder": b["ladder"], "stages": b["stages"], "final": b["final"],
            # 곁파일이 없으면 `sceneSeed` 키가 **None으로 존재**한다 — `.get(_, 11)`은 그때 기본값을 주지 않는다.
            "sceneSeed": side.get("sceneSeed") or 11, "queue": queue_state()}


def queue_state():
    with JOBS_LOCK:
        jobs = [dict(j) for j in JOBS[:12]]
    return {"running": next((j for j in jobs if j["status"] == "running"), None),
            "pending": [j for j in jobs if j["status"] == "queued"],
            "recent": [j for j in jobs if j["status"] in ("done", "failed", "cancelled")][:5]}


# ---------- 워커 (한 번에 하나) ----------

def fake_attempt(scene, stage_id, seeds, job=None):
    """GPU 없이 곁파일 규약대로 자리표시 PNG를 남긴다 — 1/2 스키마 그대로."""
    from PIL import Image, ImageDraw
    spec = ap.load_spec(scene)
    st = next(s for s in spec["stages"] if s["id"] == stage_id)
    side = at.load_side(scene, 11)
    if side.get("sceneSeed") is None:
        side["sceneSeed"] = 11
    up = at.upstream_of(spec, stage_id)
    aid = at.next_id(side)
    out_dir = os.path.join(OUT_DIR, scene, aid)
    os.makedirs(out_dir, exist_ok=True)
    images = {}
    for seed in seeds:
        waited = 0.0
        while waited < FAKE_DELAY:                  # 잠자는 동안에도 취소를 받는다(실제 경로는 프로세스를 죽인다)
            if job and job.get("killed"):
                raise RuntimeError("사람이 멈췄다")
            time.sleep(0.05)
            waited += 0.05
        img = Image.new("RGB", (640, 360), (238, 232, 220))
        ImageDraw.Draw(img).text((14, 14), f"{scene}\n{stage_id} · {aid} · s{seed}", fill=(40, 40, 40))
        p = os.path.join(out_dir, f"t{seed}-{stage_id}-s{seed}.png")
        img.save(p)
        images[str(seed)] = {"canvas": os.path.relpath(p, REPO)}
    side["attempts"].append({
        "id": aid, "stage": stage_id, "seeds": seeds,
        "prompt": st.get("prompt"), "neg": list(st.get("neg") or []),
        "region": list(spec["regions"][st["region"]]), "upstream": up,
        "tokens": {"n": 0, "lim": 77},
        "startedAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "seconds": 0.0, "by": "fake", "images": images})
    at.save_side(side)
    return f"가짜 실행기 · {aid} · {len(seeds)}장"


def real_attempt(scene, stage_id, seeds, job=None):   # job은 취소 표시용 — 실제로는 프로세스를 죽인다
    cmd = [VENV, "attempt.py", "--scene", scene, "--stage", stage_id,
           "--seeds", ",".join(str(s) for s in seeds)]
    # `subprocess.run`이 아니라 Popen이다 — 취소하려면 도는 동안 손잡이를 들고 있어야 한다.
    proc = subprocess.Popen(cmd, cwd=CANON, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    with CUR_LOCK:
        CUR["proc"] = proc
    try:
        out, _ = proc.communicate()
    finally:
        with CUR_LOCK:
            CUR["proc"] = None
    tail = "\n".join((out or "").strip().splitlines()[-12:])
    if proc.returncode != 0:
        raise RuntimeError(tail or f"종료코드 {proc.returncode}")
    return tail


def worker():
    while True:
        job = Q.get()
        with JOBS_LOCK:
            if job["status"] == "cancelled":        # 줄에서 기다리다 취소된 것 — 그리지 않는다
                Q.task_done()
                continue
            job["status"] = "running"
        try:
            job["log"] = (fake_attempt if FAKE else real_attempt)(
                job["scene"], job["stage"], job["seeds"], job)
            with JOBS_LOCK:
                job["status"] = "cancelled" if job.get("killed") else "done"
        except Exception as e:                      # noqa: BLE001 — 어떤 실패든 큐는 계속 돈다
            with JOBS_LOCK:
                job["status"] = "cancelled" if job.get("killed") else "failed"
                job["log"] = "사람이 멈췄다" if job.get("killed") else str(e)[-2000:]
        Q.task_done()


# ---------- HTTP ----------

class H(BaseHTTPRequestHandler):
    server_version = "scene-tool"

    def log_message(self, fmt, *a):
        sys.stderr.write("[server] %s\n" % (fmt % a))

    # -- 도우미 --
    def who(self):
        e = self.headers.get("Cf-Access-Authenticated-User-Email")
        if e and e in USERS:
            return e
        # 토큰 자물쇠 — Access가 앞에 없는 경로(같은 망의 폰)에서 쓴다.
        # 비교는 hmac.compare_digest로 — 문자열 == 는 앞자리부터 새어 나간다.
        if TOKEN:
            t = self.headers.get("X-Scene-Token") or urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query).get("t", [""])[0]
            if t and hmac.compare_digest(t, TOKEN):
                return "phone"
        if DEV and not e:
            return "dev"
        return None

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        try:
            self._send(code, raw, ctype)
        except (BrokenPipeError, ConnectionResetError):
            # 폰이 먼저 끊었다. 일은 이미 끝났으니 알릴 곳이 없을 뿐이다.
            self.log_message("클라이언트가 먼저 끊었다 — 응답을 버린다")

    def _send(self, code, raw, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        # 도구를 고치는 중이다 — 폰이 옛 화면을 들고 있으면 고친 것이 안 보인다.
        # 그림(`/img`)은 시도마다 경로가 달라 캐시해도 안전하다.
        if not ctype.startswith("image/"):
            self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    # -- 라우팅 --
    def route(self, method):
        path = urllib.parse.urlparse(self.path).path
        if path == "/health":
            return self.send(200, {"ok": True})
        if method == "GET" and path == "/":
            # 껍데기 한 장은 자물쇠 밖이다. 데이터는 한 줄도 들어 있지 않고, 화면이 저장해 둔 토큰을
            # 읽어 `/api`·`/img`에 실어 보내려면 **먼저 화면이 떠야** 한다. 여기까지 막으면
            # `?t=`를 주소에 매번 달지 않는 한 폰에서 다시 열 수 없다.
            return self.send(200, open(os.path.join(HERE, "index.html"), "rb").read(),
                             "text/html; charset=utf-8")
        if self.who() is None:
            return self.send(403, {"error": "Cf-Access-Authenticated-User-Email 헤더가 없거나 허용 목록에 없다"})
        try:
            return self.dispatch(method, path)
        except FileNotFoundError as e:
            self.send(404, {"error": str(e)})
        except ValueError as e:
            self.send(400, {"error": str(e)})
        except Exception as e:                       # noqa: BLE001
            self.send(500, {"error": f"{type(e).__name__}: {e}"})

    def dispatch(self, method, path):
        parts = [p for p in path.strip("/").split("/") if p]
        if method == "GET" and not parts:
            return self.send(200, open(os.path.join(HERE, "index.html"), "rb").read(),
                             "text/html; charset=utf-8")
        if method == "GET" and parts[0] == "img":
            return self.image("/".join(parts[1:]))
        if parts[:1] != ["api"]:
            return self.send(404, {"error": "없는 경로"})
        p = parts[1:]
        if method == "GET" and p == ["scenes"]:
            return self.send(200, [summary(s) for s in scene_ids()])
        if method == "GET" and p == ["queue"]:
            return self.send(200, queue_state())
        if method == "POST" and p == ["queue", "cancel"]:
            return self.cancel()
        if method == "POST" and p == ["gloss"]:
            return self.gloss()
        if method == "GET" and len(p) == 2 and p[0] == "compose":
            return self.compose_result(p[1])
        if method == "GET" and p == ["glossary"]:
            # 영문 문구·부정어의 한글 뜻. 화면이 한 번 받아 두고 입력할 때마다 옆에 채운다.
            return self.send(200, load_gloss())
        if len(p) >= 2 and p[0] == "scenes":
            scene = p[1]
            if scene not in scene_ids():
                raise FileNotFoundError(f"장면 {scene}이 없다")
            if method == "GET" and len(p) == 2:
                return self.send(200, detail(scene))
            if method == "GET" and p[2:] == ["tokens"]:
                return self.send(200, token_check(scene))
            if method == "POST" and p[2:] == ["attempts"]:
                return self.enqueue(scene)
            if method == "POST" and p[2:] == ["approve"]:
                return self.approve(scene)
            if method == "PATCH" and len(p) == 4 and p[2] == "stages":
                return self.patch_stage(scene, p[3])
            if method == "POST" and len(p) == 5 and p[2] == "stages" and p[4] == "compose":
                return self.compose(scene, p[3])
        return self.send(404, {"error": "없는 경로"})

    # -- 처리 --
    def image(self, rel):
        full = os.path.normpath(os.path.join(REPO, urllib.parse.unquote(rel)))
        if not full.startswith(IMG_ROOT + os.sep):      # 경로 탈출 거절 — .forge/reports 아래만
            return self.send(403, {"error": ".forge/reports 아래 파일만 낸다"})
        if not os.path.isfile(full):
            raise FileNotFoundError(rel)
        self.send(200, open(full, "rb").read(), mimetypes.guess_type(full)[0] or "application/octet-stream")

    def cancel(self):
        """줄에서 기다리는 작업은 표시만 하고, 도는 작업은 프로세스를 멈춘다."""
        b = self.body()
        want, killed = b.get("job"), []
        with JOBS_LOCK:
            targets = [j for j in JOBS if j["status"] in LIVE
                       and (b.get("all") or j["id"] == want)]
            for j in targets:
                if j["status"] == "queued":
                    j["status"] = "cancelled"
                    j["log"] = "줄에서 뺐다"
                else:
                    j["killed"] = True              # 워커가 이 표시를 보고 실패가 아니라 취소로 적는다
                killed.append(j["id"])
            running = any(j["status"] == "running" for j in targets)
        if running:
            with CUR_LOCK:
                if CUR["proc"] and CUR["proc"].poll() is None:
                    CUR["proc"].terminate()
        self.send(200, {"cancelled": killed, "queue": queue_state()})

    def enqueue(self, scene):
        b = self.body()
        stage = b.get("stage")
        raw = b.get("seeds") or [11]
        try:
            seeds = [int(x) for x in raw]
        except (TypeError, ValueError):
            raise ValueError(f"시드는 정수여야 한다: {raw!r}") from None
        if not seeds:
            raise ValueError("시드가 비어 있다")
        spec = ap.load_spec(scene)
        st = next((s for s in spec["stages"] if s["id"] == stage), None)
        if st is None:
            raise ValueError(f"단계 {stage}가 명세에 없다")
        if "from" in st:
            raise ValueError(f"단계 {stage}는 `from: {st['from']}`이라 재개로 그릴 수 없다")
        # 같은 캔버스에 같은 시드는 **같은 그림**이다(결정적). 연달아 눌러 같은 것을 여러 장
        # 그리는 일을 여기서 막는다 — 실측 2026-09-05: 1초 안에 넉 장이 줄을 섰고 전부 픽셀 동일이었다.
        with JOBS_LOCK:
            dup = next((j for j in JOBS if j["status"] in LIVE and j["scene"] == scene
                        and j["stage"] == stage and j["seeds"] == seeds), None)
        if dup:
            raise ValueError(f"같은 단계·같은 시드가 이미 {'도는 중' if dup['status'] == 'running' else '줄에'} 있다 "
                             f"— 같은 시드는 같은 그림이다. 다른 그림을 보려면 시드를 바꿔라")
        job = {"id": f"j{int(time.time() * 1000)}", "scene": scene, "stage": stage,
               "seeds": seeds, "status": "queued", "log": "",
               "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
        with JOBS_LOCK:
            JOBS.insert(0, job)
            del JOBS[40:]
        Q.put(job)
        self.send(200, {"job": job["id"], "queued": Q.qsize()})

    def approve(self, scene):
        b = self.body()
        kind, who = b.get("kind"), self.who()
        spec = ap.load_spec(scene)
        spec.setdefault("approved", {})
        if kind == "ladder":
            k = b.get("ladder")
            if k not in ss.LADDER:
                raise ValueError(f"사다리는 {ss.LADDER} 중 하나다")
            spec["approved"][k] = {"hash": ss.ladder_hashes(spec)[k], **ap.stamp(who)}
        elif kind in ("stage", "final"):
            attempt_id, seed = b.get("attempt"), b.get("seed")
            side = at.load_side(scene)
            a = next((x for x in side["attempts"] if x["id"] == attempt_id), None)
            if a is None:
                raise ValueError(f"시도 {attempt_id}가 곁파일에 없다")
            if str(seed) not in (a.get("images") or {}):
                raise ValueError(f"시도 {attempt_id}에 시드 {seed}의 그림이 없다")
            rec = {"attempt": attempt_id, "seed": int(seed), **ap.stamp(who)}
            if kind == "final":
                spec["approved"]["final"] = rec
            else:
                st = next((s for s in spec["stages"] if s["id"] == b.get("stage")), None)
                if st is None:
                    raise ValueError(f"단계 {b.get('stage')}가 명세에 없다")
                st["approved"] = rec
        else:
            raise ValueError("kind는 stage|ladder|final")
        ap.save_spec(spec)
        self.send(200, detail(scene))

    def compose(self, scene, stage_id):
        """한국어 지시를 받아 **일만 띄우고 곧바로 답한다.**

        AI 호출이 20~60초라 요청을 붙잡고 있으면 폰 브라우저가 먼저 끊는다(실측 2026-09-05:
        서버는 두 번 다 다 만들었는데 화면에는 `Failed to fetch`만 떴다). GPU 큐와 같은 방식으로
        일감 번호를 주고, 화면이 `/api/compose/<번호>`를 물어본다.
        """
        ask = self.body().get("ask", "")
        jid = f"c{int(time.time() * 1000)}"
        with COMPOSE_LOCK:
            COMPOSE[jid] = {"status": "running"}
            for old_id in list(COMPOSE)[:-20]:      # 오래된 것은 버린다
                COMPOSE.pop(old_id, None)
        threading.Thread(target=run_compose,
                         args=(jid, compose_now, scene, stage_id, ask), daemon=True).start()
        self.send(200, {"job": jid})

    def gloss(self):
        """손으로 고친 문구의 모르는 조각을 번역한다 — 문구 짓기와 같은 번호 방식."""
        b = self.body()
        jid = f"c{int(time.time() * 1000)}"
        with COMPOSE_LOCK:
            COMPOSE[jid] = {"status": "running"}
        threading.Thread(target=run_compose,
                         args=(jid, gloss_now, b.get("prompt", ""), b.get("neg") or []),
                         daemon=True).start()
        self.send(200, {"job": jid})

    def compose_result(self, jid):
        with COMPOSE_LOCK:
            got = COMPOSE.get(jid)
        if got is None:
            raise FileNotFoundError(f"문구 작업 {jid}를 모른다")
        self.send(200, got)

    def patch_stage(self, scene, stage_id):
        b = self.body()
        spec = ap.load_spec(scene)
        st = next((s for s in spec["stages"] if s["id"] == stage_id), None)
        if st is None:
            raise ValueError(f"단계 {stage_id}가 명세에 없다")
        if "prompt" in b:
            st["prompt"] = str(b["prompt"])
        if "neg" in b:
            st["neg"] = [str(x) for x in b["neg"]]
        if "region" in b:
            c = [float(x) for x in b["region"]]
            if len(c) != 4 or not (0 <= c[0] < c[2] <= 1 and 0 <= c[1] < c[3] <= 1):
                raise ValueError("구역은 [x0,y0,x1,y1], 0~1, x0<x1·y0<y1")
            spec["regions"][st["region"]] = c
        ap.save_spec(spec)
        # 토큰 검사는 여기서 하지 않는다 — CLIP 토크나이저 로드가 십수 초라 저장이 그만큼 멈춘다.
        # 화면이 저장 직후 `/tokens`를 따로 부른다(계획의 「저장 **전** 토큰 검사」는 그 호출이 진다).
        self.send(200, detail(scene))

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PATCH(self):
        self.route("PATCH")


# 용어집도 갈아끼울 수 있어야 한다 — 스모크가 가짜 뜻을 실제 용어집에 쌓으면 안 된다
# (같은 종류의 사고를 산출 경로에서 이미 한 번 냈다, ad8815c).
GLOSS_PATH = os.environ.get("SCENE_TOOL_GLOSSARY") or os.path.join(HERE, "glossary.json")
GLOSS_LOCK = threading.Lock()
CAST_RE = __import__("re").compile(r"^\{cast[c]?:[a-z0-9-]+\}$")


def load_gloss():
    with open(GLOSS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def frags_of(prompt):
    """문구를 화면과 **같은 규칙**으로 쪼갠다 — 다르게 쪼개면 물음표가 안 사라진다."""
    return [f.strip() for f in str(prompt).strip().rstrip(".").split(",") if f.strip()]


def unknown_terms(prompt, neg):
    g = load_gloss()
    out = [f for f in frags_of(prompt) if f not in g["frag"] and not CAST_RE.match(f)]
    out += [n.strip() for n in neg if n.strip() and n.strip() not in g["neg"]
            and n.strip() != "{head_neg}"]
    return list(dict.fromkeys(out))


def merge_gloss(prompt, neg, gloss):
    """새로 지어낸 표현의 한글 뜻을 용어집에 쌓는다 — 다음 번에는 물음표가 안 뜬다."""
    if not gloss:
        return 0
    frag_keys, neg_keys = set(frags_of(prompt)), {n.strip() for n in neg}
    with GLOSS_LOCK:
        g = load_gloss()
        added = 0
        for k, v in gloss.items():
            k = k.strip()
            if not k or CAST_RE.match(k):
                continue
            if k in frag_keys and k not in g["frag"]:
                g["frag"][k] = v
                added += 1
            if k in neg_keys and k not in g["neg"]:
                g["neg"][k] = v
                added += 1
        if added:
            g["frag"] = dict(sorted(g["frag"].items()))
            g["neg"] = dict(sorted(g["neg"].items()))
            tmp = GLOSS_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(g, fh, ensure_ascii=False, indent=1)
                fh.write("\n")
            os.replace(tmp, GLOSS_PATH)     # 반쯤 쓰인 파일이 남지 않게
    return added


def gloss_now(prompt, neg):
    """손으로 고친 문구에 남은 **모르는 조각만** 번역해 용어집에 넣는다."""
    terms = unknown_terms(prompt, neg)
    if not terms:
        return {"gloss": {}, "added": 0, "note": "모르는 낱말이 없다"}
    got = cp.translate(terms)
    added = merge_gloss(prompt, neg, got)
    return {"gloss": got, "added": added}


def compose_now(scene, stage_id, ask):
    """한국어 지시 + 명세의 근거 → AI가 지은 영문 문구. **명세에 쓰지 않는다.**"""
    spec = ap.load_spec(scene)
    st = next((x for x in spec["stages"] if x["id"] == stage_id), None)
    if st is None:
        raise ValueError(f"단계 {stage_id}가 명세에 없다")
    casts = {}
    for f in spec.get("figures", []):
        cid = f.get("cast")
        if cid and cid not in casts:
            try:
                casts[cid] = ds.cast_describe(ds.load_cast(cid))
            except FileNotFoundError:
                pass
    frags = list(load_gloss()["frag"])
    out = cp.compose(spec, st, ask, casts, frags)
    out["tokens"] = measure(scene, out["prompt"], out["neg"])
    # 지어낸 표현의 한글 뜻을 곧바로 용어집에 쌓는다. AI 호출을 한 번 더 하지 않는다 —
    # 지은 쪽이 뜻도 함께 내놓게 계약에 넣어 뒀다.
    out["added"] = merge_gloss(out["prompt"], out["neg"], out.get("gloss"))
    left = unknown_terms(out["prompt"], out["neg"])
    if left:                                # 그래도 빠진 것이 있으면 그것만 따로 번역한다
        try:
            more = cp.translate(left)
            out["added"] += merge_gloss(out["prompt"], out["neg"], more)
            out["gloss"] = {**(out.get("gloss") or {}), **more}
        except Exception as e:              # noqa: BLE001 — 번역 실패가 문구 짓기를 무르지 않는다
            out["glossNote"] = f"남은 낱말 번역 실패: {e}"
    return out


def run_compose(jid, fn, *args):
    """배경에서 AI를 부르고 결과만 남긴다. 화면은 번호로 물어본다."""
    try:
        out = fn(*args)
        out["status"] = "done"
    except Exception as e:                            # noqa: BLE001 — 실패도 조회로 알려야 한다
        out = {"status": "failed", "error": f"{type(e).__name__}: {e}"}
    with COMPOSE_LOCK:
        COMPOSE[jid] = out


def measure(scene, prompt, neg):
    """제안된 문구를 **저장하기 전에** 잰다. venv 쪽에서 `{cast:...}` 확장까지 포함해 센다."""
    try:
        r = subprocess.run([VENV, os.path.join(HERE, "count_tokens.py")],
                           input=json.dumps({"scene": scene, "prompt": prompt, "neg": neg}),
                           capture_output=True, text=True, timeout=180,
                           env={**os.environ, "SCENE_TOOL_SCENES_DIR": SCENES_DIR})
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:                            # noqa: BLE001 — eco: 재기 실패가 짓기를 막지 않는다
        return {"ok": None, "tail": f"토큰을 재지 못했다: {e}"}


def token_check(scene):
    """`derive_scene --check`를 GPU 0으로 부른다. eco: best-effort — venv가 없으면 조용히 건너뛴다."""
    try:
        r = subprocess.run([VENV, "derive_scene.py", scene, "--check"],
                           cwd=CANON, capture_output=True, text=True, timeout=180,
                           env={**os.environ, "SCENE_TOOL_SCENES_DIR": SCENES_DIR})
        over = [ln for ln in r.stdout.splitlines() if "넘친다" in ln]
        return {"ok": r.returncode == 0, "over": over,
                "tail": "\n".join((r.stdout + r.stderr).strip().splitlines()[-6:])}
    except Exception as e:                            # noqa: BLE001
        return {"ok": None, "over": [], "tail": f"토큰 검사를 건너뛰었다: {e}"}


class Srv(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        # `HTTPServer.server_bind`는 `socket.getfqdn()`으로 역방향 조회를 한다. 이 머신에서 그것이
        # 수십 초씩 멈춰 **바인드 전에 서버가 굳었다**(실측: 연결이 거절이 아니라 타임아웃). 서버 이름을
        # 쓰지 않으므로 조회를 건너뛴다.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = BIND, self.server_address[1]


def main():
    if not USERS and not DEV and not TOKEN:
        sys.exit("SCENE_TOOL_USERS · SCENE_TOOL_TOKEN · SCENE_TOOL_DEV=1 중 하나는 있어야 한다")
    threading.Thread(target=worker, daemon=True).start()
    if BIND != "127.0.0.1" and not TOKEN and not USERS:  # noqa: SIM102 — 위 가드와 뜻이 다르다
        # 이 도구는 GPU를 돌리고 명세를 고친다. 자물쇠 없이 망에 내놓지 않는다.
        sys.exit("SCENE_TOOL_BIND가 루프백 밖이면 SCENE_TOOL_TOKEN이나 SCENE_TOOL_USERS가 있어야 한다")
    if BIND != "127.0.0.1" and DEV:
        sys.exit("SCENE_TOOL_DEV=1은 루프백에서만 쓴다 — 망에 내놓으면 아무나 들어온다")
    srv = Srv((BIND, PORT), H)
    print(f"장면 승인 도구 · http://{BIND}:{PORT}  "
          f"(허용 {USERS or '—'} · 토큰 {'있음' if TOKEN else '없음'} · DEV={int(DEV)} · FAKE_GEN={int(FAKE)})",
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
