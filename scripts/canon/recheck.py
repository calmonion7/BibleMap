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
import scale as S  # noqa: E402 — task 408 크기 숫자는 크기 기준표(scale.json)에서만

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


HEAD_BAND = {"person_dodge": 0.13, "person_duck": 0.14}   # make_guide 피하는 꼴 머리 원 지름 = 키 × 이 값


def _near_miss(spec, region):
    """b3·task 412 — 아슬아슬한 빗나감 한도 = 피하는 사람 머리 하나 높이(기준표 나이대 머리 × 구역 키). 옛 고정 0.05는 창을 던진 팔 높이
    (사람 m16e 「창 높이가 조금 올라가야 … 던질 때 팔의 높이」)로 올리면 숙인 머리 위 0.068에서 걸림 — 머리 하나(0.084) 안은 빗나감으로 읽힘."""
    f = next((f for f in spec.get("figures", []) if f.get("region") == region), None)
    age = ((ds._cast_in_scene(f).get("card", {}).get("ageBand") or {}).get("class")) if f else None
    _, y0, _, y1 = spec["regions"][region]
    return S.head_ratio(age) * (y1 - y0)


def dodge_clear_errors(spec):
    """피함은 길 밖으로(task 400 a5→a6, 규칙 generate.dodge-clear) — guide에 피하는 사람 꼴(person_dodge·person_duck)과 허공 물체 꼴이 함께 있으면
    물체 구역의 세로 띠가 피하는 사람의 머리 띠(구역 위끝 ~ 키×0.13)와 겹치면 안 된다. a5: 창이 머리 높이로 곧장 → 「움츠릴 뿐 창길에서 비키지 않음」 40/40."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    sh = g.get("shape", {})
    dodgers = [k for k, v in sh.items() if v in HEAD_BAND]
    objs = [k for k, v in sh.items() if v in AIR_SHAPES]
    out = []
    pose = g.get("pose", {})
    for d in dodgers:
        x0, y0, x1, y1 = R[d]
        top, bot = y0, y0 + (y1 - y0) * HEAD_BAND[sh[d]]
        if d in pose:   # f4: 뼈대 인물은 뼈대의 실제 머리 자리(숙인 머리는 구역 위끝보다 아래)
            sys.path.insert(0, os.path.join(HERE, "batch"))
            import make_guide as M
            hy = min(y for k, (x, y) in M.POSES[pose[d]].items() if k in (0, 14, 15, 16, 17))
            r = M.HEAD_R["person"]
            top, bot = y0 + (y1 - y0) * (hy - r), y0 + (y1 - y0) * (hy + r)
        for o in objs:
            ox0, oy0, ox1, oy1 = R[o]
            if oy0 < bot and oy1 > top:
                out.append(f"{o} 세로 {oy0}~{oy1}이 {d} 머리 띠 {top:.3f}~{bot:.3f}와 겹침 — 피한 사람에게 곧장 날아가는 꼴")
            elif top - oy1 > _near_miss(spec, d):   # b3: 한참 위로 지나면 「겨누지도 않음」 · n1: 「그 사람 앞에서 끝남」 조건은 뺌 — 사람 m1e 「창은 3분의2쯤 날아가게」(가로 자리는 spear-two-thirds)
                out.append(f"{o}이 {d} 머리 바로 위(띠 위쪽 머리 하나 {_near_miss(spec, d):.3f} 안)를 지나 그 위까지 오지 않음 — 빗나감이 아니라 겨누지 않은 꼴")
    return out


def guide_legs_errors(spec):
    """가이드 실루엣은 차림 길이를 따른다(task 402 b1→b2, 규칙 generate.guide-costume-legs) — 차림 문구가 무릎 길이인 인물이
    가이드에 사람 꼴로 있으면 guide.legs "costume"(무릎 아래 두 다리)이어야 한다. b1: 바닥까지 넓어지는 사다리꼴이 긴 로브 실루엣이라
    「knee-length … bare shins」 문구를 이겨 사울 긴 망토 8/8."""
    g = spec.get("guide") or {}
    sh = g.get("shape", {})
    knee = [f["region"] for f in spec["figures"] if "knee-length" in (f.get("costume") or {}).get("en", "")
            and str(sh.get(f["region"], "")).startswith("person")]
    return [f"{', '.join(knee)}: 무릎 길이 차림인데 guide.legs가 costume이 아니다 — 가이드 실루엣이 긴 옷으로 그려진다"] if knee and g.get("legs") != "costume" else []


def youth_noun_errors(spec):
    """youth는 청년 명사로(task 403 r4, 규칙 derive.youth-noun) — 카드 ageBand class youth(15~20)인 인물이 있고 child가 없는데
    파생 프롬프트에 boy·girl이 있으면 걸림. c11 s101: 「boy」로 옮겨진 20세 다윗이 열두 살 아이로 그려짐(21/22 중 유일한 틀림)."""
    classes = {ds._cast_in_scene(f).get("card", {}).get("ageBand", {}).get("class") for f in spec["figures"]}
    if "youth" not in classes or "child" in classes:
        return []
    hit = re.findall(r"\b(boy|girl)s?\b", ds.route_prompt(spec), re.I)
    return [f"youth 인물인데 파생 프롬프트에 「{'·'.join(sorted(set(hit)))}」 — 청년이 아이로 그려진다"] if hit else []


FIST_WORDS = re.compile(r"\b(curled|clenched|balled|closed hand|fists?)\b", re.I)


def empty_hand_fist_errors(spec):
    """빈손은 편 손으로(task 405 r15, 규칙 derive.empty-hand-open) — 몸짓 칸(gesture.ko)에 「빈손」인 인물이 있는데
    파생 프롬프트에 주먹 낱말이 있으면 걸림. m2e~m5e: 「his hand loosely curled」 → 던진 몸짓 틀림 52표 중 47표가 「주먹을 내지르는 꼴」."""
    if not any("빈손" in (f.get("gesture") or {}).get("ko", "") for f in spec["figures"]):
        return []
    hit = FIST_WORDS.findall(ds.route_prompt(spec))
    return [f"빈손 몸짓인데 파생 프롬프트에 「{'·'.join(sorted(set(h.lower() for h in hit)))}」 — 빈손이 주먹으로 그려진다"] if hit else []


BARE_WALL = re.compile(r"\b(?:bare|plain|blank|empty)\s+walls?\b", re.I)


def wall_material_errors(spec):
    """벽은 재질 낱말로(task 405 r15, 규칙 derive.wall-material) — 파생 프롬프트에 재질 없는 「bare·plain·blank·empty wall」이 있으면 걸림.
    m5e: 「a bare wall behind David」 → 벽 앞 틀림 「다윗 뒤는 매끈한 회벽」(s23·s42) — 돌벽 방인데 그 벽만 회벽으로 그려짐."""
    hit = BARE_WALL.findall(ds.route_prompt(spec))
    return [f"재질 없는 벽 문구 「{'·'.join(sorted(set(h.lower() for h in hit)))}」 — 매끈한 회벽으로 그려진다"] if hit else []


INFLATE_BUILD = re.compile(r"\b(barrel|massive|huge|enormous|bulky)\b", re.I)


def inflating_build_errors(spec):
    """체격은 부풀리는 낱말 없이(task 405 r18, 규칙 derive.no-inflating-build) — 카드 silhouette class가 giant가 아닌 인물이 있는데
    파생 프롬프트에 barrel·massive·huge 같은 낱말이 있으면 걸림. m8e 사람 「왼쪽 사울은 비율이 안좋음」: 「thick barrel torso」 → 술통 몸통에
    튜닉 아래 다리가 짧아 보임(문항 e.saul-proportion-measure s7·s5 5/5 틀림). 거인(골리앗)은 본문이 큰 몸을 말하므로 뺀다."""
    classes = {ds._cast_in_scene(f).get("card", {}).get("silhouette", {}).get("class") for f in spec["figures"]}
    if not classes - {"giant", None}:
        return []
    hit = INFLATE_BUILD.findall(ds.route_prompt(spec)) if "giant" not in classes else []
    return [f"거인 아닌 인물의 체격 문구에 「{'·'.join(sorted(set(h.lower() for h in hit)))}」 — 몸통이 부풀어 다리가 짧아 보인다"] if hit else []


def pose_skeleton_errors(spec):
    """던진 몸짓은 포즈 뼈대로(task 403 c7~c13, 규칙 generate.pose-skeleton) — 몸짓 칸(gesture.ko)에 던짐 동사가 있는 인물은
    guide.pose에 뼈대가 있어야 함. c1~c6: 깊이 꼴은 실루엣 덩어리만 주어 사울 몸·던진 몸짓 함께 맞음 0장 → 뼈대 c7~c13 4장."""
    pose = (spec.get("guide") or {}).get("pose", {})
    miss = [f["region"] for f in spec["figures"] if THROWN.search((f.get("gesture") or {}).get("ko", "")) and f["region"] not in pose]
    return [f"{', '.join(miss)}: 몸짓에 던짐 동사가 있는데 guide.pose 뼈대가 없다 — 깊이 꼴은 던진 몸짓의 관절을 못 준다"] if miss else []


def _guide_people(spec):
    """guide 사람 구역(사람 꼴 person*·뼈대) 이름 — task 413: 이게 없으면 크기 규칙은 잴 칸이 없다(빈 통과 → 못 잼 None)."""
    g = spec.get("guide") or {}
    sh, pose = g.get("shape", {}), g.get("pose", {})
    return [k for k in dict.fromkeys(list(sh) + list(pose)) if str(sh.get(k, "")).startswith("person") or k in pose]


def figure_scale_errors(spec):
    """초점 인물 화면 키는 무리 단계 범위 안(task 403 d1 · task 409, 규칙 generate.figure-scale·derive.crowd-stage) — guide 인물 구역(사람 꼴 person*·뼈대)의
    높이가 장면 사람 수(figures + crowds[].count)의 단계 범위(S.crowd_stage — 독대 0.60~0.70 …) 밖이면 걸림. 뼈대 인물의 하한은 보이는 키 × perspective.pose_seen.
    c14 s5: 다윗 구역 0.52(숙인 꼴) → 「다윗 키가 화면 절반에 못 미치고 빈 벽이 화면 대부분」 3/3 · m1e s42 사울 0.84 → 「너무 가까이」.
    task 409 전에는 무리 꼴(crowd)이 있으면 건너뛰었다 — 이제 무리 장면은 그 단계 범위로 잰다."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    if not _guide_people(spec):   # task 413: 사람이 있는데 잴 구역이 없으면 못 잼(빈 통과 아님)
        return None if spec.get("figures") else []
    sh, pose = g.get("shape", {}), g.get("pose", {})
    stage, (lo, hi) = S.crowd_stage(S.people_count(spec))
    lo_seen = lo * S.v("perspective.pose_seen")

    def seen(k):   # h4: 뼈대 인물은 보이는 키(뼈대 머리 꼭대기 ~ 발) — 숙인 뼈대는 구역보다 작게 그려짐(h3e 숙인 다윗 「화면 절반」 5/5)
        h = R[k][3] - R[k][1]
        if k not in pose:
            return h
        sys.path.insert(0, os.path.join(HERE, "batch"))
        import make_guide as M
        top = min(y for i, (x, y) in M.POSES[pose[k]].items() if i in (0, 14, 15, 16, 17)) - M.HEAD_R["person"]
        return h * (1 - max(0.0, top))
    people = [k for k in dict.fromkeys(list(sh) + list(pose)) if str(sh.get(k, "")).startswith("person") or k in pose]
    small = [k for k in people if seen(k) < (lo_seen if k in pose else lo)]
    big = [k for k in people if R[k][3] - R[k][1] > hi]
    return ([f"{k}: 보이는 키 {seen(k):.2f} < {lo_seen if k in pose else lo:.2f}(무리 단계 {stage}) — 인물이 단계 범위보다 작게 그려진다" for k in small]
            + [f"{k}: 구역 높이 {R[k][3] - R[k][1]:.2f} > {hi}(무리 단계 {stage}) — 단계 범위보다 가깝게 그려진다" for k in big])


YOUTH_MIN_RATIO = S.v("age_height_min.youth")   # d5: 청년 구역 높이 / 같은 장면 어른 구역 높이(d4e2 다윗 0.62/0.86 = 0.72 → 「몸이 작아 12~14세」)


def youth_height_errors(spec):
    """청년은 어른 키에 가깝게(task 403 d5, 규칙 generate.youth-height) — guide 사람 꼴 인물 중 카드 ageBand youth의 구역 높이가
    같은 장면 어른(young 이상) 인물 구역 높이의 YOUTH_MIN_RATIO 미만이면 걸림. 숙인 꼴도 그림은 선 꼴로 옮겨 작은 아이가 됨(d2~d4e2)."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    sh, pose = g.get("shape", {}), g.get("pose", {})
    people = {f["region"]: ds._cast_in_scene(f).get("card", {}).get("ageBand", {}).get("class") for f in spec["figures"]
              if str(sh.get(f["region"], "")).startswith("person") or f["region"] in pose}
    if not people:   # task 413: 청년이 있는데 잴 구역이 없으면 못 잼
        return None if any(ds._cast_in_scene(f).get("card", {}).get("ageBand", {}).get("class") == "youth" for f in spec["figures"]) else []
    adult = [R[k][3] - R[k][1] for k, c in people.items() if c not in ("child", "youth")]
    if not adult:
        return []
    return [f"{k}: 청년 구역 높이 {R[k][3] - R[k][1]:.2f} < 어른 {max(adult):.2f} × {YOUTH_MIN_RATIO} — 아이처럼 작게 그려진다"
            for k, c in people.items() if c == "youth" and R[k][3] - R[k][1] < YOUTH_MIN_RATIO * max(adult)]


COUNT_WHY = ("[직접]", "[추론]", "[저작](")


def crowd_count_errors(spec):
    """무리 칸은 사람 수와 근거를 가짐(task 409, 규칙 derive.crowd-stage) — crowds[]마다 count(정수)·count_why([직접]·[추론]·[저작](이유)).
    무리 단계(S.crowd_stage)가 장면 사람 수에서 초점 인물 화면 키 범위를 정하므로, 수가 없으면 단계를 셀 수 없다."""
    return [f"무리 「{c.get('what', '')[:20]}」: count·count_why(근거 단계) 없음 — 무리 단계를 셀 수 없다"
            for c in spec.get("crowds") or []
            if not isinstance(c.get("count"), int) or not str(c.get("count_why", "")).startswith(COUNT_WHY)]


def perspective_errors(spec):
    """무리 구역은 눈높이 원근의 사람 키를 담음(task 409, 규칙 generate.eye-level-perspective) — guide 무리 꼴(crowd) 구역의 발 y(아래 끝)가
    장면 지평선(S.scene_horizon) 아래면, 그 자리 보통 키 어른 화면 키(S.screen_height)가 구역 높이를 넘으면 걸림(가이드 무리가 구역 위로 솟음).
    발이 지평선 위인 구역(강 건너 둑·언덕)은 평지 셈 밖이라 건너뜀."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    if spec.get("crowds") and "crowd" not in (g.get("shape") or {}).values():   # task 413: 무리가 있는데 잴 무리 구역이 없으면 못 잼
        return None
    hy = S.scene_horizon(spec) if g else None
    out = []
    for k, shape in (g.get("shape") or {}).items():
        if shape != "crowd" or R[k][3] <= hy:
            continue
        ph, h = S.screen_height(R[k][3], hy), R[k][3] - R[k][1]
        if ph > h:
            out.append(f"{k}: 발 y {R[k][3]:.2f}의 어른 화면 키 {ph:.2f} > 구역 높이 {h:.2f}(지평선 {hy:.3f}) — 무리 구역이 원근보다 낮다")
    return out


HEAD_TOL = 0.04   # 판정 여유(초점 화면 키 비) — 키 비 자체는 크기 기준표 height(task 408: f1 HEAD_STEP 0.87 거듭제곱 → 표 키 비 직접, 삼상 9:2 「어깨 위만큼」)


def height_ratio_errors(spec):
    """서 있는 인물의 화면 키는 눈높이 지평선에서(task 404 f1 · task 409, 규칙 generate.height-ratio·generate.eye-level-perspective) — 화면 키가 가장 큰
    guide 사람 꼴·뼈대 인물(초점)로 지평선을 정하고(S.scene_horizon), 다른 서 있는 인물의 구역 높이가 발 y에서 계산한 화면 키(S.screen_height × 카드 키 등급)와
    초점 화면 키의 ± HEAD_TOL 넘게 다르면 걸림. 같은 발 y면 옛 검사(같은 깊이 두 인물 구역 높이 비 = 표 키 비)와 같다.
    d5e·d4e2: 다윗 0.69 / 사울 0.86 = 0.80(tall vs average 한 칸) → 「거인과 아이」(두 사람 크기 3/3 틀림, 기록 c5 2/8 · c11 0/8)."""
    R = spec.get("regions", {})
    people = S.standing(spec)
    if not people and len(spec.get("figures") or []) >= 2:   # task 413: 두 사람 이상인데 잴 구역이 없으면 못 잼
        return None
    if len(people) < 2:
        return []
    hy = S.scene_horizon(spec)
    fk = max(people, key=lambda p: R[p[0]][3] - R[p[0]][1])[0]
    fh = R[fk][3] - R[fk][1]
    out = []
    for k, hr in people:
        if k == fk:
            continue
        want, got = S.screen_height(R[k][3], hy, hr), R[k][3] - R[k][1]
        if abs(got - want) / fh > HEAD_TOL:
            out.append(f"{k}: 구역 높이 {got:.2f} ≠ 지평선 {hy:.3f}에서 계산한 {want:.2f}(± 초점 {fk} 키의 {HEAD_TOL}) — 두 사람 크기가 어긋나 그려진다")
    return out


SECOND_POINT = re.compile(r"\b(pointed|spikes?|barbs?)\b", re.I)


def second_point_errors(spec):
    """부수 부위는 촉 낱말 없이(task 403 d1, 규칙 derive.no-second-point) — 파생 프롬프트에 실린 낱말 사전 look 문구(L1~L3 en)에
    pointed·spike·barb가 있으면 걸림. c14 s5: 「a short pointed iron butt-spike at the back」 → 뒤끝에 앞 촉만 한 화살촉(창 모양 3/3 틀림).
    뒤끝이 뾰족하다는 본문 근거(삼하 2:23)는 뜻·근거 칸에 두고, 그리는 문구는 크기 대비로만 쓴다."""
    with open(check_scenes.WORDS, encoding="utf-8") as fh:
        words = json.load(fh)["words"]
    low = ds.route_prompt(spec).lower()
    out = []
    for w in words:
        for k in ("L1", "L2", "L3"):
            t = w.get("look", {}).get(k, {}).get("en", "")
            if t and t.lower().rstrip(".") in low and SECOND_POINT.search(t):
                out.append(f"사전 {w['id']} {k} 문구에 「{SECOND_POINT.search(t).group(0)}」 — 부수 부위가 둘째 촉으로 그려진다")
    return out


HOLD = re.compile(r"두 손으로[^,—·]*(가슴|품)")


def pose_hold_errors(spec):
    """손 자리는 뼈대로(task 404 f4, 규칙 generate.pose-hold) — 몸짓 칸(gesture.ko)이 「두 손으로 … 가슴(품)에」처럼 손 자리를 말하는 인물은
    guide.pose 뼈대가 있어야 함. f1e~f3e: 깊이 꼴 숙인 다윗은 손 자리를 못 줘 「수금이 벽에 기대 있음」 5/5(사울 던진 몸짓 c1~c6과 같은 벽)."""
    pose = (spec.get("guide") or {}).get("pose", {})
    if "guide" not in spec:
        return []
    miss = [f["region"] for f in spec["figures"] if HOLD.search((f.get("gesture") or {}).get("ko", "")) and f["region"] not in pose]
    return [f"{', '.join(miss)}: 몸짓이 두 손 자리를 말하는데 guide.pose 뼈대가 없다 — 깊이 꼴은 손 자리를 못 준다"] if miss else []


def pose_only_errors(spec):
    """뼈대 가이드는 뼈대만(task 404 g1, 규칙 generate.pose-only-control) — guide.pose가 있으면 guide.control이 "pose"여야 함(깊이 그림을 섞지 않음).
    진단 P1·P2(gibeah-pose-diag): 깊이+뼈대 한 장은 깊이 실루엣을 선 사람으로 그려 뼈대(기운 몸통·든 뒷발)가 약하고, 숙인 다윗 깊이 꼴도 선 채로."""
    g = spec.get("guide") or {}
    return ["guide.pose가 있는데 guide.control이 pose가 아니다 — 깊이 그림과 섞이면 뼈대가 약하게 읽힌다"] if g.get("pose") and g.get("control") != "pose" else []


def split_control_errors(spec):
    """뼈대 가이드는 스텝별로(task 404 h1, 규칙 generate.split-control) — guide.pose가 있으면 guide.split: 앞 스텝 뼈대만(자세) → 다음 스텝 깊이(몸·벽).
    한 장에 섞으면 깊이 실루엣이 몸짓을 죽이고(f6 · 진단 P1·P2), 뼈대만이면 몸 덩어리·벽·수금을 잃음(g1e·g2e)."""
    g = spec.get("guide") or {}
    return ["guide.pose가 있는데 guide.split이 없다 — 깊이와 뼈대를 한 장에 섞거나 하나만 주면 맞바꿈"] if g.get("pose") and not g.get("split") else []


FLIGHT_TOL, HAND_GAP = 0.03, 0.07   # HAND_GAP m4: 그림 팔이 뼈대보다 약 0.05 더 뻗음(m3e s11 손 0.67 vs 뼈대 0.72)


def _lexicon():
    with open(check_scenes.WORDS, encoding="utf-8") as fh:
        return {w["id"]: w for w in json.load(fh)["words"]}


def prop_size_errors(spec):
    """지물 크기는 사람 몸에 견줌(task 405 m5, 규칙 derive.prop-size-relative — 사람 「사람을 줄였으면 창도 줄여야」·「창 앞촉이 큰것 같음」) —
    장면 구절 요소(kind 지물)가 잇는 사전 항목은 look.size(사람 키 등에 견준 비·문구, 부위 크기 parts)가 있어야 하고,
    그리는 문구(L2 en)에 그 크기·부위 크기 문구가 들어 있어야 함. 사람 크기를 바꿔도 지물이 같은 비로 따라가게."""
    els = spec.get("verse_elements") or []
    words, out = _lexicon(), []
    squash = lambda s: re.sub(r"\s+", "", s)
    for e in els:
        if e.get("kind") != "지물" or "out" in e:
            continue
        for w in words.values():
            if w.get("drawable", True) is False or not any(squash(f) in squash(e["quote"]) for f in [w["word"], *w["forms"]]):
                continue
            size, l2 = w["look"].get("size"), w["look"]["L2"]["en"]
            if not size:
                out.append(f"사전 {w['id']}: look.size(사람에 견준 크기) 없음")
                continue
            for ph in [size["en"]] + [p["en"] for p in size.get("parts", {}).values()]:
                if ph not in l2:
                    out.append(f"사전 {w['id']}: L2 그리는 문구에 크기 「{ph}」 없음")
    return sorted(set(out))


def prop_size_coverage_errors(spec=None):
    """손에 쥔 지물은 모두 크기를 가짐(task 408, 규칙 derive.prop-size-coverage) — 장면 figures[].prop 문구마다 크기 기준표 held_exclude
    (옷자락·빈손 — 근거와 함께)에 있거나, 그 문구를 held에 담은 사전 항목이 있고 그 항목에 look.size가 있어야 함. spec이 없으면 37명세 전부."""
    specs = [spec] if spec else [ds.load(sid) for sid in scene_ids()]
    skip = S.table()["held_exclude"]
    held = {h: w for w in _lexicon().values() for h in w.get("held", [])}
    out = []
    for sp in specs:
        for f in sp.get("figures", []):
            p = f.get("prop")
            if not p or p in skip:
                continue
            w = held.get(p)
            if not w:
                out.append(f"{sp['id']} {f.get('region')}: 손 지물 「{p}」를 held에 담은 사전 항목 없음(크기 대상 아니면 scale.json held_exclude에 근거와 함께)")
            elif not w.get("look", {}).get("size"):
                out.append(f"{sp['id']} {f.get('region')}: 손 지물 「{p}」 → 사전 {w['id']}에 look.size 없음")
    return out


HOLD_MODES = ("hand", "hug", "wear", "touch")   # 손에 쥠(그림 기본값) · 품에 안음 · 입음 · 손을 댐


def held_hold_errors(spec):
    """쥔 꼴은 사전에서(task 413, 규칙 derive.held-hold — 기브아 수금 hug를 넓힘) — ① 사전 held 항목은 모두 look.hold{mode, grounds(근거 단계)},
    hug는 en·item·noun까지 · ② 장면 figures[].prop이 hug 항목에 묶였는데 파생 문구에 hold.en이 없으면 걸림 — 그림 기본값은 손에 매단 꼴(m16e).
    add 항목(수금 — edit.held-prop-add)은 바탕에서 빼고 편집 지시(gen_local_edit.held_prompt hug)가 hold 문구를 쓰므로 ②에서 뺀다."""
    L, out = _lexicon(), []
    for w in L.values():
        if not w.get("held"):
            continue
        h = w.get("look", {}).get("hold") or {}
        if h.get("mode") not in HOLD_MODES or not str(h.get("grounds", "")).startswith(COUNT_WHY):
            out.append(f"사전 {w['id']}: look.hold(mode {'·'.join(HOLD_MODES)} · grounds 근거 단계) 없음")
        elif h["mode"] == "hug" and not all(h.get(k) for k in ("en", "item", "noun")):
            out.append(f"사전 {w['id']}: hug인데 look.hold en·item·noun 없음")
    held, prompt = {x: w for w in L.values() for x in w.get("held", [])}, None
    for f in spec.get("figures", []):
        w = held.get(f.get("prop"))
        h = (w or {}).get("look", {}).get("hold") or {}
        if h.get("mode") != "hug" or h.get("add") or not h.get("en"):
            continue
        prompt = ds.route_prompt(spec) if prompt is None else prompt
        if h["en"] not in prompt:
            out.append(f"{f['region']}: 손 지물 「{f['prop']}」(사전 {w['id']} hug)인데 파생 문구에 쥔 꼴 「{h['en']}」 없음 — 손에 매단 꼴로 그려진다")
    return out


def flight_errors(spec):
    """나는 물체의 자리는 명세 칸으로(task 405, 규칙 generate.flight-position — 사람 m1e 「창은 3분의2쯤 날아가게」를 일반화) —
    guide에 허공 물체 꼴과 던지는 뼈대(throw_follow)·피하는 뼈대가 있으면 guide.flight{object, word, from, to, at}가 있어야 하고:
    촉(구역 왼끝, make_guide.spear 관례)이 from 손목 → to 머리의 at 지점 ± 0.03, 그려질 뒤끝(촉 + 사전 size.ratio × from 키 ÷ from 키 등급)이 손목 − 0.07 앞.
    (m4 실측: 그림은 구역 길이와 상관없이 지물을 제 크기로 그림 — 길이는 사전 크기로 셈)."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    sh, pose = g.get("shape", {}), g.get("pose", {})
    objs = [k for k, v in sh.items() if v in AIR_SHAPES]
    thrower = [k for k, n in pose.items() if n == "throw_follow"]
    if not objs:
        return []
    if not thrower:   # task 413: 꼴만 있는 허공 물체(던지는 뼈대 없음)는 빈 통과였음 → 날아간 자리를 셀 수 없어 실패
        return [f"{', '.join(objs)}: 허공 물체 꼴이 있는데 던지는 뼈대(throw_follow)가 없다 — 누가 던졌는지·날아간 자리를 셀 수 없다"]
    fl = g.get("flight")
    if not fl:
        return ["guide.flight(나는 물체 자리 — 누구에게서 누구에게 몇 분의 몇) 칸 없음"]
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import make_guide as M

    def pt(k, idx):
        a0, b0, a1, b1 = R[k]
        pts, _ = M.pose_points((a0 * M.W, b0 * M.H, a1 * M.W, b1 * M.H), pose[k])
        xs = [pts[i][0] / M.W for i in idx if i in pts]
        return sum(xs) / len(xs)
    hand, head = pt(fl["from"], (4,)), pt(fl["to"], (0, 14, 16))
    want = hand + fl["at"] * (head - hand)
    x0, _, x1, _ = R[fl["object"]]
    size = _lexicon().get(fl.get("word"), {}).get("look", {}).get("size")
    out = []
    if not size:
        return [f"guide.flight.word {fl.get('word')} — 사전 look.size 없음(그릴 길이를 못 셈)"]
    held = set(_lexicon().get(fl.get("word"), {}).get("held", []))   # task 399 회고: 던진 지물을 던지는 사람 prop으로 두면 손에 남은 꼴(판정자도 속음)
    fp = next((f.get("prop") for f in spec.get("figures", []) if f.get("region") == fl["from"]), None)
    if fp in held:
        out.append(f"{fl['from']} prop 「{fp}」가 날아가는 {fl['object']} — 던진 지물은 던진 사람 손 지물이 아니다(prop none)")
    if abs(x0 - want) > FLIGHT_TOL:
        out.append(f"{fl['object']} 촉 x {x0:.3f} ≠ {fl['at']:.2f} 지점 {want:.3f}±{FLIGHT_TOL} — 명세 자리(guide.flight)가 아니다")
    tb = R[fl["from"]]
    hr = dict(S.standing(spec)).get(fl["from"], 1.0)   # task 411: 사전 비는 어른 남자 키 비 — 큰 사람(사울 tall)은 구역 키 ÷ 키 등급(합성 paste_step과 같은 셈)
    butt = x0 + max(x1 - x0, size["ratio"] * S.ref(size["ref"]) * (tb[3] - tb[1]) * M.H / M.W / hr)
    if butt > hand - HAND_GAP:
        out.append(f"{fl['object']} 그려질 뒤끝 x {butt:.3f}(사전 크기 {size['ratio']} × 던지는 사람 키)가 던진 손목 {hand:.3f}에 닿음 — 손에 남은 꼴")
    return out


def flight_height_errors(spec):
    """나는 물체 높이는 던진 팔 높이(task 412, 규칙 generate.flight-height — 사람 m16e 「창 높이가 조금 올라가야 하지 않을까? 던질 때 팔의 높이」) —
    guide.flight의 from이 뼈대 인물이면 물체 구역 세로 가운데 = 그 뼈대 어깨(점 2·5 평균) ± FLIGHT_TOL. m16e: 창 0.49는 던진 손목(마무리 꼴 0.579)과
    어깨(0.443) 사이 — 놓는 순간의 팔 높이보다 낮게 날아감."""
    g, R = spec.get("guide") or {}, spec.get("regions", {})
    fl, pose = g.get("flight"), g.get("pose", {})
    if not fl or fl.get("from") not in pose:
        return []
    sys.path.insert(0, os.path.join(HERE, "batch"))
    import make_guide as M
    a0, b0, a1, b1 = R[fl["from"]]
    pts, _ = M.pose_points((a0 * M.W, b0 * M.H, a1 * M.W, b1 * M.H), pose[fl["from"]])
    ys = [pts[i][1] / M.H for i in (2, 5) if i in pts]
    if not ys:
        return [f"{fl['from']} 뼈대에 어깨 점이 없음 — 던진 팔 높이를 못 잼"]
    sy, (_, oy0, _, oy1) = sum(ys) / len(ys), R[fl["object"]]
    mid = (oy0 + oy1) / 2
    return [f"{fl['object']} 세로 가운데 {mid:.3f} ≠ {fl['from']} 어깨 {sy:.3f}±{FLIGHT_TOL} — 던진 팔 높이로 날지 않음"] if abs(mid - sy) > FLIGHT_TOL else []


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
    "recheck.guide_legs_errors": lambda spec, ctx: guide_legs_errors(spec),
    "recheck.youth_noun_errors": lambda spec, ctx: youth_noun_errors(spec),
    "recheck.pose_skeleton_errors": lambda spec, ctx: pose_skeleton_errors(spec),
    "recheck.empty_hand_fist_errors": lambda spec, ctx: empty_hand_fist_errors(spec),
    "recheck.wall_material_errors": lambda spec, ctx: wall_material_errors(spec),
    "recheck.inflating_build_errors": lambda spec, ctx: inflating_build_errors(spec),
    "recheck.figure_scale_errors": lambda spec, ctx: figure_scale_errors(spec),
    "recheck.second_point_errors": lambda spec, ctx: second_point_errors(spec),
    "recheck.youth_height_errors": lambda spec, ctx: youth_height_errors(spec),
    "recheck.height_ratio_errors": lambda spec, ctx: height_ratio_errors(spec),
    "recheck.pose_hold_errors": lambda spec, ctx: pose_hold_errors(spec),
    "recheck.pose_only_errors": lambda spec, ctx: pose_only_errors(spec),
    "recheck.split_control_errors": lambda spec, ctx: split_control_errors(spec),
    "recheck.prop_size_errors": lambda spec, ctx: prop_size_errors(spec),
    "recheck.prop_size_coverage_errors": lambda spec, ctx: prop_size_coverage_errors(spec),
    "recheck.held_hold_errors": lambda spec, ctx: held_hold_errors(spec),
    "recheck.flight_errors": lambda spec, ctx: flight_errors(spec),
    "recheck.flight_height_errors": lambda spec, ctx: flight_height_errors(spec),
    "recheck.crowd_count_errors": lambda spec, ctx: crowd_count_errors(spec),
    "recheck.perspective_errors": lambda spec, ctx: perspective_errors(spec),
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
        if not m:   # task 412: 기브아 다시 그리기 — 바탕은 gibeah-step23 시도 그림(steps[0].src 「m15/s7.png」), 합성·넣기 편집
            b = re.match(r"(\w+)/s(\d+)\.png$", f["steps"][0].get("src", ""))
            if not b:
                raise SystemExit(f"[Recheck] {sid} 국소 편집 승인의 바탕을 모름: {f['steps'][0]}")
            mb = json.load(open(os.path.join(HERE, "samples", "gibeah-step23", b.group(1), "metrics.json"), encoding="utf-8"))
            return {"image": os.path.join(HERE, f["image"]), "prompt": mb.get("prompt"), "boxes": None,
                    "from": f"gibeah-step23 {b.group(1)} s{b.group(2)} + 국소 편집",
                    "why_boxes": f"gibeah-step23 {b.group(1)} 기록에 몸 크롭 상자가 없다 — OWLv2 상자는 GPU 단계라 이번 범위 밖"}
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
