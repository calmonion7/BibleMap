#!/usr/bin/env python3
"""장면 승인 상태 — 무엇이 [[재검토]]인지 계산하는 순수 함수 (2026-09-05, task 338).

명세(`scenes/<id>.json`)와 곁파일(`attempts/<id>.json`) **둘만** 읽고 판단한다. torch도 GPU도 파일 접근도 없다 —
그래서 host python3로 돌고 단위 테스트가 가능하다(`test_scene_state.py`).

사다리 셋(승인의 층위):
  ① verses      — `spec.verses` 전체
  ② description — `moment` + `background` + `figures` + `crowds`
  ③ split       — 단계의 (id, kind, region **이름**, skip, from) 순서 목록 + `regions`의 이름 집합

구역 **좌표**와 단계 문구·부정어는 사다리에 넣지 않는다. 그것은 각 단계의 입력이라 시도가 스냅샷으로 들고 있고,
바뀌면 **그 단계와 그 아래만** 재검토다.

재검토 규칙 — 승인된 단계 N이 재검토인 조건(하나라도 참):
  · 승인이 가리키는 시도의 (문구·부정어·구역 좌표)가 지금 명세와 다르다
  · 그 시도의 `upstream`이 **직전 비건너뜀 단계의 지금 승인**과 다르다(첫 단계는 `None` = 빈 종이)
  · 사다리 ①②③ 중 승인해 둔 해시가 지금 해시와 다르다
  · **앞 단계가 재검토다** — 그 캔버스 위에 그려졌으므로 함께 흔들린다(아래 「전파」)

전파: 계획의 예시 목록은 「S1 구역 좌표 수정 → S1과 아래 전부」·「S2를 새 upstream으로 재승인 → S3~ 유지」로
전파를 요구하고, 「S4 문구 수정 → S4·final만」은 전파를 금한다 — 셋이 함께 성립하지 않는다. **전파를 택했다.**
과하게 잡는 쪽이 안전하기 때문이다: 안 잡으면 승인되지 않은 캔버스 위 그림이 최신으로 보인다.

`final`은 마지막 단계의 지금 승인이 `approved.final`과 다르거나, **아래 어디든 재검토가 있으면** 재검토다.
"""
import hashlib
import json

LADDER = ("verses", "description", "split")


def _h(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def ladder_hashes(spec):
    """→ {"verses": h, "description": h, "split": h} — 지금 명세의 사다리 해시."""
    return {
        "verses": _h(spec.get("verses")),
        "description": _h([spec.get(k) for k in ("moment", "background", "figures", "crowds")]),
        "split": _h([[[s["id"], s["kind"], s["region"], bool(s.get("skip")), s.get("from")]
                      for s in spec["stages"]],
                     sorted(spec["regions"])]),
    }


def live_stages(spec):
    """건너뛰지 않는 단계만, 명세 순서대로."""
    return [s for s in spec["stages"] if not s.get("skip")]


def _up(u):
    return None if not u else (u["stage"], u["attempt"], u["seed"])


def _coords(v):
    return [round(float(x), 6) for x in (v or [])]


def stale(spec, attempts):
    """→ {단계 id | 'final' | 'verses' | 'description' | 'split': [이유, ...]} — 재검토인 것만 담는다."""
    by_id = {a["id"]: a for a in attempts.get("attempts", [])}
    now = ladder_hashes(spec)
    appr = spec.get("approved") or {}
    out = {}

    bad_ladder = [k for k in LADDER
                  if (appr.get(k) or {}).get("hash") not in (None, now[k])]
    for k in bad_ladder:
        out[k] = ["명세가 승인 시점 이후 바뀌었다"]

    live = live_stages(spec)
    below = False        # 앞 단계 중 재검토가 있었나
    prev = None          # 직전 비건너뜀 단계의 지금 승인 (stage, attempt, seed)
    for st in live:
        ap = st.get("approved")
        if ap is None:
            prev = None          # 승인이 없으면 아래 단계가 얹힐 곳도 없다
            continue
        why = ["앞 단계가 재검토라 이 단계가 선 캔버스도 재검토다"] if below else []
        a = by_id.get(ap["attempt"])
        if a is None:
            why.append(f"승인이 가리키는 시도 {ap['attempt']}가 곁파일에 없다")
        else:
            if a.get("prompt") != st.get("prompt"):
                why.append("문구가 승인 시점과 다르다")
            if list(a.get("neg") or []) != list(st.get("neg") or []):
                why.append("부정어가 승인 시점과 다르다")
            if _coords(a.get("region")) != _coords(spec["regions"][st["region"]]):
                why.append("구역 좌표가 승인 시점과 다르다")
            if _up(a.get("upstream")) != prev:
                why.append("앞 단계의 지금 승인이 이 시도가 얹힌 것과 다르다")
        why += [f"사다리 {k}가 승인 시점과 다르다" for k in bad_ladder]
        if why:
            out[st["id"]] = why
            below = True
        prev = (st["id"], ap["attempt"], ap["seed"])

    fin = appr.get("final")
    if fin:
        why = []
        last = live[-1] if live else None
        last_ap = (last or {}).get("approved")
        if not last_ap:
            why.append("마지막 단계에 승인이 없다")
        elif (fin.get("attempt"), fin.get("seed")) != (last_ap["attempt"], last_ap["seed"]):
            why.append("마지막 단계의 지금 승인이 완료 기록과 다르다")
        if any(s["id"] in out for s in live) or bad_ladder:
            why.append("아래 단계 중 재검토가 있다")
        if why:
            out["final"] = why
    return out


def board(spec, attempts):
    """→ 화면·CLI가 그대로 쓰는 단계 보드. 상태는 건너뜀 / 재검토 / 승인 / 시도 있음 / 미시도."""
    tried = attempts.get("attempts", [])
    bad = stale(spec, attempts)
    now = ladder_hashes(spec)
    appr = spec.get("approved") or {}
    rows = []
    for s in spec["stages"]:
        ap = s.get("approved")
        if s.get("skip"):
            status = "건너뜀"
        elif s["id"] in bad:
            status = "재검토"
        elif ap:
            status = "승인"
        elif any(a["stage"] == s["id"] for a in tried):
            status = "시도 있음"
        else:
            status = "미시도"
        rows.append({"id": s["id"], "kind": s["kind"], "region": s["region"], "status": status,
                     "approved": ap, "why": bad.get(s["id"], []),
                     "attempts": [a["id"] for a in tried if a["stage"] == s["id"]]})
    return {
        "scene": spec.get("id"),
        "stages": rows,
        "ladder": {k: {"hash": now[k], "approved": (appr.get(k) or {}).get("hash"),
                       "stale": k in bad} for k in LADDER},
        "final": {"approved": appr.get("final"), "stale": "final" in bad,
                  "why": bad.get("final", [])},
        "stale": bad,
    }
