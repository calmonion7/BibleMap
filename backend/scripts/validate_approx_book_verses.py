"""generate_approx_book_verses.py의 VERSE_MAP ↔ book_events 정합 검증 (task#274 S1).

생성기가 하드코딩한 (bookId, eventId) 테이블이 데이터와 갈라지면,
생성기는 main()의 가드에서 sys.exit(1)로 죽고 아무 작업도 하지 못한다(task#273 실사례).
갈라짐은 양방향 모두 결함이므로 둘 다 위반으로 본다:
  - 죽은 키   : VERSE_MAP에 있고 book_events에 없음 → 생성기가 sys.exit(1)로 죽는다
  - 미커버 쌍 : book_events에 있고 VERSE_MAP에 없음 → ⚡ 연결에 구절이 붙지 않는다

생성기를 실행하지 않고 소스만 읽는다(ast.literal_eval — import 부작용 0).
배포 게이트가 데이터를 쓰면 "주입 → 게이트" 순서 계약이 깨지므로 읽기 전용이다
(.forge/adr/260801-195022-deploy-gate-fail-closed.md).
"""
import ast
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _verse_map_pairs():
    src = _read("backend/scripts/generate_approx_book_verses.py")
    m = re.search(r"^VERSE_MAP = \{.*?^\}", src, re.S | re.M)
    assert m, "generate_approx_book_verses.py에서 VERSE_MAP 딕셔너리 리터럴을 찾지 못함"
    table = ast.literal_eval(m.group(0).split("=", 1)[1].strip())
    return set(table.keys())


def _book_event_pairs():
    data = json.loads(_read("data/book_events/books.json"))
    return {(book_id, event_id) for book_id, events in data.items() for event_id in events}


def main():
    vm, be = _verse_map_pairs(), _book_event_pairs()
    dead = sorted(vm - be)
    uncovered = sorted(be - vm)
    lines = ([f"  죽은 키(생성기가 sys.exit(1)로 죽음): {b} / {e}" for b, e in dead]
             + [f"  미커버 쌍(구절 없는 ⚡ 연결): {b} / {e}" for b, e in uncovered])
    assert not lines, (
        f"VERSE_MAP ↔ book_events 불일치 {len(lines)}건 "
        f"(죽은 키 {len(dead)} · 미커버 {len(uncovered)}):\n" + "\n".join(lines)
    )
    print(f"검사: VERSE_MAP {len(vm)}항목 ↔ book_events {len(be)}쌍 양방향 일치 "
          f"(죽은 키 0 · 미커버 0)")
    print("PASS")


if __name__ == "__main__":
    main()
