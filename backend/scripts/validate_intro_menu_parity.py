"""인트로↔실제 하위 메뉴 정합 검증 (task#277 S3).

사이트 인트로의 컨텐츠 소개 장면은 "앱의 실제 하위 메뉴를 그대로 보여준다"가 원칙인데(회고
260724-004042), 앱에 탭이 늘어도 인트로는 조용히 낡는다. 실제로 task#245 이후 성경책 부의
탭 4종이 누락된 채 남아 있었다. 아무도 대조하지 않는 소개 문구는 썩는다(ADR 260820-003946).

대조 대상(앱을 실행하지 않고 소스에서 정적으로 추출 — 게이트는 판정자이지 작성자가 아니다):
  - frontend/src/IntroView.jsx    : const SCENES = [{nav, tabs: [[Icon, '라벨']]}]
  - frontend/src/App.jsx          : activeStage 'overview'·'book'의 <StageNav.Tab icon= label=>
  - frontend/src/ExploreStage.jsx : INTRO_TAB·EXPLORE_TABS·RELATIONS_TAB·RELIANCE_TAB·
                                    FAMILY_TAB·TOUR_INTRO_TAB의 {icon, label}

부별로 (아이콘, 라벨) 쌍 집합을 양방향 대조한다 — 실제에 있고 인트로에 없으면 누락, 인트로에
있고 실제에 없으면 유령. 라벨만이 아니라 아이콘도 보는 이유: "라벨은 같은데 아이콘이 다른"
드리프트도 인트로 원칙(앱과 동일한 lucide 컴포넌트) 위반이다.

--selftest는 인메모리 사본에 고의 드리프트를 주입해 이 검사가 실제로 FAIL하는지 확인한다.
기준선에서 통과하는 게이트는 PASS만으로 아무것도 증명하지 못하고, 주입 대상을 하나로 고정하면
검사가 그 항목에 우연히 묶였는지 가릴 수 없다(회고 260820-003946) — 그래서 전 탭을 순회한다.
"""
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 부 소개 목록에서 제외하는 실제 탭 — 제외 근거를 코드에 남긴다.
#   («책 정보», BookOpen): 책 상세 스테이지의 "현재 위치" 탭이다. 부의 하위 메뉴가 아니라
#   이미 소개된 「책 둘러보기」로 들어간 뒤의 자기 자신이라 소개 목록에 넣으면 중복이 된다.
_EXCLUDED = {("BookOpen", "책 정보")}

# 탭이 아니어서 대조 대상이 아닌 인트로 장면 — 어느 부에도 속하지 않는 전역 기능(task#277 D2).
#   상단 하위 메뉴가 아니라 검색 버튼·북마크 토글·읽기 진도라 대응하는 StageNav.Tab이 없다.
#   («읽기 진도»는 앱 UI가 ✓ 글리프여서 대응 lucide 컴포넌트조차 없다.)
_NOT_A_SECTION = {"어디서나"}


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _scene_region(src, nav):
    """SCENES 안에서 nav 장면 하나의 본문 구간 (주입 대상을 장면별로 좁히기 위해)."""
    i = src.index("nav: '%s'" % nav)
    j = src.index("\n  },", i)
    return i, j


def _intro_sections(src):
    """인트로 SCENES → {nav: [(icon, label)]}. 전역 기능 장면은 제외."""
    block = re.search(r"const SCENES = \[(.*?)\n\]", src, re.S)
    assert block, "IntroView.jsx의 SCENES 배열 파싱 실패"
    out = {}
    for m in re.finditer(r"nav: '([^']+)',.*?tabs: \[(.*?)\],\n", block.group(1), re.S):
        nav = m.group(1)
        if nav in _NOT_A_SECTION:
            continue
        out[nav] = [(i, l) for i, l in re.findall(r"\[(\w+), '([^']+)'\]", m.group(2))]
    assert out, "IntroView.jsx에서 대조할 인트로 장면을 하나도 못 뽑았다"
    return out


def _stage_nav_tabs(src, stage):
    """App.jsx의 activeStage === '<stage>' 블록 안 <StageNav.Tab icon= label=>."""
    i = src.index("{activeStage === '%s' && (" % stage)  # 리본 부 계산에도 같은 비교가 있어 렌더 블록으로 앵커
    j = src.index("</StageNav>", i)
    return re.findall(r"<StageNav\.Tab\s+icon=\{(\w+)\}\s+label=\"([^\"]+)\"", src[i:j])


def _named_tabs(src, names):
    """ExploreStage.jsx의 이름붙은 탭 상수 → 선언 순서대로 (icon, label)."""
    out = []
    for n in names:
        i = src.index("const %s = " % n)
        j = src.find("\nconst ", i + 1)
        decl = src[i:j if j != -1 else len(src)]
        out += re.findall(r"icon:\s*(\w+),\s*label:\s*'([^']+)'", decl)
    return out


def _app_sections():
    app, explore = _read("frontend/src/App.jsx"), _read("frontend/src/ExploreStage.jsx")
    person = _named_tabs(explore, ["INTRO_TAB", "EXPLORE_TABS", "RELATIONS_TAB", "RELIANCE_TAB", "FAMILY_TAB"])
    tour = _named_tabs(explore, ["TOUR_INTRO_TAB", "EXPLORE_TABS"])
    books = _stage_nav_tabs(app, "overview") + _stage_nav_tabs(app, "book")
    out = {"인물": person, "성경책": books, "투어": tour}
    for nav, tabs in out.items():
        assert tabs, "%s 부의 실제 탭을 소스에서 하나도 못 뽑았다" % nav
    return out


def _dedupe(pairs):
    seen, out = set(), []
    for p in pairs:
        if p not in seen and p not in _EXCLUDED:
            seen.add(p)
            out.append(p)
    return out


def _errors(intro_src):
    intro, app = _intro_sections(intro_src), _app_sections()
    errs = []
    for nav in sorted(set(intro) | set(app)):
        if nav not in intro:
            errs.append("인트로에 '%s' 부 소개 장면이 없다" % nav)
            continue
        if nav not in app:
            errs.append("인트로의 '%s' 장면에 대응하는 실제 부가 없다" % nav)
            continue
        want, have = set(_dedupe(app[nav])), set(intro[nav])
        for p in sorted(want - have):
            errs.append("%s 부 누락 — 실제 탭 %s가 인트로에 없다" % (nav, p))
        for p in sorted(have - want):
            errs.append("%s 부 유령 — 인트로의 %s가 실제 탭에 없다" % (nav, p))
    return errs


def _selftest():
    """전 탭 순회 주입 — 누락·유령 양방향이 매번 FAIL해야 한다."""
    src = _read("frontend/src/IntroView.jsx")
    assert not _errors(src), "기준선이 이미 FAIL이라 대조군을 돌릴 수 없다"
    n = 0
    for nav, tabs in sorted(_intro_sections(src).items()):
        i, j = _scene_region(src, nav)
        for icon, label in tabs:  # ① 누락 — 실제 탭을 인트로에서 하나씩 지운다
            entry = "[%s, '%s']" % (icon, label)
            assert entry in src[i:j], "주입 대상 %s를 %s 장면에서 못 찾았다" % (entry, nav)
            hurt = src[:i] + src[i:j].replace(entry, "", 1) + src[j:]
            assert _errors(hurt), "누락 주입(%s %s)에도 검사가 통과했다" % (nav, entry)
            n += 1
        # ② 유령 — 실제에 없는 라벨을 인트로에 넣는다
        k = src.index("tabs: [", i)
        hurt = src[:k] + "tabs: [[BookOpen, '유령메뉴-%s'], " % nav + src[k + len("tabs: ["):]
        assert _errors(hurt), "유령 주입(%s)에도 검사가 통과했다" % nav
        n += 1
    print("대조군: 고의 드리프트 %d종(누락·유령 양방향, 전 탭 순회) 전부 FAIL 확인" % n)
    print("PASS")


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    src = _read("frontend/src/IntroView.jsx")
    intro, app = _intro_sections(src), _app_sections()
    errs = _errors(src)
    assert not errs, "인트로↔실제 하위 메뉴 드리프트:\n  " + "\n  ".join(errs)
    print("검사: %s — 인트로 장면과 실제 탭의 (아이콘, 라벨) 쌍이 부별로 양방향 일치"
          % " · ".join("%s %d탭" % (n, len(_dedupe(app[n]))) for n in intro))
    print("PASS")


if __name__ == "__main__":
    main()
