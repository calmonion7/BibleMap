"""근거 절이 rangeLabel이 가리키는 범위를 덮는지 검증 (task#282 S3).

`generate_person_event_verses.py`는 교차-장 범위(`(Job 38:1–42:6)`)와 장 단위 범위(`(Gen 29–31)`)를
**첫 절 1개만** 베이킹했다(`fetch_verses`의 `v_end is None → [v_start]` / `v_start is None → [1]`).
결과로 화면은 "38:1–42:6"이라 적고 본문은 1절만 보여준다 — 사용자에게는 근거가 *있는데 부실한*
것처럼 보이므로 비어있음보다 나쁘다. 실측 12건. 그 결함 클래스를 게이트에 재현한다.

**불변식은 개수가 아니라 경계로 쓴다**(ADR 260821-000937):

    모든 event_verses 블록에서  베이킹된 verseID 집합 == rangeLabel 범위 ∩ verses.json 키 집합

집합 대조이므로 누락·초과·엉뚱한 절이 한 자에 걸린다. 알려진 12건을 열거하지 않으므로
새로 들어온 같은 클래스의 결함도 걸린다.

**전개는 생성기의 `expand_range_label`을 import해 재사용한다**(파서 2벌 금지 — ADR 260819-205242).
검증기가 자기 파서를 새로 선언하면 잡는 것이 "전개 버그"가 아니라 "두 파서의 차이"가 된다.
오라클도 생성기와 같다 — 정본 절 사전 `data/bible/verses.json`(ADR 260821-125000). 그래서
게이트가 통과시킨 절은 반드시 화면에 본문이 합성되는 절이고, 판정에 네트워크가 끼지 않는다.

존재 판정은 본문이 아니라 **키**다. `textKo`가 null인 절이 19개 있어 "본문 비어있지 않음"으로
판정하면 정상 데이터를 위반으로 지목한다(거짓 빨강).

--selftest는 인메모리 사본에 고의 드리프트를 주입해 이 검사가 실제로 FAIL하는지 확인한다.
기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946).
"""
import json
import os
import sys

from backend.scripts.generate_person_event_verses import expand_range_label, verse_keys_by_book

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVENT_VERSES_REL = "data/event_verses/events.json"


def _load_event_verses():
    with open(os.path.join(_ROOT, EVENT_VERSES_REL), encoding="utf-8") as f:
        return json.load(f)


def _errors(event_verses, keys_by_book):
    """위반 메시지 목록. 빈 리스트 == 불변식 성립."""
    errs = []
    blocks = 0
    for ev_id in sorted(event_verses):
        for i, block in enumerate(event_verses[ev_id].get("books", [])):
            blocks += 1
            label = block.get("rangeLabel")
            book_order = block.get("bookOrder")
            if not isinstance(book_order, int):
                errs.append(f"{ev_id}[{i}] bookOrder가 정수가 아님 — {book_order!r}")
                continue
            expected = expand_range_label(label, book_order, keys_by_book)
            if expected is None:
                errs.append(f"{ev_id}[{i}] rangeLabel 파싱 불가 — {label!r}")
                continue
            baked = {v.get("verseID") for v in block.get("verses", [])}
            if baked == expected:
                continue
            missing = sorted(expected - baked)
            extra = sorted(baked - expected)
            detail = []
            if missing:
                detail.append(f"누락 {len(missing)}건(예 {missing[:3]})")
            if extra:
                detail.append(f"초과 {len(extra)}건(예 {extra[:3]})")
            errs.append(
                f"{ev_id}[{i}] bk{book_order:02d} '{label}' — 베이킹 {len(baked)}절 "
                f"!= 범위 {len(expected)}절: " + ", ".join(detail)
            )

    # 비공허 짝(ADR 260821-000937) — 0블록을 보고 통과하는 공허한 단언을 막는다.
    if blocks == 0:
        errs.append(f"검사 대상 블록이 0개 — {EVENT_VERSES_REL}가 비었거나 구조가 바뀌었다(공허 통과 방지)")
    return errs


def _counts(event_verses):
    blocks = sum(len(ev.get("books", [])) for ev in event_verses.values())
    verses = sum(len(b.get("verses", [])) for ev in event_verses.values() for b in ev.get("books", []))
    return blocks, verses


def _selftest():
    """단언 4종 + 비공허 짝을 각각 인메모리로 주입해 FAIL하는지 순회 확인."""
    keys = verse_keys_by_book()
    base = _load_event_verses()
    assert not _errors(base, keys), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다"

    # 절이 2개 이상인 블록을 주입 대상으로 고른다(1절 블록은 삭제 주입이 빈 집합이 되어 애매하다).
    target = None
    for ev_id in sorted(base):
        for i, b in enumerate(base[ev_id].get("books", [])):
            if len(b.get("verses", [])) >= 2:
                target = (ev_id, i)
                break
        if target:
            break
    assert target, "절 2개 이상인 블록이 없어 대조군을 구성할 수 없다"
    ev_id, bi = target
    n = 0

    def _copy():
        """대상 블록만 얕게 복사한 사본 — 원본을 오염시키지 않는다."""
        ev = dict(base[ev_id])
        ev["books"] = list(ev["books"])
        ev["books"][bi] = dict(ev["books"][bi])
        ev["books"][bi]["verses"] = list(ev["books"][bi]["verses"])
        return {**base, ev_id: ev}

    # ① 절 삭제 — 범위 안 절이 빠지면 "누락"으로 걸려야 한다
    hurt = _copy()
    hurt[ev_id]["books"][bi]["verses"].pop()
    assert _errors(hurt, keys), "절 삭제 주입에도 검사가 통과했다"
    n += 1

    # ② 초과 삽입 — 범위 밖 절이 끼면 "초과"로 걸려야 한다
    hurt = _copy()
    bo = hurt[ev_id]["books"][bi]["bookOrder"]
    outside = next(k for k in sorted(keys[bo]) if k not in expand_range_label(
        hurt[ev_id]["books"][bi]["rangeLabel"], bo, keys))
    hurt[ev_id]["books"][bi]["verses"].append(
        {"verseID": outside, "chapter": int(outside[2:5]), "verse": int(outside[5:8])})
    assert _errors(hurt, keys), "범위 밖 절 삽입에도 검사가 통과했다"
    n += 1

    # ③ 라벨 변조 — 절은 그대로인데 라벨이 넓어지면 "누락"으로 걸려야 한다
    hurt = _copy()
    hurt[ev_id]["books"][bi]["rangeLabel"] = "1:1–150:1"
    assert _errors(hurt, keys), "라벨 변조 주입에도 검사가 통과했다"
    n += 1

    # ④ 라벨 파싱 불가 — 형식이 깨지면 조용히 넘기지 않고 걸려야 한다(fail-closed)
    hurt = _copy()
    hurt[ev_id]["books"][bi]["rangeLabel"] = "창세기 처음쯤"
    assert _errors(hurt, keys), "파싱 불가 라벨에도 검사가 통과했다"
    n += 1

    # ⑤ 비공허 짝 — 대상이 0블록이면 통과가 아니라 실패여야 한다
    assert _errors({}, keys), "블록 0개에도 검사가 통과했다(공허 통과)"
    n += 1

    print(f"대조군: 고의 드리프트 {n}종(절 삭제·범위 밖 삽입·라벨 변조·파싱 불가·0블록) 전부 FAIL 확인")
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    keys = verse_keys_by_book()
    event_verses = _load_event_verses()
    errs = _errors(event_verses, keys)
    assert not errs, f"근거 절이 라벨 범위를 덮지 않음 ({len(errs)}건):\n  " + "\n  ".join(errs)
    blocks, verses = _counts(event_verses)
    print(f"검사: 사건 {len(event_verses)}건의 권 블록 {blocks}개, 베이킹된 절 {verses}개 — "
          f"전부 baked verseID 집합 == rangeLabel 범위 ∩ 정본 절 사전")
    print("PASS")


if __name__ == "__main__":
    main()
