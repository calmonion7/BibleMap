#!/usr/bin/env python3
"""AI 판정자 — 그림 + 장면 명세·인물 정본에서 파생한 채점표 → `claude -p`(구독) → {pass, scores, reasons}.

  judge_vlm.py <image> --scene <id> --layer bg|figure:<인물키>|full   # stdout JSON
  judge_vlm.py --calibrate                                            # calibration.json 전건, `일치: N/M`
"""
import argparse, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(CANON, "..", ".."))
CAL = os.path.join(HERE, "calibration.json")


def _load(*p):
    with open(os.path.join(CANON, *p), encoding="utf-8") as fh:
        return json.load(fh)


def _cast_lines(cid):
    c = _load("cast", f"{cid}.json")
    f = [f"{k}: {c[k]}" for k in ("age", "hair", "beard", "headwear", "build", "costume") if c.get(k)]
    return f"- {cid} ({'/'.join(c.get('names', [])[:1])}): " + "; ".join(f)


ARTIFACTS = ("인공물: 손가락 수·형태 붕괴, 얼굴 뭉개짐·비대칭 붕괴, 같은 인물의 복제, 몸에서 떨어져 허공에 뜬 지물, "
             "지물이 몸을 관통하거나 어깨·몸에서 자라난 듯한 형태, 각진 패치·타일 같은 질감 붕괴, 액자·테두리·글자·워터마크, "
             "정본에 있는 머리쓰개·수염·뿔 등 핵심 특징의 소실")
STYLE = "화풍: 일관된 손그린 삽화풍(성경 삽화). 사진·3D·만화 캐리커처·소품 삽화 모음 같은 구도 파괴는 감점."


def rubric(scene, layer):
    s = _load("scenes", f"{scene}.json")
    figs = s["figures"]
    if layer == "bg":
        return ("층: 배경판. 규칙: 사람·인물·동물 형상이 하나도 없는 순수 풍경이어야 한다(조금이라도 있으면 불통과). "
                f"기대 배경: {s['background']}\n구도가 명세의 지형과 맞는가, {ARTIFACTS}, {STYLE}")
    if layer.startswith("figure:"):
        key = layer.split(":", 1)[1]
        f = next((x for x in figs if x["cast"] == key), None)
        if f is None:
            sys.exit(f"장면에 인물 {key} 없음")
        return ("층: 인물 판. 규칙: 인물이 정확히 한 명, 흰 단색 배경, 머리부터 발까지 전신이 잘림 없이 보여야 한다. "
                f"기대 인물(정본): {_cast_lines(key)}\n기대 자세: {f['pose']}; 지물: {f['prop']}; 방향: {f['facing']}을 향함.\n"
                f"점검: 인물 수, 방향, 지물 유무와 몸과의 접속, 머리쓰개/수염 정본 일치, {ARTIFACTS}, {STYLE}")
    cast = "\n".join(_cast_lines(f["cast"]) for f in figs)
    ko = lambda v: v.get("ko", "") if isinstance(v, dict) else (v or "")

    def _expect(f):   # 한 장 모드: gesture가 있으면 명세의 한 장 서술(gesture·expression·costume·gaze)이 기대값
        if not f.get("gesture"):
            return f"{f['pose']}; 지물 {f['prop']}; {f['facing']}을 향함"
        gz = f"; 시선 {f['gaze']}" if f.get("gaze") else ""
        return f"{ko(f['gesture'])}; 표정 {ko(f.get('expression'))}; 복장 {ko(f.get('costume'))}; {f['facing']}을 향함{gz}"
    fl = "\n".join(f"- {f['cast']}: {_expect(f)}" for f in figs)
    cr = "".join(f"\n명세에 있는 배경 인물(인물 수 위반이 아님): {c['what']} — 위치 {c.get('region', '')}" for c in s.get("crowds", []))
    return (f"층: 장면 전체. 규칙: 명세의 인물 {len(figs)}명이 전부 있고 각자 정본 외형·방향·지물이 맞아야 한다. "
            f"장면: {s['moment']}\n배경: {s['background']}\n인물 정본:\n{cast}\n인물별 기대:\n{fl}{cr}\n"
            f"점검: 인물 수 일치(부족·복제 모두 불통과), 방향, 지물, 머리쓰개/수염 정본 일치, {ARTIFACTS}, {STYLE}")


PROMPT = """너는 성경 장면 삽화의 엄격한 품질 판정자다. Read 도구로 이미지 파일 {img} 를 직접 보고 판정하라. 인물 정본 문구는 식별용 참고이며 그림체상 세부(수염 유무·옷색·피부)가 조금 다른 것은 정상이다. 정면을 보는 인물이라도 몸통·발이 기대 방향이면 방향 일치로 본다. 명백히 보이는 것만 결함으로 적어라.
{rubric}

채점: 항목별 0~1(count 인물 수, pose 방향·자세·지물, canon 정본 외형 일치, style 화풍, artifact 인공물 없음).
판정 기준 — 치명 결함이 하나라도 있을 때만 pass=false: (1) 인물 수가 틀림(누락·복제·유령 인물), (2) 지물이 몸에서 떨어져 허공에 뜸·몸을 관통·어깨에서 자라남,
(3) 얼굴·손·몸의 붕괴나 각진 패치 같은 질감 붕괴, (4) 머리쓰개·투구 형태가 정본과 정반대(없어야 할 뿔·깃 추가, 있어야 할 머리쓰개 전무) — 수염·옷색·연령은 장면 역할(소년·종자 등)과 그림체에 따라 달라질 수 있어 치명이 아니다, (5) 층 규칙 위반, (6) 구도 파괴(소품 삽화 모음 등).
경미한 차이는 감점만 하고 통과시킨다: 옷 색조·무늬의 미세한 차이, 연령 표현의 약간의 차이, 방향이 정확한 측면이 아니라 3/4 시선·몸통 쪽이면 허용,
자세 서술이 대략 맞는 경우. 화풍은 일관된 삽화풍이면 충분하다. 결함은 눈에 보이는 것만 근거로 하고 추측하지 말라.
reasons는 한국어 짧은 문장 배열(결함 구체 서술). 설명 없이 JSON 한 개만 출력:
{{"pass": true|false, "scores": {{"count":0.0,"pose":0.0,"canon":0.0,"style":0.0,"artifact":0.0}}, "reasons": ["..."]}}"""


BLIND = """Read 도구로 이미지 파일 {img} 를 직접 보라. 이 그림에서 무슨 일이 일어나고 있는가? 누가(어떤 사람·옷차림·표정) 누구에게 무엇을 하는지, 장소와 순간이 무엇인지 3~4문장 한국어로 서술하라. 성경 지식으로 추측해 이름을 붙이지 말고 눈에 보이는 것만 적어라. 서술만 출력."""

MEANING = """너는 성경 장면 삽화 판정자다. 한 사람이 이 그림을 처음 보고 쓴 서술(blind)이 장면의 의도된 뜻을 읽어냈는지 대조하라. 그림은 보지 말고 글만 비교한다.
의도된 뜻: {meaning}
의도된 관계: {relation}
서술(blind): {blind}

채점 0~1: 서술이 (1) 뜻의 핵심 사건·행위를, (2) 관계(누가 누구를 향해 무엇을 하는가)를 담아야 높다. 인물이 있다는 말, 배경·옷차림 묘사만 있고 사건·관계가 없으면 0.4 이하. 사건은 맞으나 관계가 흐리면 0.5~0.7. 핵심 사건과 관계가 모두 읽히면 0.8 이상. 관대하게 보지 말라.
설명 없이 JSON 한 개만: {{"meaning": 0.0, "reason": "한국어 한 문장"}}"""

MEANING_PASS = 0.7


def _claude(prompt, img=None):
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if img:
        cmd += ["--allowedTools", "Read", "--add-dir", os.path.dirname(img)]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=tempfile.gettempdir(), timeout=300).stdout


def _json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _spec_meaning(scene):
    """명세 meaning·relation({ko,...} 또는 문자열), 없으면 moment.why·figures로 대체."""
    s = _load("scenes", f"{scene}.json")
    t = lambda v: v.get("ko", "") if isinstance(v, dict) else (v or "")
    meaning = t(s.get("meaning")) or s["moment"]["why"]
    relation = t(s.get("relation")) or "; ".join(f"{f['cast']}: {f['pose']} (지물 {f['prop']}, {f['facing']}을 향함)" for f in s["figures"])
    return meaning, relation


def blind_read(image):
    return _claude(BLIND.format(img=os.path.abspath(image)), os.path.abspath(image)).strip()


def judge_meaning(blind, scene):
    meaning, relation = _spec_meaning(scene)
    for _ in range(2):
        d = _json(_claude(MEANING.format(meaning=meaning, relation=relation, blind=blind)))
        if d and "meaning" in d:
            return float(d["meaning"]), d.get("reason", "")
    return 0.0, "뜻 판정 파싱 실패"


def judge_defects(image, scene, layer):
    img = os.path.abspath(image)
    prompt = PROMPT.format(img=img, rubric=rubric(scene, layer))
    last = ""
    for _ in range(2):
        last = _claude(prompt, img)
        d = _json(last)
        if d and "pass" in d:
            return {"pass": bool(d["pass"]), "scores": d.get("scores", {}), "reasons": d.get("reasons", [])}
    return {"pass": False, "scores": {}, "reasons": ["판정 출력 파싱 실패: " + last[:200]]}


def judge(image, scene, layer):
    """v2: 맹목 읽기 → 뜻 판정(full 층만) + 결함 채점. pass = 둘 다 통과."""
    r = judge_defects(image, scene, layer)
    if layer != "full":
        return r
    blind = blind_read(image)
    ms, why = judge_meaning(blind, scene)
    r["scores"]["meaning"] = ms
    r["blind"] = blind
    if ms < MEANING_PASS:
        r["pass"] = False
        r["reasons"].append(f"뜻 미판독({ms:.2f}): {why}")
    return r


def calibrate():
    items = json.load(open(CAL, encoding="utf-8"))
    n = rev = revhit = 0
    p3 = None
    for it in items:
        r = judge(os.path.join(ROOT, it["image"]), it["scene"], it["layer"])
        want = it["label"] == "good"
        ok = r["pass"] == want
        n += ok
        name = os.path.basename(it["image"])
        print(f"{'일치' if ok else '불일치'} | {name} | 기대 {'통과' if want else '탈락'} / 판정 {'통과' if r['pass'] else '탈락'} | meaning {r['scores'].get('meaning', '-')} | {'; '.join(r['reasons'])[:200]}")
        if it.get("axes4") == "pass" and not want:  # 4축이 거꾸로 판정한 사례
            rev += 1
            revhit += ok
        if "final-ip0.0-cn0.6-fcn0.6-sip0.7-s11" in it["image"]:
            p3 = "탈락" if not r["pass"] else "통과"
    print(f"part3-first-final: {p3}")
    print(f"4축 역판정 사례 적중: {revhit}/{rev}")
    print(f"일치: {n}/{len(items)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?")
    ap.add_argument("--scene")
    ap.add_argument("--layer", default="full")
    ap.add_argument("--calibrate", action="store_true")
    a = ap.parse_args()
    if a.calibrate:
        calibrate()
    else:
        if not (a.image and a.scene):
            ap.error("image와 --scene 필요")
        print(json.dumps(judge(a.image, a.scene, a.layer), ensure_ascii=False))
