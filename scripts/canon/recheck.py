#!/usr/bin/env python3
"""규칙 원장 재검(task 392) — 규칙이 바뀌면 모든 명세·승인 그림을 다시 잰다. 지표 = 지금 규칙집 통과율.

  recheck.py ledger      # rules.json의 version을 rules 내용 해시로 다시 적는다(규칙을 고친 뒤 한 번)
  recheck.py stamp       # 승인 그림 approved.final에 spec_hash·prompt_hash·rules_version(이미 있으면 건너뜀, --force면 다시)
  recheck.py specs       # 전 명세 × 명세·파생 함수 규칙 → samples/recheck/specs.json + notes/RECHECK.md
  recheck.py images      # 승인 그림 × 그림 규칙(J1 요소·채택 상식 — claude -p Sonnet) → samples/recheck/images.json + RECHECK.md
                         #   같은 그림·같은 문항이면 지난 답을 다시 쓴다(--fresh면 다시 묻는다)
  recheck.py tokens      # (venv314 안에서 specs가 부른다) 장면마다 Z-Image 토큰 수·CLIP 77 넘는 단계 → JSON

재검은 표시만 한다 — 승인을 취소하지 않는다(ADR 260905-104910). 결과 표는 손으로 고치지 않는다(이 명령이 다시 쓴다).
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "batch"))
import params  # noqa: E402
import approve  # noqa: E402
import check_scenes  # noqa: E402
import check_cast_v2  # noqa: E402
import derive_scene as ds  # noqa: E402
import scene_state as ss  # noqa: E402

LEDGER = os.path.join(HERE, "rules.json")
OUT = os.path.join(HERE, "samples", "recheck")
RECHECK_MD = os.path.join(HERE, "notes", "RECHECK.md")
SCENES = os.path.join(HERE, "scenes")
IMG = os.path.expanduser("~/.local/biblemap-imggen")
VENV = os.path.join(IMG, ".venv314", "bin", "python")
SKIP_KEYS = ("stages", "negatives", "judge", "approved", "_format")   # 금지 낱말 검사에서 뺄 칸(판 단계 문구·판정 설정·승인 기록)


def ledger():
    with open(LEDGER, encoding="utf-8") as fh:
        return json.load(fh)


def ledger_version(L):
    return hashlib.sha256(json.dumps(L["rules"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def scene_ids():
    return sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(SCENES, "*.json")))


# ── 명세 규칙 — 함수는 오류 목록(빈 목록 = 통과) 또는 None(잴 수 없음 = none)을 낸다 ──

def banned_words(spec):
    """→ ["칸 경로: 낱말", ...] — VERSE_ELEMENT_BANNED가 명세 글(SKIP_KEYS 제외) 어디든 있으면."""
    out = []

    def walk(v, path):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, f"{path}.{k}" if path else k)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                walk(x, f"{path}[{i}]")
        elif isinstance(v, str):
            out.extend(f"{path}: {w}" for w in params.VERSE_ELEMENT_BANNED if w in v)
    walk({k: v for k, v in spec.items() if k not in SKIP_KEYS}, "")
    return out


STAGE_MARK = re.compile(r"^\[(직접|추론)\]")
VERSE_REF = re.compile(r"\d+:\d+")


def stage_why_errors(spec, verses=None):
    """생애 단계 근거(task 399, 규칙 spec.stage-from-scripture) — 인물마다 `stage_why`가 [직접]|[추론]으로 시작하고
    구절 인용(「…」)과 장·절을 담아야 한다. 호칭 낱말 하나가 아니라 직무·연대·앞뒤 문맥으로 이 장면 때 나이를 유추한다.
    verses를 주면 「인용」마다 앞에 책 이름·장:절이 붙었는지, 본문 글자 그대로인지(띄어쓰기 무시, … 로 끊음) 본다
    — 2차 검토에서 삼하 2:10 「비로소」가 빠진 인용이 추론의 하한을 흔들었다(check_cast_v2 (c2)와 같은 대조)."""
    out = []
    for f in spec["figures"]:
        w = str(f.get("stage_why", ""))
        if not STAGE_MARK.match(w) or "「" not in w or not VERSE_REF.search(w):
            out.append(f"{f['cast']}: stage_why 없음 또는 [직접]/[추론] · 「인용」 · 장:절 빠짐")
            continue
        if verses is None:
            continue
        found = list(check_cast_v2.QUOTE.finditer(w))
        if len(found) != w.count("「"):
            out.append(f"{f['cast']}: stage_why 인용 {w.count('「')}개 중 {w.count('「') - len(found)}개에 책 이름·장:절이 없어 본문과 대조 못 함")
        for m in found:
            ch, a, b = int(m.group(2)), int(m.group(3)), int(m.group(4) or m.group(3))
            src = re.sub(r"\s+", "", "".join(verses.get(f"{check_cast_v2.BOOK[m.group(1)]:02d}{ch:03d}{v:03d}", {}).get("textKo", "")
                                              for v in range(a, b + 1)))
            out += [f"{f['cast']}: stage_why {m.group(1)} {ch}:{a} 인용이 본문에 없음 「{frag.strip()[:30]}」"
                    for frag in re.split(r"…|\.\.\.", m.group(5)) if re.sub(r"\s+", "", frag) not in src]
    return out


THROWN = re.compile(r"던지|던져|던졌|쏘|쏜|떨어뜨")
AIR_SHAPES = {"spear"}   # 허공을 나는 물체 가이드 꼴(make_guide) — 새 물체가 나오면 꼴과 함께 더한다


def thrown_guide_errors(spec):
    """던짐은 가이드(task 400, 규칙 generate.thrown-guide) — 순간 절 본문에 손을 떠나 나는 물체 동사가 있으면
    명세 `guide`에 허공 물체 꼴(AIR_SHAPES)이 있어야 한다. 397·400 a1: 문구만으로는 16/16 창이 사울 손에 남아 찌르기가 됨."""
    v = spec.get("moment", {}).get("verse", "")
    if not THROWN.search(spec["verses"].get("quotes", {}).get(v, "")):
        return []
    shapes = set((spec.get("guide") or {}).get("shape", {}).values())
    return [] if shapes & AIR_SHAPES else [f"순간 {v}에 던짐·쏨 동사 — 명세 guide에 허공 물체 꼴({'·'.join(sorted(AIR_SHAPES))})이 없다"]


INDOOR = re.compile(r"\b(inside|interior|room|indoors)\b", re.I)


def guide_backdrop_errors(spec):
    """실내 가이드는 방 바탕(task 400 a2→a3, 규칙 generate.guide-backdrop) — 실내 장면(배경 문구에 inside·room …)의 guide는
    backdrop "room"이어야 한다. 실외용 바탕의 위쪽 빈 검은 띠가 캡션 자리·책 지면으로 읽혀 a2 8장 중 4장에 글자가 생겼다."""
    if "guide" not in spec:
        return []
    bg = (spec.get("whole_background") or {}).get("en", "") or " ".join(s.get("prompt", "") for s in spec.get("stages", []) if s.get("kind") == "full")
    if INDOOR.search(bg) and spec["guide"].get("backdrop") != "room":
        return ["실내 장면인데 guide.backdrop이 room이 아니다 — 위쪽 빈 띠가 글자·지면으로 그려진다"]
    return []


def guide_body_errors(spec):
    """가이드 몸 너비는 카드 체격에서(task 400 a5, 규칙 generate.guide-body-build) — 사람 꼴(person*)이 있는 guide는 body "card".
    a3·a4: 카드는 넓은 어깨·통 몸통인데 기본 너비 꼴이면 체격 문구가 화면 끝 셋째 인물로 그려짐(8/8 → 3/8)."""
    g = spec.get("guide")
    if not g or not any(str(v).startswith("person") for v in g.get("shape", {}).values()):
        return []
    return [] if g.get("body") == "card" else ["guide에 사람 꼴이 있는데 body가 card가 아니다 — 몸 너비가 카드 체격을 따르지 않는다"]


HEAD_BAND = 0.13   # make_guide 사람 꼴 머리 원 지름 = 키 × 0.13


def dodge_clear_errors(spec):
    """피함은 길 밖으로(task 400 a5→a6, 규칙 generate.dodge-clear) — guide에 피하는 사람 꼴(person_dodge)과 허공 물체 꼴이 함께 있으면
    물체 구역의 세로 띠가 피하는 사람의 머리 띠(구역 위끝 ~ 키×0.13)와 겹치면 안 된다. a5: 창이 머리 높이로 곧장 → 「움츠릴 뿐 창길에서 비키지 않음」 40/40."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    sh = g.get("shape", {})
    dodgers = [k for k, v in sh.items() if v == "person_dodge"]
    objs = [k for k, v in sh.items() if v in AIR_SHAPES]
    out = []
    for d in dodgers:
        x0, y0, x1, y1 = R[d]
        top, bot = y0, y0 + (y1 - y0) * HEAD_BAND
        for o in objs:
            oy0, oy1 = R[o][1], R[o][3]
            if oy0 < bot and oy1 > top:
                out.append(f"{o} 세로 {oy0}~{oy1}이 {d} 머리 띠 {top:.3f}~{bot:.3f}와 겹침 — 피한 사람에게 곧장 날아가는 꼴")
    return out


def has_situation(spec):
    s = spec.get("situation")
    return [] if isinstance(s, dict) and str(s.get("text", "")).strip() else ["situation 칸 없음 — 장면 구절 전부로 쓴 상황 묘사가 없다"]


def _verse_elements(spec, ctx):
    if not spec.get("verse_elements"):
        return ["verse_elements 없음 — 구절 시각 요소 목록 미작성"]
    return check_scenes.verse_element_errors(spec, ds.route_prompt(spec), ctx["verses"])


def _cast(spec, ctx):
    errs = []
    for cid in dict.fromkeys(f["cast"] for f in spec["figures"]):
        if cid not in ctx["casts"]:
            errs.append(f"{cid}: cast 카드 없음")
            continue
        errs += [f"{cid} {e}" for e in ctx["casts"][cid]]
    return errs


def _tok(key):
    def f(spec, ctx):
        t = (ctx["tokens"] or {}).get(spec["id"])
        if not t or key not in t:
            return None
        if key == "z":
            return [] if t["z"] <= check_scenes.WHOLE_MAX else [f"한 장 프롬프트 {t['z']}토큰 > {check_scenes.WHOLE_MAX} — 뒤쪽이 잘린다"]
        return [f"{s}: CLIP 77토큰 넘침" for s in t["clip_over"]]
    return f


SPEC_CHECKS = {
    "check_scenes.check": lambda spec, ctx: check_scenes.check(spec, ctx["verses"]),
    "derive_scene.check_whole": lambda spec, ctx: ds.check_whole(spec),
    "check_scenes.verse_element_errors": _verse_elements,
    "recheck.banned_words": lambda spec, ctx: banned_words(spec),
    "recheck.has_situation": lambda spec, ctx: has_situation(spec),
    "check_cast_v2.check": _cast,
    "derive_scene.route_prompt": lambda spec, ctx: [] if ds.route_prompt(spec).strip() else ["파생 프롬프트가 비었다"],
    "derive_scene.head_text": lambda spec, ctx: ["파생 프롬프트에 「bare head」"] if "bare head" in ds.route_prompt(spec).lower() else [],
    "derive_scene.stages": _tok("clip_over"),
    "check_scenes.whole_prompt_overflow": _tok("z"),
    "check_scenes.prop_in_prompt_errors": lambda spec, ctx: check_scenes.prop_in_prompt_errors(spec, ds.route_prompt(spec)),
    "check_scenes.place_on_figure_errors": lambda spec, ctx: check_scenes.place_on_figure_errors(spec),
    "recheck.stage_why_errors": lambda spec, ctx: stage_why_errors(spec, ctx["verses"]),
    "recheck.thrown_guide_errors": lambda spec, ctx: thrown_guide_errors(spec),
    "recheck.guide_backdrop_errors": lambda spec, ctx: guide_backdrop_errors(spec),
    "recheck.guide_body_errors": lambda spec, ctx: guide_body_errors(spec),
    "recheck.dodge_clear_errors": lambda spec, ctx: dodge_clear_errors(spec),
    "check_scenes.lexicon_look_errors": lambda spec, ctx: check_scenes.lexicon_look_errors(spec, ds.route_prompt(spec)),
}


def spec_rules(L):
    """원장에서 명세에 돌릴 규칙 — layer spec|derive이고 check가 함수 경로. 폐기(retired) 규칙은 뺀다(통과율에서도)."""
    rs = [r for r in L["rules"] if r["layer"] in ("spec", "derive", "generate") and r["check"] not in ("human", "todo")
          and not r["check"].startswith("test:") and not r.get("retired")]
    rs = [r for r in rs if r["layer"] != "generate" or r["check"] in SPEC_CHECKS]   # 생성 층은 명세로 재는 것만(관문 자체는 뺌)
    unknown = [r["id"] for r in rs if r["check"] not in SPEC_CHECKS]
    if unknown:
        raise SystemExit(f"[Recheck] 원장 함수 규칙에 실행기가 없다: {unknown}")
    return rs


def tokens_here(ids):
    """→ {장면: {z, clip_over}} — 토크나이저(transformers)가 이 파이썬에 있어야 한다."""
    from transformers import CLIPTokenizer
    n = check_scenes.zimage_tokens()
    clip = CLIPTokenizer.from_pretrained(params.SDXL_BASE, subfolder="tokenizer")
    out = {}
    for sid in ids:
        spec, t = ds.load(sid), {}
        try:
            t["z"] = n(ds.route_prompt(spec))
        except Exception as e:  # noqa: BLE001 — 장면 하나가 깨져도 나머지는 잰다
            t["z_error"] = f"{type(e).__name__}: {e}"
        try:
            t["clip_over"] = [s["id"] for s in ds.stages(spec) if not s["skip"] and len(clip(s["prompt"]).input_ids) > clip.model_max_length]
        except Exception as e:  # noqa: BLE001
            t["clip_error"] = f"{type(e).__name__}: {e}"
        out[sid] = t
    return out


def tokens(ids):
    """→ ({장면: 토큰}, 출처) — 이 파이썬에 토크나이저가 없으면 venv314로 돌린다, 그것도 없으면 (None, 이유)."""
    try:
        import transformers  # noqa: F401
        return tokens_here(ids), "this python"
    except ImportError:
        pass
    if not os.path.exists(VENV):
        return None, "토크나이저 없음(venv314 없음)"
    r = subprocess.run([VENV, os.path.abspath(__file__), "tokens"], capture_output=True, text=True, cwd=HERE, timeout=900)
    if r.returncode:
        return None, f"venv314 실패: {r.stderr.strip()[-300:]}"
    return json.loads(r.stdout.strip().splitlines()[-1]), "venv314"


def _context(ids):
    """명세 규칙 실행 재료 — 구절·cast 검사 결과·토큰 수(못 재면 None)."""
    with open(check_scenes.VERSES, encoding="utf-8") as fh:
        verses = json.load(fh)
    casts = {}
    for p in glob.glob(os.path.join(HERE, "cast", "*.json")):
        with open(p, encoding="utf-8") as fh:
            c = json.load(fh)
        casts[c["id"]] = check_cast_v2.check(c, verses)
    tok, tok_src = tokens(ids)
    return {"verses": verses, "casts": casts, "tokens": tok}, tok_src


def _eval(spec, rules, ctx):
    """→ ({규칙: pass|fail|none}, {규칙: 오류 앞 6개})."""
    row, det = {}, {}
    for r in rules:
        try:
            errs = SPEC_CHECKS[r["check"]](spec, ctx)
        except Exception as e:  # noqa: BLE001 — 검사기가 이 명세에서 죽으면 실패로 센다(이유를 남긴다)
            errs = [f"검사 중 오류 {type(e).__name__}: {e}"]
        row[r["id"]] = "none" if errs is None else ("fail" if errs else "pass")
        if errs:
            det[r["id"]] = errs[:6]
    return row, det


def spec_failures(sid, details=False):
    """task 399 생성 관문 — 이 명세에 걸리는 명세·파생 함수 규칙 id 목록(못 잼도 통과가 아니다). details면 (목록, 오류)."""
    ctx, _ = _context([sid])
    row, det = _eval(ds.load(sid), spec_rules(ledger()), ctx)
    bad = [k for k, v in row.items() if v != "pass"]
    return (bad, {k: det.get(k, ["못 잼"]) for k in bad}) if details else bad


def require_pass(sid):
    """새 그림을 만드는 정본 생성 명령이 첫 GPU 호출 전에 부른다(규칙 generate.spec-gate) — 걸리면 멈춘다, 우회 없음."""
    bad, det = spec_failures(sid, details=True)
    if bad:
        sys.exit(f"[Recheck] 명세 규칙 불통과: {sid} — " + " · ".join(f"{k} ({det[k][0]})" for k in bad))


def specs():
    L = ledger()
    rules, ids = spec_rules(L), scene_ids()
    ctx, tok_src = _context(ids)
    table, details = {}, {}
    for sid in ids:
        table[sid], details[sid] = _eval(ds.load(sid), rules, ctx)
    out = {"rules_version": L["version"], "tokens": tok_src, "specs": table, "details": details,
           "rules": [summary(r, {sid: table[sid][r["id"]] for sid in ids}) for r in rules]}
    _write("specs.json", out)
    notes_section("specs", specs_md(out, rules))
    print(f"[Recheck] 명세 {len(ids)} × 규칙 {len(rules)} · 토큰 {tok_src} · 전 규칙 통과 {sum(all(v != 'fail' for v in t.values()) for t in table.values())}/{len(ids)}")
    return out


def summary(r, col):
    by = {k: sorted(s for s, v in col.items() if v == k) for k in ("pass", "fail", "stale", "none")}
    n = len(by["pass"]) + len(by["fail"]) + len(by["stale"])
    return {"id": r["id"], "layer": r["layer"], "scope": r["scope"], "check": r["check"], **by,
            "rate": round(len(by["pass"]) / n, 4) if n else None}


# ── 승인 그림 ──

def approved():
    """→ [(장면, 명세, final)] — approved.final이 있는 명세."""
    out = []
    for sid in scene_ids():
        spec = ds.load(sid)
        f = (spec.get("approved") or {}).get("final")
        if f:
            out.append((sid, spec, f))
    return out


def _seed_rec(seeds, seed):
    return next((x for x in seeds if str(x.get("seed")) == str(seed)), None)


def source(sid, f):
    """승인 그림의 출처 → {image, prompt, boxes, why} — 생성 묶음 metrics에서 그 시드의 프롬프트·몸 상자를 찾는다."""
    if f.get("path") == "local-edit":   # 국소 편집: 바탕은 plain-words 회차(steps[0].base_src = 「plain-words r2 s5」)
        m = re.match(r"plain-words (\S+) s(\d+)", f["steps"][0].get("base_src", ""))
        sc = json.load(open(os.path.join(HERE, "samples", "plain-words", "metrics.json")))["rounds"][m.group(1)]["scenes"][sid]
        x = _seed_rec(sc["seeds"], m.group(2))
        return {"image": os.path.join(HERE, f["image"]), "prompt": sc.get("prompt"), "boxes": (x or {}).get("boxes"),
                "from": f"plain-words {m.group(1)} s{m.group(2)} + 국소 편집"}
    if f.get("path") == "night-pick":
        img = f["image"] if os.path.isabs(f["image"]) else os.path.join(HERE, f["image"])
        bundle = os.path.relpath(img, IMG).split(os.sep)[0] if img.startswith(IMG) else f["image"].split("/")[1]
        m = json.load(open(os.path.join(HERE, "samples", bundle, "metrics.json")))
        sc = (m.get("scenes") or {}).get(sid)
        if sc is None:   # restyle 회차: 장면 하나 — 프롬프트는 맨 위, 몸 상자 기록 없음
            return {"image": img, "prompt": m.get("prompt"), "boxes": None, "from": bundle,
                    "why_boxes": f"{bundle} 기록에 몸 크롭 상자가 없다(바탕과 다른 그림) — OWLv2 상자는 GPU 단계라 이번 범위 밖"}
        x = _seed_rec(sc["seeds"], f["seed"])
        return {"image": img, "prompt": sc.get("prompt"), "boxes": (x or {}).get("boxes"), "from": bundle}
    # 단계 사다리 완료(attempt) — 한 장 프롬프트 없음, 그림은 곁파일의 마지막 캔버스
    side = approve.load_side(sid)
    a = next(a for a in side["attempts"] if a["id"] == f["attempt"])
    img = os.path.join(params.REPO_ROOT, a["images"][str(f["seed"])]["canvas"])
    return {"image": img, "prompt": None, "boxes": None, "from": f"단계 사다리 {f['attempt']}",
            "why_prompt": "단계 사다리 경로 — 단계별 판 문구로 그려 한 장 프롬프트가 없다",
            "why_boxes": "단계 사다리 그림에 몸 크롭 상자 기록이 없다 — OWLv2 상자는 GPU 단계라 이번 범위 밖"}


def stamp(force=False):
    """승인 그림 approved.final에 출처 해시를 적는다. 생성 때 명세는 기록이 없어 지금 명세 해시를 적고,
    생성 때 프롬프트가 지금 파생과 같으면 「생성 때 명세 = 지금 명세」, 다르면 prompt_matches_spec: false와 이유."""
    ver = ledger()["version"]
    n = 0
    for sid, spec, f in approved():
        if "spec_hash" in f and not force:
            continue
        src = source(sid, f)
        f.update(spec_hash=ss.spec_hash(spec), rules_version=ver)
        for k in ("prompt_hash_why", "spec_hash_why", "prompt_matches_spec"):
            f.pop(k, None)
        if src["prompt"] is None:
            f.update(prompt_hash=None, prompt_hash_why=src["why_prompt"],
                     spec_hash_why=f"생성 때 명세 기록 없음 — {f.get('on')} 승인 뒤 지금 명세의 해시")
        else:
            f["prompt_hash"] = ss.prompt_hash(src["prompt"])
            f["prompt_matches_spec"] = src["prompt"] == ds.route_prompt(spec)
            if not f["prompt_matches_spec"]:
                f["spec_hash_why"] = f"생성 때 프롬프트({src['from']})가 지금 명세의 파생과 다름 — 생성 때 명세 기록 없음, 지금 명세의 해시"
        approve.save_spec(spec)
        n += 1
        print(f"[Recheck] stamp {sid} prompt {'같음' if f.get('prompt_matches_spec') else '다름/없음'}")
    print(f"[Recheck] 출처 해시 {n}장 적음")


def _maj(answers):
    """[{qid: 맞음|틀림}, ...] → {qid: 다수 답}."""
    keys = {k for a in answers for k in a}
    return {k: ("틀림" if sum(a.get(k) == "틀림" for a in answers) * 2 > len(answers) else "맞음") for k in keys}


def _ask(J, it, header, zoom, label):
    d, files = J.prepare(it, "recheck", zoom)
    text, got, tries = J.prompt(it, files, header), None, []
    for _ in range(2):   # JSON이 깨지면 한 번만 다시
        o = J.call(text, d, "sonnet")
        tries.append(J.use(o) | {"error": bool(o.get("is_error"))})
        got = None if o.get("is_error") else J.parse(o.get("result"), it["qids"])
        if got:
            break
    print(f"[Recheck] {it['key']} {label} {'ok' if got else '답 없음'}", flush=True)
    return {"ask": hashlib.sha256(text.encode()).hexdigest()[:12], "tries": tries, **(got or {"answers": None})}


def j1(J, N, sid, spec, f, src, prev):
    """J1 요소 판정 — Sonnet v2 전 문항(지물 빼고) + 지물만 Sonnet p2(크롭 2.5배). 문항은 지금 명세, 그림은 승인된 바로 그 그림."""
    figs = [x["cast"] for x in spec["figures"]]
    if not src.get("boxes") or any(c not in src["boxes"] for c in figs):
        return "none", src.get("why_boxes") or f"몸 크롭 상자 없음: {[c for c in figs if c not in (src.get('boxes') or {})]}", None
    qs = [q for q in N.questions(spec, {"seeds": [{"seed": f["seed"], "base": src["image"], "boxes": src["boxes"]}]}, True)
          if not q["id"].endswith(".identity")]
    base = {"key": f"approved:{sid}", "task": "approved", "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
            "seed": f["seed"], "src": src["image"]}
    runs = {}
    for name, header, zoom, sel in (("v2", "v2", 1.0, lambda q: N.cls(q["id"]) != "prop"), ("p2", "p2", 2.5, lambda q: N.cls(q["id"]) == "prop")):
        part = [q for q in qs if sel(q)]
        if not part:
            continue
        it = {**base, "qs": part, "qids": [q["id"] for q in part]}
        old = (prev or {}).get(name)
        d, files = J.prepare(it, "recheck", zoom)
        same = old and old.get("answers") and old.get("ask") == hashlib.sha256(J.prompt(it, files, J.HEADERS[header]).encode()).hexdigest()[:12]
        runs[name] = old if same else _ask(J, it, J.HEADERS[header], zoom, f"J1 {name}")
    if any(not r.get("answers") for r in runs.values()):
        return "none", "J1 답 없음(호출 실패)", runs
    ans = {k: v for r in runs.values() for k, v in r["answers"].items()}
    wrong = sorted(k for k, v in ans.items() if v == "틀림")
    return ("fail" if wrong else "pass"), ("틀림 " + ", ".join(wrong) if wrong else f"{len(ans)}문항 맞음"), runs


def plaus(J, P, sid, spec, f, src, prev):
    """채택 상식 규칙(notes/PLAUSIBILITY.md 「채택:」) — 걸린 문항을 3회 묻고 다수결(규칙을 채택할 때와 같은 방식)."""
    qs = P.questions(spec, adopted_only=True)
    if not qs:
        return "pass", "걸린 채택 문항 0", None
    for q in qs:
        q.pop("crop_keys", None)
    it = {"key": f"approved:{sid}", "task": "plaus", "scene": sid, "title": spec["title"], "range": spec["verses"]["range"],
          "seed": f["seed"], "src": src["image"], "qs": qs, "qids": [q["id"] for q in qs]}
    d, files = J.prepare(it, "recheck", 1.0)
    ask = hashlib.sha256(J.prompt(it, files, P.HEADER).encode()).hexdigest()[:12]
    reps = [r for r in (prev or {}).get("reps", []) if r.get("answers") and r.get("ask") == ask]
    reps += [_ask(J, it, P.HEADER, 1.0, f"상식 {i + 1}") for i in range(len(reps), P.FX["reps"])]
    if any(not r.get("answers") for r in reps):
        return "none", "상식 답 없음(호출 실패)", {"reps": reps}
    maj = _maj([r["answers"] for r in reps])
    wrong = sorted(k for k, v in maj.items() if v == "틀림")
    return ("fail" if wrong else "pass"), ("틀림 " + ", ".join(wrong) if wrong else f"{len(maj)}문항 맞음"), {"reps": reps, "majority": maj}


def images(fresh=False, workers=4):
    import judge_items as J
    import make_night_page as N
    import plausibility as P
    L = ledger()
    sp = _read("specs.json")
    if not sp or sp["rules_version"] != L["version"]:
        raise SystemExit("[Recheck] specs.json이 없거나 원장 판이 다르다 — recheck.py specs 먼저")
    old = {} if fresh else (_read("images.json") or {}).get("images", {})
    todo = approved()

    def one(row):
        sid, spec, f = row
        src = source(sid, f)
        changed = f.get("spec_hash") != ss.spec_hash(spec)
        rules, why = {}, {}
        prev = old.get(sid, {})
        rules["judge.j1-items"], why["judge.j1-items"], j1_runs = j1(J, N, sid, spec, f, src, prev.get("j1"))
        rules["judge.plausibility-adopted"], why["judge.plausibility-adopted"], pl = plaus(J, P, sid, spec, f, src, prev.get("plausibility"))
        rules["judge.style"], why["judge.style"] = "none", "화풍 판정자 조건부(판정자 재현성) — 승인 그림 재검에 아직 안 씀"
        rules["human.face-matched-quality"], why["human.face-matched-quality"] = "none", "얼굴은 사람 판정 — 화질 맞춤 화면(task 393) 전"
        for r in sp["rules"]:   # 명세·파생 규칙: 이 그림의 명세가 지금 규칙을 어기면 그림은 낡음(stale)
            v = sp["specs"][sid][r["id"]]
            rules[r["id"]] = "stale" if changed or v == "fail" else v
            if rules[r["id"]] == "stale":
                why[r["id"]] = "그림 뒤 명세가 바뀜" if changed else "명세가 지금 규칙을 어김: " + "; ".join(sp["details"][sid].get(r["id"], []))[:200]
        if f.get("prompt_matches_spec") is False:
            rules["derive.no-hand-prompt"], why["derive.no-hand-prompt"] = "stale", f.get("spec_hash_why", "생성 때 프롬프트 ≠ 지금 파생")
        return sid, {"image": src["image"], "seed": f["seed"], "path": f.get("path") or f"attempt {f.get('attempt')}", "from": src["from"],
                     "spec_changed": changed, "prompt_matches_spec": f.get("prompt_matches_spec"), "rules": rules, "why": why,
                     "j1": j1_runs, "plausibility": pl}

    with ThreadPoolExecutor(workers) as ex:
        res = dict(ex.map(one, todo))
    cols = sorted({k for v in res.values() for k in v["rules"]}, key=lambda k: [r["id"] for r in L["rules"]].index(k))
    out = {"rules_version": L["version"], "images": res,
           "rules": [summary(next(r for r in L["rules"] if r["id"] == k), {s: v["rules"][k] for s, v in res.items()}) for k in cols]}
    _write("images.json", out)
    notes_section("images", images_md(out))
    ok = sum(all(x == "pass" or x == "none" for x in v["rules"].values()) for v in res.values())
    print(f"[Recheck] 승인 그림 {len(res)} · 잰 규칙 모두 통과 {ok}/{len(res)}")
    return out


# ── 기록 ──

def _read(name):
    p = os.path.join(OUT, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


MARK = {"pass": "✅", "fail": "✗", "stale": "낡음", "none": "–"}


def short(sid):
    return sid.replace("authored-", "")


def specs_md(out, rules):
    ids = sorted(out["specs"])
    lines = [f"원장 판 `{out['rules_version']}` · 토큰 검사 {out['tokens']} · 명세 {len(ids)}", "",
             "| 규칙 | 층 | 원래 범위 | 통과 | 실패 | 못 잼 | 통과율 |", "|---|---|---|---|---|---|---|"]
    for r in out["rules"]:
        rate = "–" if r["rate"] is None else f"{r['rate'] * 100:.0f}%"
        lines.append(f"| `{r['id']}` | {r['layer']} | {r['scope']} | {len(r['pass'])} | {len(r['fail'])} | {len(r['none'])} | {rate} |")
    full = [s for s in ids if all(v != "fail" for v in out["specs"][s].values())]
    cells = [v for t in out["specs"].values() for v in t.values() if v != "none"]
    retired = [r for r in ledger()["rules"] if r.get("retired")]
    if retired:
        lines += ["", "폐기 규칙(재검·통과율에서 뺌): " + " · ".join(f"`{r['id']}` — {r['retired']}" for r in retired)]
    lines += ["", f"**전 규칙 통과 명세 {len(full)}/{len(ids)}** · 칸 통과 {sum(v == 'pass' for v in cells)}/{len(cells)}"
              f" ({sum(v == 'pass' for v in cells) / len(cells) * 100:.0f}%)", ""]
    head = [r["id"].split(".", 1)[1] for r in rules]
    lines += ["| 명세 | " + " | ".join(head) + " |", "|---|" + "---|" * len(head)]
    for s in ids:
        lines.append(f"| {short(s)} | " + " | ".join(MARK[out["specs"][s][r['id']]] for r in rules) + " |")
    return "\n".join(lines)


def images_md(out):
    res = out["images"]
    cols = [r["id"] for r in out["rules"]]
    lines = [f"원장 판 `{out['rules_version']}` · 승인 그림 {len(res)} · ✅ 통과 · ✗ 실패 · 낡음 = 명세가 바뀌었거나 지금 규칙을 어김 · – 못 잼", "",
             "| 규칙 | 통과 | 실패 | 낡음 | 못 잼 |", "|---|---|---|---|---|"]
    for r in out["rules"]:
        lines.append(f"| `{r['id']}` | {len(r['pass'])} | {len(r['fail'])} | {len(r['stale'])} | {len(r['none'])} |")
    clean = [s for s, v in res.items() if all(x in ("pass", "none") for x in v["rules"].values())]
    lines += ["", f"**잰 규칙 모두 통과(실패·낡음 0) {len(clean)}/{len(res)}**", "",
              "| 승인 그림 | 경로 | J1 요소 | 상식 | 낡음 규칙 |", "|---|---|---|---|---|"]
    for s in sorted(res):
        v = res[s]
        st = [c.split(".", 1)[1] for c in cols if v["rules"][c] == "stale"]
        lines.append(f"| {short(s)} | {v['path']} s{v['seed']} | {MARK[v['rules']['judge.j1-items']]} {v['why']['judge.j1-items'][:60]} | "
                     f"{MARK[v['rules']['judge.plausibility-adopted']]} {v['why']['judge.plausibility-adopted'][:40]} | {', '.join(st) or '없음'} |")
    return "\n".join(lines)


def notes_section(name, body):
    b, e = f"<!-- recheck:{name}:begin -->", f"<!-- recheck:{name}:end -->"
    t = open(RECHECK_MD, encoding="utf-8").read()
    t = t[:t.index(b) + len(b)] + "\n" + body + "\n" + t[t.index(e):]
    with open(RECHECK_MD, "w", encoding="utf-8") as fh:
        fh.write(t)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "ledger":
        L = ledger()
        L["version"] = ledger_version(L)
        t = open(LEDGER, encoding="utf-8").read()
        t = re.sub(r'"version": "[0-9a-f]*"', f'"version": "{L["version"]}"', t, count=1)
        open(LEDGER, "w", encoding="utf-8").write(t)
        print(f"[Recheck] 원장 판 {L['version']} · 규칙 {len(L['rules'])}")
    elif cmd == "stamp":
        stamp("--force" in argv)
    elif cmd == "specs":
        specs()
    elif cmd == "images":
        images("--fresh" in argv)
    elif cmd == "tokens":
        print(json.dumps(tokens_here(scene_ids()), ensure_ascii=False))
    else:
        sys.exit(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
