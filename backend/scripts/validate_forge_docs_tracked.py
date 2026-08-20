"""영구 forge 문서(.forge/adr·.forge/retro) 미추적 0건 검증 (task#279 S4).

task#275의 ADR 1건과 회고 2건이 작성된 뒤 `git add` 없이 방치돼, 파일럿이 철회될 때까지
아무도 눈치채지 못했다(`.gitignore`는 `!.forge/adr/**`·`!.forge/retro/**`로 정상 화이트리스트
중이었으므로 규칙 결함이 아니라 `git add` 누락이다). 그 회귀를 게이트에 재현한다 —
영구 문서 루트에 미추적 파일이 하나라도 있으면 FAIL.

**배포 경로에서도 살아있는 하드 게이트다 — task#279가 계획의 반대 사실을 실측했다.**
계획은 "`deploy.sh`가 워킹트리를 하드리셋하므로 CI에서는 공허하게 통과한다"를 전제했으나 틀렸다:
`.github/workflows/deploy.yml`은 **개발 트리와 같은 디렉터리**(`/Users/calmonion/Project/BibleMap`)에서
`git reset --hard origin/main` 후 `deploy.sh`를 부르고, **하드리셋은 추적 파일만 되돌리며 미추적
파일은 지우지 않는다**(`git clean`이 아니다). 미추적 ADR·회고는 리셋을 그대로 살아 넘어와
`deploy.sh:65`의 `CHECK_STRICT=1 bash scripts/check.sh`에 노출된다.

⇒ **결과: 영구 문서가 미추적인 상태로 push하면 배포가 중단된다.** 실패는 조용하지 않고
위 assert 메시지(미추적 파일 목록 + "커밋 전 추가하라")로 뜬다. 이 강도가 맞는지 —
문서 위생 문제로 프로덕션 배포를 막을 것인지 — 는 사람이 정할 트레이드오프로 남겨 뒀다
(task#279 주행이 fork로 올림). 약화하려면 이 항목을 `CHECK_STRICT` 분기 밖으로 빼야 한다.

--selftest는 레포 안 임시 스캔 루트에 미추적 파일을 떨어뜨려 **같은 스캔 함수**가 FAIL하는지
확인한다. 기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946).
실제 adr/·retro/는 건드리지 않는다.
"""
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOTS = [".forge/adr", ".forge/retro"]
SELFTEST_ROOT = ".forge/.docs-tracked-selftest"
EXIT_NO_GIT = 3  # git 미가용 전용 — check.sh는 이 경우 skip 계약으로 넘긴다


def _git(*args):
    return subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True)


def _untracked(roots):
    """roots 아래 미추적(그리고 gitignore되지 않은) 파일 목록 — 검사와 대조군이 공유하는 스캔."""
    r = _git("ls-files", "--others", "--exclude-standard", "--", *roots)
    assert r.returncode == 0, f"git ls-files 실패: {r.stderr.strip()}"
    return [l for l in r.stdout.splitlines() if l]


def _require_git():
    if _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("git 미가용 — 작업트리가 아니거나 git이 없다. 이 검사는 로컬 전용 가드다.")
        sys.exit(EXIT_NO_GIT)


def _selftest():
    _require_git()
    d = os.path.join(_ROOT, SELFTEST_ROOT)
    try:
        os.makedirs(d, exist_ok=True)
        assert not _untracked([SELFTEST_ROOT]), "임시 스캔 루트가 비어있지 않다 — 대조군 성립 불가"
        with open(os.path.join(d, "injected.md"), "w", encoding="utf-8") as f:
            f.write("# 고의 주입 — 미추적 문서\n")
        found = _untracked([SELFTEST_ROOT])
        assert found, "미추적 파일 주입에도 스캔이 빈 결과를 냈다"
        os.remove(os.path.join(d, "injected.md"))
        assert not _untracked([SELFTEST_ROOT]), "주입 파일 제거 후에도 스캔이 검출했다"
        print(f"대조군: 임시 루트 {SELFTEST_ROOT}에 미추적 1건 주입 → 검출 {found} 확인, 제거 후 0건 복귀")
        print("PASS")
    finally:
        for f in ("injected.md",):
            p = os.path.join(d, f)
            if os.path.exists(p):
                os.remove(p)
        if os.path.isdir(d):
            os.rmdir(d)


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    _require_git()
    bad = _untracked(ROOTS)
    assert not bad, "영구 문서가 미추적 상태다(git add 누락) — 커밋 전 추가하라:\n  " + "\n  ".join(bad)
    print(f"검사: {' · '.join(ROOTS)} 미추적 0건 "
          "(배포 차단 가드 — 미추적 시 CHECK_STRICT=1 배포 경로에서 배포가 중단된다)")
    print("PASS")


if __name__ == "__main__":
    main()
