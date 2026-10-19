#!/usr/bin/env python3
"""승인 기록기 — 사람이 고른 시도를 [[장면 명세]] 안에 적는다 (2026-09-05, task 338).

승인은 **명세 안에** 산다(ADR 260905-104910). 곁파일(`attempts/<id>.json`)은 무엇을 시도했는지의 이력이고,
「이것이 정본이다」는 명세가 진다 — 명세만 보면 무엇이 승인됐는지 알 수 있어야 하기 때문이다.

  approve.py --scene <id> --stage S4 --attempt a003 --seed 11        # 단계 승인
  approve.py --scene <id> --ladder verses                            # 사다리 ①②③ 확인(지금 해시를 적는다)
  approve.py --scene <id> --final --attempt a005 --seed 11           # [[장면 완료]]
  approve.py --scene <id> --night-pick --seed 11 --kind edit --image <그림>   # 한 장 경로 [[장면 완료]](task 368 [[장면 고르기]])
  (task 369 편집 확인 답은 batch/run_night.py record가 confirm_pick으로 적는다)

앞 단계 승인이 이 시도가 얹힌 것과 다르면 **경고만 하고 적는다** — 그 어긋남은 곧 `scene_state.stale`이
재검토로 계산해 보여 준다. 승인 시점에 막으면 사람이 순서를 되짚어 고칠 길이 막힌다.

host python3로 돈다(torch 없음). 명세는 indent 2로 되쓰므로 승인 줄만 diff에 남는다.
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params  # noqa: E402
import scene_state as ss  # noqa: E402

SCENES = os.path.join(params.CANON_DIR, "scenes")


def spec_path(scene):
    return os.path.join(SCENES, f"{scene}.json")


def load_spec(scene):
    with open(spec_path(scene), encoding="utf-8") as fh:
        return json.load(fh)


def save_spec(spec):
    with open(spec_path(spec["id"]), "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def load_side(scene):
    p = os.path.join(params.CANON_DIR, "attempts", f"{scene}.json")
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {"scene": scene, "attempts": []}


def stamp(by):
    return {"by": by, "on": datetime.date.today().isoformat()}


def night_pick(spec, seed, kind, image, by):
    """한 장 경로의 [[장면 완료]](task 368) — 밤샘 후보 중 사람이 고른 한 장. 단계 사다리 밖이라 시도 id 대신
    경로·시드·바탕/편집·그림 경로를 적는다(생성기가 명세만으로 재현 대상을 알 수 있게)."""
    if kind not in ("edit", "base"):
        raise ValueError(f"kind는 edit|base다: {kind}")
    spec.setdefault("approved", {})["final"] = {"path": "night-pick", "seed": seed, "kind": kind, "image": image, **stamp(by)}
    return spec


CONFIRM_KIND = {"편집본": "edit", "바탕": "base"}


def confirm_pick(spec, seed, answer, base, edit, by):
    """편집 확인 답(task 369 — 편집은 고른 장에만) → [[장면 완료]]. 「편집본」이면 편집 그림, 「바탕」이면 고른 바탕을 승인본으로."""
    if answer not in CONFIRM_KIND:
        raise ValueError(f"확인 답은 {sorted(CONFIRM_KIND)} 중 하나다: {answer}")
    kind = CONFIRM_KIND[answer]
    return night_pick(spec, seed, kind, edit if kind == "edit" else base, by)


def local_edit(spec, seed, image, steps, by):
    """국소 편집 경로의 [[장면 완료]](task 371) — 고른 바탕 위 klein 부위 편집 중 사람이 고른 한 장. steps = 편집 차례(부위·지시·시드)."""
    if not steps:
        raise ValueError("local-edit 완료에는 편집 차례가 하나 이상 있어야 한다")
    spec.setdefault("approved", {})["final"] = {"path": "local-edit", "seed": seed, "image": image, "steps": steps, **stamp(by)}
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--stage")
    ap.add_argument("--attempt")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--ladder", choices=ss.LADDER)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--night-pick", action="store_true")
    ap.add_argument("--kind", choices=("edit", "base"))
    ap.add_argument("--image")
    ap.add_argument("--by", default="cli")
    a = ap.parse_args()
    if sum(bool(x) for x in (a.stage, a.ladder, a.final, a.night_pick)) != 1:
        sys.exit("--stage · --ladder · --final · --night-pick 중 정확히 하나를 준다")

    spec = load_spec(a.scene)
    if a.night_pick:
        if a.seed is None or not a.kind or not a.image:
            sys.exit("--night-pick에는 --seed·--kind·--image가 필요하다")
        save_spec(night_pick(spec, a.seed, a.kind, a.image, a.by))
        print(f"장면 완료 기록(night-pick) · 시드 {a.seed} {a.kind}")
        return 0
    side = load_side(a.scene)
    spec.setdefault("approved", {})

    if a.ladder:
        h = ss.ladder_hashes(spec)[a.ladder]
        spec["approved"][a.ladder] = {"hash": h, **stamp(a.by)}
        save_spec(spec)
        print(f"사다리 {a.ladder} 확인 · 해시 {h}")
        return 0

    if not a.attempt or a.seed is None:
        sys.exit("--attempt와 --seed가 필요하다")
    by_id = {x["id"]: x for x in side["attempts"]}
    at = by_id.get(a.attempt)
    if at is None:
        sys.exit(f"시도 {a.attempt}가 곁파일에 없다")
    if str(a.seed) not in (at.get("images") or {}):
        sys.exit(f"시도 {a.attempt}에 시드 {a.seed}의 그림이 없다 (있는 시드: "
                 f"{', '.join(at.get('images') or {}) or '없음'})")

    if a.final:
        live = ss.live_stages(spec)
        last = live[-1]["id"] if live else None
        if at["stage"] != last:
            print(f"⚠ 완료가 가리키는 시도는 {at['stage']} 단계인데 마지막 단계는 {last}다", file=sys.stderr)
        spec["approved"]["final"] = {"attempt": a.attempt, "seed": a.seed, **stamp(a.by)}
        save_spec(spec)
        print(f"장면 완료 기록 · {a.attempt} 시드 {a.seed}")
        return 0

    st = next((s for s in spec["stages"] if s["id"] == a.stage), None)
    if st is None:
        sys.exit(f"단계 {a.stage}가 명세에 없다")
    if at["stage"] != a.stage:
        sys.exit(f"시도 {a.attempt}는 {at['stage']} 단계의 것이다")

    # 앞 단계 승인과 어긋나면 **경고만** — 재검토로 계산돼 화면에 뜬다.
    prev, want = None, None
    for s in ss.live_stages(spec):
        if s["id"] == a.stage:
            want = None if prev is None else ({"stage": prev["id"], **{k: prev["approved"][k]
                                                                      for k in ("attempt", "seed")}}
                                              if prev.get("approved") else None)
            break
        prev = s
    if ss._up(at.get("upstream")) != ss._up(want):
        print(f"⚠ 이 시도는 {at.get('upstream')} 위에 그려졌는데 앞 단계의 지금 승인은 {want}다 "
              f"— 적기는 하지만 재검토로 뜬다", file=sys.stderr)

    st["approved"] = {"attempt": a.attempt, "seed": a.seed, **stamp(a.by)}
    save_spec(spec)
    bad = ss.stale(spec, side)
    print(f"{a.stage} 승인 · {a.attempt} 시드 {a.seed}"
          + (f" · 재검토: {', '.join(bad)}" if bad else " · 재검토 없음"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
