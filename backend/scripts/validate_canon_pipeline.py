"""저작 파이프라인 [[생성 파라미터]] 정본 단일화 + `scripts/` 추적 검증 (task#316 S3).

두 축을 본다. 둘 다 **소스만 읽어** 판정한다 — `check.sh`는 GPU도 이미지 생성 venv도 없는
환경에서 돌기 때문에, 파이프라인을 실행해서 확인하는 형태는 애초에 성립하지 않는다.

  축1 — 재선언 금지. `scripts/canon/params.py`가 선언한 이름이 같은 디렉터리의 다른 `.py`에서
     **모듈 레벨로 다시 대입**되면 FAIL. 검사 목록을 손으로 유지하지 않는 것이 핵심이다 —
     목록은 ADR `260821-000937`이 금지한 형태(알려진 위반 지점의 열거)이므로, 정본을 AST로
     파싱해 키 집합을 **파생**한다. 이 파일이 생기기 전 `CN_MODEL`·`SDXL_BASE`는 각 6곳,
     `SCENE_CN`·`STEPS`·`GUIDANCE`는 각 3곳에 리터럴로 복사돼 있었다(ADR `260823-221839`).

     이름 축만으로는 **이름만 바꾼 복사본**(`_SCENE_CN = 0.8`)을 놓친다. 그래서 정본이 선언한
     문자열 상수 중 `repo/name` 형태인 것 — 즉 모델 ID — 은 **값으로도** 본다. 값 축을 모델 ID로
     한정하는 것은 의도적이다: `30`·`0.3`·`60` 같은 수치는 무관한 맥락에서 흔해 오탐이 확실하고,
     모델 ID는 길고 고유해 오탐이 0이다. 이 경계가 곧 이 불변식이 인코딩한 결함 클래스의 한계다
     — **초록은 이 불변식이 아는 재선언이 없다는 뜻이지, 드리프트가 없다는 뜻이 아니다**
     (회고 2026-08-24 §3: 게이트가 전부 초록인 채로 정보가 소실됐다).

  축2 — 미추적 금지. `scripts/` 아래 미추적 파일이 하나라도 있으면 FAIL. `check.sh`가 부르는
     `check_cast_axes.py`·`check_mask_ranges.py`가 미추적이면 새 클론·CI에서 **게이트 자신이
     깨진다**. `validate_forge_docs_tracked.py`와 같은 스캔 형태·같은 git 미가용 skip 계약이며,
     같은 이유로 강도도 같다(배포 차단).

--selftest는 두 축 **각각** 고의 위반을 임시 스캔 루트에 주입해 검출을 확인하고 원복한다.
기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR `260820-003946`). 실제 `scripts/canon/`은
건드리지 않는다.
"""
import ast
import os
import re
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANON_DIR = "scripts/canon"
PARAMS_NAME = "params.py"
UNTRACKED_ROOTS = ["scripts"]
SELFTEST_ROOT = ".forge/.canon-gate-selftest"
EXIT_NO_GIT = 3  # git 미가용 전용 — check.sh는 이 경우 skip 계약으로 넘긴다

# 허브 모델 ID 형태(`repo/name`). 정본이 이 형태로 선언한 문자열만 값 축의 대상이 된다.
_MODEL_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _git(*args):
    return subprocess.run(["git", *args], cwd=_ROOT, capture_output=True, text=True)


def _targets(node):
    """대입문 하나가 묶는 이름들. 튜플 대입(`STEPS, GUIDANCE = 30, 6.5`)을 반드시 포함한다 —
    실제로 `probe_cn.py`·`sweep_cause.py`·`gen_sweep_age_portrait.py`가 그 형태를 썼으므로,
    `Name` 타깃만 보는 검사는 그 세 파일에 통째로 눈이 먼다."""
    out = []
    tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in tgts:
        for n in ast.walk(t):
            if isinstance(n, ast.Name):
                out.append(n.id)
    return out


def _module_level_names(path):
    """모듈 레벨 대입이 묶는 이름 집합. 함수·클래스 안의 지역 이름은 보지 않는다."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names.update(_targets(node))
    return names


def _canon(params_path):
    """정본이 선언한 (이름 집합, 모델 ID 집합)을 파생한다 — 손으로 적은 목록이 아니다.
    `_`로 시작하는 이름은 그 파일의 내부 사정이라 정본 키로 보지 않는다."""
    with open(params_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=params_path)
    names, model_ids = set(), set()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        names.update(n for n in _targets(node) if not n.startswith("_"))
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, str) and _MODEL_ID.match(v.value):
            model_ids.add(v.value)
    return names, model_ids


def _canon_files(canon_dir):
    """정본을 뺀 `scripts/canon/**/*.py` 목록(절대경로)."""
    root = os.path.join(_ROOT, canon_dir) if not os.path.isabs(canon_dir) else canon_dir
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in sorted(filenames):
            if fn.endswith(".py") and fn != PARAMS_NAME:
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def _violations(canon_dir):
    """두 축 중 축1의 스캔 — 검사와 대조군이 공유한다."""
    root = os.path.join(_ROOT, canon_dir) if not os.path.isabs(canon_dir) else canon_dir
    params_path = os.path.join(root, PARAMS_NAME)
    assert os.path.exists(params_path), f"정본이 없다: {params_path}"
    names, model_ids = _canon(params_path)
    assert names, f"정본이 아무 이름도 선언하지 않았다: {params_path}"
    bad = []
    for path in _canon_files(canon_dir):
        rel = os.path.relpath(path, _ROOT)
        for n in sorted(_module_level_names(path) & names):
            bad.append(f"{rel}: 모듈 레벨 재선언 `{n}` — params.py에서만 선언하라")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for mid in sorted(model_ids):
            if mid in text:
                bad.append(f"{rel}: 모델 ID 리터럴 `{mid}` — params.py를 참조하라")
    return bad


def _untracked(roots):
    r = _git("ls-files", "--others", "--exclude-standard", "--", *roots)
    assert r.returncode == 0, f"git ls-files 실패: {r.stderr.strip()}"
    return [l for l in r.stdout.splitlines() if l]


def _require_git():
    if _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        print("git 미가용 — 작업트리가 아니거나 git이 없다. 이 검사는 로컬 전용 가드다.")
        sys.exit(EXIT_NO_GIT)


def _write(d, name, text):
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(text)


def _selftest():
    _require_git()
    d = os.path.join(_ROOT, SELFTEST_ROOT)
    try:
        os.makedirs(d, exist_ok=True)
        # --- 축1 대조군 — 정본을 흉내 낸 임시 스캔 루트에 세 형태를 각각 주입한다 ---
        _write(d, PARAMS_NAME, 'A_SCALE = 0.8\nB_MODEL = "vendor/model-1.0"\n_PRIVATE = 1\n')
        _write(d, "clean.py", "import os\nlocal_only = 1\n\n\ndef f():\n    A_SCALE = 1\n    return A_SCALE\n")
        assert not _violations(SELFTEST_ROOT), "기준선이 이미 위반을 낸다 — 대조군 성립 불가"

        _write(d, "clean.py", "A_SCALE = 0.8\n")
        assert any("A_SCALE" in v for v in _violations(SELFTEST_ROOT)), "단일 이름 재선언을 못 잡았다"

        _write(d, "clean.py", "A_SCALE, OTHER = 0.8, 1\n")
        assert any("A_SCALE" in v for v in _violations(SELFTEST_ROOT)), "튜플형 재선언을 못 잡았다"

        _write(d, "clean.py", 'X = "vendor/model-1.0"\n')
        assert any("vendor/model-1.0" in v for v in _violations(SELFTEST_ROOT)), \
            "이름을 바꾼 모델 ID 복사를 못 잡았다(값 축)"

        _write(d, "clean.py", "local_only = 1\n")
        assert not _violations(SELFTEST_ROOT), "주입 제거 후에도 위반이 남았다"
        print("대조군 축1: 단일 이름 · 튜플형 · 이름 바꾼 모델 ID 3형태 주입 → 각각 검출, 제거 후 0건 복귀")

        # --- 축2 대조군 — 같은 스캔 함수가 미추적을 잡는지 ---
        for f in (PARAMS_NAME, "clean.py"):
            os.remove(os.path.join(d, f))
        assert not _untracked([SELFTEST_ROOT]), "임시 스캔 루트가 비어있지 않다 — 대조군 성립 불가"
        _write(d, "injected.py", "# 고의 주입 — 미추적\n")
        found = _untracked([SELFTEST_ROOT])
        assert found, "미추적 파일 주입에도 스캔이 빈 결과를 냈다"
        os.remove(os.path.join(d, "injected.py"))
        assert not _untracked([SELFTEST_ROOT]), "주입 파일 제거 후에도 스캔이 검출했다"
        print(f"대조군 축2: 임시 루트에 미추적 1건 주입 → 검출 {found} 확인, 제거 후 0건 복귀")
        print("PASS")
    finally:
        if os.path.isdir(d):
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
            os.rmdir(d)


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    bad = _violations(CANON_DIR)
    assert not bad, ("[[생성 파라미터]]가 정본 밖에서 재선언됐다 — params.py 하나만 고치도록 배선하라:\n  "
                     + "\n  ".join(bad))
    _require_git()
    untracked = _untracked(UNTRACKED_ROOTS)
    assert not untracked, ("`scripts/` 아래가 미추적이다 — 새 클론·CI에서 게이트 자신이 깨진다. "
                           "커밋 전 추가하라:\n  " + "\n  ".join(untracked))
    n_files = len(_canon_files(CANON_DIR))
    n_keys, n_ids = (len(x) for x in _canon(os.path.join(_ROOT, CANON_DIR, PARAMS_NAME)))
    print(f"검사: {CANON_DIR}/{PARAMS_NAME}가 선언한 {n_keys}개 이름(모델 ID {n_ids}종 포함)이 "
          f"나머지 {n_files}개 파일에 재선언 0건 · {' · '.join(UNTRACKED_ROOTS)} 미추적 0건")
    print("PASS")


if __name__ == "__main__":
    main()
