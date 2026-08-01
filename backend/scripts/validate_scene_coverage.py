"""투어 정차지 ↔ 장면 스케치 커버리지 검증 (task#259 S1).

투어 정차지에 스케치가 없으면 해설 카드에 삽화가 조용히 빠지고, 반대로 스케치 키가
정차지와 어긋나면 그린 그림이 영원히 렌더되지 않는다. 양쪽 집합을 대조해 고정한다.

검사 대상:
  - data/tours/*.json              : stops[].id
  - frontend/src/sketches/*.jsx    : 레지스트리 키 'authored-...':
  - frontend/src/tourSketches.jsx  : 모듈 import + SCENES 스프레드 병합

세 번째 검사가 없으면 모듈을 만들고 병합에 추가하는 걸 잊었을 때 "키는 있으니 커버됨"으로
통과하면서 앱은 아무것도 렌더하지 않는 구멍이 남는다.
"""
import glob
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 스케치 미저작이 정당한 정차지(현재 없음). 비우는 것이 정본 — 새 정차지는 스케치를 함께 저작한다.
EXPECTED_UNCOVERED = set()

# 스케치 모듈이 아닌 헬퍼 — 병합 대상에서 제외.
_NOT_MODULES = {"lib", "SceneLabel"}

# 토큰이 자기식별적이라 포매팅에 둔감한 좁은 정규식.
_KEY = re.compile(r"""['"](authored-[A-Za-z0-9-]+)['"]\s*:""")


def _stop_ids():
    ids = set()
    for path in sorted(glob.glob(os.path.join(_ROOT, "data", "tours", "*.json"))):
        with open(path, encoding="utf-8") as f:
            for stop in json.load(f).get("stops", []):
                ids.add(stop["id"])
    return ids


def _sketch_keys():
    keys = set()
    for path in sorted(glob.glob(os.path.join(_ROOT, "frontend", "src", "sketches", "*.jsx"))):
        with open(path, encoding="utf-8") as f:
            keys |= set(_KEY.findall(f.read()))
    return keys


def _unmerged_modules():
    """sketches/의 모듈 중 tourSketches.jsx에서 import되지 않았거나 스프레드되지 않은 것."""
    modules = {
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(_ROOT, "frontend", "src", "sketches", "*.jsx"))
    } - _NOT_MODULES
    with open(os.path.join(_ROOT, "frontend", "src", "tourSketches.jsx"), encoding="utf-8") as f:
        src = f.read()
    imported = dict(re.findall(r"""import\s+(\w+)\s+from\s+['"]\./sketches/(\w+)['"]""", src))
    spread = set(re.findall(r"\.\.\.(\w+)", src))
    merged = {module for binding, module in imported.items() if binding in spread}
    return sorted(modules - merged)


def main():
    stops = _stop_ids()
    keys = _sketch_keys()

    uncovered = stops - keys - EXPECTED_UNCOVERED  # 스케치 없는 정차지(조용한 삽화 누락)
    orphans = keys - stops                          # 어떤 정차지에도 안 걸리는 스케치(영원히 미렌더)
    stale = EXPECTED_UNCOVERED & keys               # 이제 저작된 항목이 허용목록에 남음
    unmerged = _unmerged_modules()

    assert not uncovered, f"스케치 미저작 정차지: {sorted(uncovered)} — 스케치를 그리거나 EXPECTED_UNCOVERED 갱신"
    assert not orphans, f"정차지에 없는 스케치 키(미렌더): {sorted(orphans)} — 키 오타이거나 정차지 id 변경"
    assert not stale, f"이제 저작된 항목이 허용목록에 잔존: {sorted(stale)} — EXPECTED_UNCOVERED에서 제거"
    assert not unmerged, f"tourSketches.jsx에 병합되지 않은 모듈: {unmerged} — import + SCENES 스프레드 추가"

    print(f"검사: 정차지 {len(stops)}건 ↔ 스케치 키 {len(keys)}건, 미저작 {len(stops - keys)}건")
    print("PASS — 양방향 일치, 미병합 모듈 0")


if __name__ == "__main__":
    main()
