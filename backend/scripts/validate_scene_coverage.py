"""투어 정차지 ↔ 장면 스케치 커버리지 검증 (task#259 S1 · task#287에서 동적 구조로 갱신).

투어 정차지에 스케치가 없으면 해설 카드에 삽화가 조용히 빠지고, 반대로 스케치 키가 정차지와
어긋나면 그린 그림이 영원히 렌더되지 않는다. 양쪽 집합을 대조해 고정한다.

**task#287로 판정 기준이 바뀌었다.** 예전엔 `tourSketches.jsx`가 9모듈을 한 레지스트리로 병합해
"키가 어느 모듈에 있든" 렌더됐다. 이제는 투어 단위로 모듈을 **동적 로드**하므로, 키가 존재해도
**그 정차지가 속한 투어의 모듈 밖**에 있으면 아무것도 렌더되지 않는다 — 병합 구조에선 존재하지
않던 무음 결함 클래스다. 그래서 "커버됨 = 키가 있다"가 아니라 "그 투어의 모듈 안에 있다"로 본다.

검사 대상:
  - data/tours/*.json                          : 투어 id + stops[].id
  - frontend/src/sketches/*.jsx                : 레지스트리 키 'authored-...':
  - frontend/src/tourSketches.jsx              : TOUR_MODULES(투어 id → 동적 import) 매핑
  - frontend/src/sketches/introMontage.jsx     : 인트로 몽타주 전용 소형 레지스트리
  - frontend/src/IntroView.jsx                 : ERA_SCENES(인트로가 실제로 요구하는 5키)

판정하는 결함 클래스:
  A 미저작        정차지에 대응하는 스케치 키가 어디에도 없다
  B 고아 키       어떤 정차지에도 안 걸리는 스케치 키(영원히 미렌더)
  C 허용목록 잔존 이제 저작됐는데 EXPECTED_UNCOVERED에 남아 있다
  D 모듈 미연결   sketches/의 모듈이 TOUR_MODULES에 없다(내려받을 길이 없다)
  E 투어 미연결   data/tours/의 투어가 TOUR_MODULES에 없다(그 투어 전체가 무음)
  F 오배치        키는 있는데 그 투어의 모듈이 아닌 곳에 있다(동적 구조에서 새로 생긴 결함)
  G 인트로 미연결 ERA_SCENES 키가 introMontage 레지스트리에 없다

--selftest는 **같은 판정 함수**에 결함을 개별 주입해 A~G가 각각 빨강이 되는지 확인한다.
특히 **A(미저작)와 D/E/F(미연결)를 서로 다른 메시지로 구분**하는지 본다 — 두 결함은 증상이
같고(무음·무오류) 처방이 정반대라, 뭉뚱그리면 그림을 그려야 할 때 배선을 뒤지게 된다.
기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946).
"""
import glob
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 스케치 미저작이 정당한 정차지(현재 없음). 비우는 것이 정본 — 새 정차지는 스케치를 함께 저작한다.
EXPECTED_UNCOVERED = set()

# 스케치 모듈이 아닌 것 — 헬퍼(lib·SceneLabel)와 인트로 전용 소형 모듈(투어에 걸리지 않는다).
_NOT_MODULES = {"lib", "SceneLabel", "introMontage"}

# 토큰이 자기식별적이라 포매팅에 둔감한 좁은 정규식.
_KEY = re.compile(r"""['"](authored-[A-Za-z0-9-]+)['"]\s*:""")
_TOUR_MODULE = re.compile(r"""['"]([a-z0-9-]+)['"]\s*:\s*\(\)\s*=>\s*import\(['"]\./sketches/(\w+)['"]\)""")
_ERA_SCENES = re.compile(r"const ERA_SCENES = \[(.*?)\]", re.S)


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _scan():
    """소스 → 판정에 필요한 사실들. 검사와 대조군이 공유하는 입력."""
    tours = {}
    for path in sorted(glob.glob(os.path.join(_ROOT, "data", "tours", "*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        tours[d["id"]] = [s["id"] for s in d.get("stops", [])]

    keys_by_module = {}
    for path in sorted(glob.glob(os.path.join(_ROOT, "frontend/src/sketches/*.jsx"))):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            keys_by_module[name] = set(_KEY.findall(f.read()))

    tour_modules = dict(_TOUR_MODULE.findall(_read("frontend/src/tourSketches.jsx")))
    intro_keys = set(_KEY.findall(_read("frontend/src/sketches/introMontage.jsx")))
    m = _ERA_SCENES.search(_read("frontend/src/IntroView.jsx"))
    assert m, "IntroView.jsx에서 ERA_SCENES를 찾지 못했다"
    era_scenes = set(re.findall(r"['\"](authored-[A-Za-z0-9-]+)['\"]", m.group(1)))
    return tours, keys_by_module, tour_modules, intro_keys, era_scenes


def judge(tours, keys_by_module, tour_modules, intro_keys, era_scenes, expected_uncovered=frozenset()):
    """결함 클래스 A~G → 위반 메시지 목록. 검사와 대조군이 공유하는 유일한 판정."""
    bad = []
    stops = {sid for ids in tours.values() for sid in ids}
    all_keys = set().union(*keys_by_module.values()) if keys_by_module else set()
    modules = set(keys_by_module) - _NOT_MODULES

    uncovered = stops - all_keys - expected_uncovered
    if uncovered:
        bad.append(f"A 미저작: 스케치가 없는 정차지 {sorted(uncovered)} — 그림을 그리거나 EXPECTED_UNCOVERED 갱신")
    orphans = all_keys - stops - intro_keys
    if orphans:
        bad.append(f"B 고아 키: 어떤 정차지에도 없는 스케치 {sorted(orphans)} — 키 오타이거나 정차지 id 변경")
    stale = expected_uncovered & all_keys
    if stale:
        bad.append(f"C 허용목록 잔존: 이제 저작된 항목 {sorted(stale)} — EXPECTED_UNCOVERED에서 제거")
    unwired = sorted(modules - set(tour_modules.values()))
    if unwired:
        bad.append(f"D 모듈 미연결: TOUR_MODULES에 없는 모듈 {unwired} — tourSketches.jsx에 동적 import 항목 추가")
    tourless = sorted(set(tours) - set(tour_modules))
    if tourless:
        bad.append(f"E 투어 미연결: TOUR_MODULES에 없는 투어 {tourless} — 그 투어 전 정차지가 무음이 된다")
    misplaced = []
    for tid, ids in tours.items():
        mod = tour_modules.get(tid)
        if not mod:
            continue  # E가 이미 잡는다
        owned = keys_by_module.get(mod, set())
        misplaced += [sid for sid in ids if sid in all_keys and sid not in owned]
    if misplaced:
        bad.append(f"F 오배치: 키는 있으나 그 투어의 모듈 밖에 있는 정차지 {sorted(misplaced)} — 동적 로드는 해당 투어 모듈만 내려받는다")
    intro_missing = sorted(era_scenes - intro_keys)
    if intro_missing:
        bad.append(f"G 인트로 미연결: introMontage에 없는 ERA_SCENES 키 {intro_missing} — 인트로 몽타주가 빈 칸이 된다")
    return bad


def _check():
    tours, keys_by_module, tour_modules, intro_keys, era_scenes = _scan()
    bad = judge(tours, keys_by_module, tour_modules, intro_keys, era_scenes, EXPECTED_UNCOVERED)
    stops = {sid for ids in tours.values() for sid in ids}
    all_keys = set().union(*keys_by_module.values()) if keys_by_module else set()
    print(f"검사: 투어 {len(tours)}개 · 정차지 {len(stops)}건 ↔ 스케치 키 {len(all_keys)}건 · "
          f"TOUR_MODULES {len(tour_modules)}항목 · 인트로 {len(era_scenes)}키")
    for b in bad:
        print(f"  ✗ {b}")
    assert not bad, "커버리지 결함: " + " | ".join(x.split(":")[0] for x in bad)
    print("PASS — 미저작·고아·미연결·오배치 0")


def _selftest():
    base = _scan()
    ok = judge(*base, EXPECTED_UNCOVERED)
    assert not ok, f"대조군 기준선이 이미 빨강이다: {ok}"
    tours, kbm, tm, intro, era = base
    a_tour = sorted(tours)[0]

    def drop_key(module_of):
        """어떤 모듈에서 키 하나를 지운 사본."""
        c = {k: set(v) for k, v in kbm.items()}
        c[module_of].discard(victim)
        return c

    victim = tours[a_tour][0]
    owner = tm[a_tour]
    other = next(m for m in tm.values() if m != owner)

    cases = [
        ("A", "정차지의 키를 어디서도 지움", (drop_key(owner), tm, intro, era)),
        ("B", "정차지에 없는 고아 키 주입",
         ({**{k: set(v) for k, v in kbm.items()}, owner: kbm[owner] | {"authored-ghost-scene"}}, tm, intro, era)),
        ("D", "모듈을 TOUR_MODULES에서 제거", (kbm, {k: v for k, v in tm.items() if v != other}, intro, era)),
        ("E", "투어를 TOUR_MODULES에서 제거", (kbm, {k: v for k, v in tm.items() if k != a_tour}, intro, era)),
        ("F", "키를 다른 투어 모듈로 옮김",
         ({**{k: set(v) for k, v in kbm.items()},
           owner: kbm[owner] - {victim}, other: kbm[other] | {victim}}, tm, intro, era)),
        ("G", "ERA_SCENES 키를 introMontage에서 제거",
         (kbm, tm, {k for k in intro if k not in era} | (set(list(era)[1:])), era)),
    ]
    for code, desc, (k, t, i, e) in cases:
        bad = judge(tours, k, t, i, e, EXPECTED_UNCOVERED)
        hit = [b for b in bad if b.startswith(code)]
        assert hit, f"{code} 결함({desc})을 주입했는데 통과시켰다 — 게이트가 죽어있다. 검출된 것: {bad}"
        print(f"  ✓ {code} 주입 → {hit[0][:110]}")

    # C는 허용목록 인자로만 발동한다.
    bad = judge(tours, kbm, tm, intro, era, {victim})
    assert any(b.startswith("C") for b in bad), "C 허용목록 잔존을 못 잡는다"
    print(f"  ✓ C 주입 → {[b for b in bad if b.startswith('C')][0][:110]}")

    # 핵심 구분: 미저작(A)과 미연결(D/E)이 **서로 다른 메시지**로 나와야 한다.
    a_msg = [b for b in judge(tours, drop_key(owner), tm, intro, era, EXPECTED_UNCOVERED) if b.startswith("A")]
    d_msg = [b for b in judge(tours, kbm, {k: v for k, v in tm.items() if v != other}, intro, era, EXPECTED_UNCOVERED) if b.startswith("D")]
    assert a_msg and d_msg and a_msg[0] != d_msg[0], "미저작과 미연결이 같은 메시지로 뭉개진다"
    print("  ✓ 미저작(A)과 미연결(D)이 서로 다른 원인을 지목한다 — 처방이 정반대라 구분이 필수")
    print("PASS — 7개 결함 클래스 각각의 주입에서 검증기가 빨강이 된다")


if __name__ == "__main__":
    (_selftest if "--selftest" in sys.argv else _check)()
