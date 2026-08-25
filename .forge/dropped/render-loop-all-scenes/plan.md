<!-- forge-slug: render-loop-all-scenes -->
<!-- task: 301 -->
<!-- tdd: off -->
<!-- priority: medium -->
# 저작자 렌더 루프를 전 장면으로 — `render_scene.py` 하드코딩 해제 + 한 패스 일괄 렌더

## Goal / Non-goals

- **Goal**: 확장 9파트(task#288~296)가 S1에서 의존하는 **수정 → 렌더 → 육안 판단** 루프를 293장면 전부에 쓸 수 있게 만든다. 지금 `scripts/render_scene.py`는 파일럿 3장면만 `SCENES` 딕셔너리에 하드코딩하고 있어 확장 착수 시점에 **바로 막힌다**.
- **Non-goals**:
  - 장면 재작도 — 각 파트의 일이다.
  - 매체 전환(생성 래스터) — task#300이 사람 fork로 남긴 별건.
  - 정차지 딥링크(`#/tour/<slug>/<n>`) 신설 — 라우팅 계약 변경이라 이 작업 범위 밖. 딥링크가 없다는 전제 위에서 한 패스로 푼다.
  - 검증기(`validate_scene_sketch_detail.py`) 변경 — 게이트는 이미 모듈 통째 지정을 지원한다.

## Source of truth

- **장면 → 투어 정본**: `frontend/src/tourSketches.jsx`의 `TOUR_MODULES`(투어 → 모듈) + 각 모듈의 `SCENES` 기본 내보내기(정차지 키 → `{ Scene, caption }`). 파싱 방식은 `backend/scripts/validate_scene_sketch_detail.py`의 `_registry()`가 선례다 — 같은 정규식 접근을 재사용하고 새 파서를 만들지 않는다.
- **라우팅 제약**: `frontend/src/urlState.js` — 투어 해시는 `#/tour/<slug>`뿐이고 **정차지 단위 딥링크가 없다**. 그래서 N번째 정차지는 "다음 정차지"를 N번 눌러 도달할 수밖에 없고, 이것이 일괄 렌더가 필요한 이유다.
- **선행**: task#300(렌더 루프 신설) → 이 작업 → task#288~296(확장 9파트).
- **Definition of Done**: 임의의 등록 장면 이름으로 렌더가 되고, 한 모듈의 여러 장면을 **투어 1회 통과**로 촬영할 수 있으며, 파일럿 3장면 산출물이 기존과 동등하다.

## Work slices

- [ ] **S1. 레지스트리 기반 장면 해석** — `SCENES` 하드코딩 3건을 제거하고 `TOUR_MODULES` + 모듈 레지스트리에서 `장면함수 → (투어 slug, 캡션)`을 도출한다. `--list`로 해석된 전 장면을 열거한다. 완료기준: `--list`가 293장면(등록 기준)을 투어별로 열거하고, 파일럿 3장면 + 무작위 타 모듈 3장면이 이름만으로 렌더된다.
- [ ] **S2. 한 패스 일괄 렌더** — 여러 장면을 한 번의 브라우저·한 번의 투어 전진으로 촬영한다(정차지 딥링크가 없으므로 앞으로만 가며 요청 장면을 순서대로 찍는다). 완료기준: 한 모듈의 전 장면을 단일 호출로 촬영하고, 같은 장면을 개별 호출로 찍은 것과 프레임이 일치한다. (depends: S1)
- [ ] **S3. 회귀 확인** — 파일럿 3장면을 재렌더해 `.forge/reports/scene-detail-pilot/after/`의 기존 산출물과 동등함을 확인하고, `--at` 기본값 문서 문구(모든 연출 종료 후)가 `--help`에 그대로 남아 있는지 본다. 완료기준: 3장면 재렌더 동등 + `CHECK_STRICT=1 bash scripts/check.sh` 전항목 PASS. (depends: S2)
