"""API 응답 캐시 수명 상한 불변식 검증 (task#285 S3 — 3차 버그 헌트 #2).

3차 헌트가 확정한 결함: `reliance.py`·`books.py`·`verses.py`의 6개 응답이
`Cache-Control: public, max-age=3600`을 ETag 없이 내려보내, 이 프로젝트의 **표준
데이터수정 경로**(`data/` 편집 + `docker compose restart api`)로 고친 내용이 재방문
브라우저에 최대 1시간 반영되지 않았다. 프론트의 캐시버스터(`api.js`의 `?v=BUILD_ID`)는
빌드타임 리터럴이라 백엔드만 재시작하는 그 경로를 원리적으로 커버하지 못한다.

**불변식은 개수가 아니라 경계다**(ADR 260821-000937). "지금 6곳"을 세는 대신
"라우트 응답의 max-age는 상한을 넘지 않는다"를 단언한다 — 그래야 내일 누가 새 라우트에
긴 캐시를 달아도 같은 결함이 다시 열리지 않는다. 알려진 위반 목록을 박아두면 새 위반은
그대로 통과한다.

상한 300초는 이 코드베이스가 이미 압도적으로 쓰던 관례다(수정 시점 분포: max-age=300 21곳
· public,max-age=3600 6곳 · no-store 1곳). `no-store`는 캐시하지 않겠다는 선언이므로 통과.

**이 게이트를 풀어야 한다면**: 조건부 GET(ETag/Last-Modified)을 붙여 데이터 변경 시
브라우저가 재문의하도록 만든 뒤 _MAX_AGE_CAP을 올려라. 상한만 올리고 검증 수단을 안 주면
헌트가 확정한 그 결함이 그대로 돌아온다.

정적 자산(nginx의 1년 immutable)은 이 검사 대상이 아니다 — 그쪽은 콘텐츠 해시가 무효화를
담당하며 `nginx/nginx.conf` 소관이다.

--selftest는 인메모리 사본에 고의 위반을 주입해 **같은 스캔 함수**가 FAIL하는지 확인한다.
기준선 PASS만으론 게이트가 살아있음을 증명하지 못한다(ADR 260820-003946). 실제 소스는
건드리지 않는다.
"""
import glob
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROUTES_GLOB = "backend/app/routes/*.py"
_MAX_AGE_CAP = 300

# Cache-Control 헤더 리터럴 안의 max-age=N. 주석은 _strip으로 먼저 걷어낸다.
_HEADER = re.compile(r'"Cache-Control"\s*:\s*"([^"]*)"')
_MAX_AGE = re.compile(r"max-age\s*=\s*(\d+)")
_COMMENT = re.compile(r"#[^\n]*")


def _strip(src):
    """주석을 공백으로 치환 — 주석 안의 예시가 위반으로 오인되지 않게(길이 보존)."""
    return _COMMENT.sub(lambda m: " " * len(m.group(0)), src)


def _violations(sources):
    """[(경로, 줄, 헤더값, max_age)] — 빈 리스트 == 불변식 성립. 검사와 대조군이 공유하는 스캔."""
    out = []
    for rel, src in sources.items():
        clean = _strip(src)
        for m in _HEADER.finditer(clean):
            value = m.group(1)
            age = _MAX_AGE.search(value)
            if not age:
                continue  # no-store 등 수명 미선언
            if int(age.group(1)) > _MAX_AGE_CAP:
                line = clean.count("\n", 0, m.start()) + 1
                out.append((rel, line, value, int(age.group(1))))
    return out


def _load():
    sources = {}
    for path in sorted(glob.glob(os.path.join(_ROOT, _ROUTES_GLOB))):
        rel = os.path.relpath(path, _ROOT)
        with open(path, encoding="utf-8") as f:
            sources[rel] = f.read()
    return sources


def _check():
    sources = _load()
    assert sources, f"라우트 소스를 하나도 못 읽었다 — 검사가 공허하다 ({_ROUTES_GLOB})"
    # 공허하지 않음: Cache-Control 선언이 실제로 존재하는지 단언(전부 사라지면 검사가 무의미).
    declared = sum(len(_HEADER.findall(_strip(s))) for s in sources.values())
    assert declared > 0, "Cache-Control 선언이 0건 — 스캔이 공허하다"
    bad = _violations(sources)
    assert not bad, "라우트 응답의 max-age가 상한을 넘는다 (3차 헌트 #2 재발):\n" + "\n".join(
        f"  {rel}:{line} — {value!r} (max-age={age} > {_MAX_AGE_CAP})" for rel, line, value, age in bad
    )
    print(f"OK — 라우트 {len(sources)}개 · Cache-Control 선언 {declared}건 · max-age 상한 {_MAX_AGE_CAP}초 초과 0건")


def _selftest():
    """고의 위반 주입에 같은 스캔이 FAIL하는지 — 인메모리 사본만 사용(소스 무변경)."""
    sources = _load()
    assert not _violations(sources), "기준선이 이미 위반 — 대조군 성립 불가"

    injected = dict(sources)
    injected["backend/app/routes/__injected__.py"] = (
        'return JSONResponse(x, headers={"Cache-Control": "public, max-age=3600"})\n'
    )
    found = _violations(injected)
    assert found, "고의 위반(max-age=3600) 주입에도 스캔이 빈 결과를 냈다"
    assert found[0][3] == 3600, f"주입 위반의 max-age를 잘못 읽었다: {found}"

    # 주석 안의 위반은 잡지 않는다(오탐 방지)도 함께 단언.
    commented = dict(sources)
    commented["backend/app/routes/__commented__.py"] = (
        '# headers={"Cache-Control": "public, max-age=3600"}  ← 주석 예시\n'
    )
    assert not _violations(commented), "주석 안의 예시를 위반으로 오인했다"

    print("OK — 대조군: 위반 주입 시 FAIL, 주석 예시는 통과(오탐 없음)")


if __name__ == "__main__":
    (_selftest if "--selftest" in sys.argv else _check)()
