# 2026-10-11 — ④ BibleMap 표준 배포 전환 (task#341)

## 계획 대비 실제
- 계획대로 된 것: dev 먼저 → 화면 확인 → prod 순서, 프론트·데이터를 이미지에 굽기, pre-deploy로 주입→엄격 게이트 순서 유지, dev neo4j를 prod 볼륨 복사로 시드, DoD 10개 전부 실측 통과
- 달랐던 것: api `mem_limit`(64m → 192m), neo4j 힙(256m → 192m), dev 1차 배포 실패(compose `:?` 보간)

## 배운 것
- 다음엔 이렇게:
  - **`bin/mem-report`의 「관측 최대치」는 상주(anon)만 센다.** Docker Desktop VM은 스왑이 있어서, 상한 없는 컨테이너는 상주가 작아 보여도 `memory.swap.current`에 수십 MB가 숨어 있을 수 있다(BibleMap api 상주 29 · 스왑 44 · peak 96MB). 상한값은 `/sys/fs/cgroup/memory.peak`를 직접 보고 정한다. 상한을 건 시험 스택에서 `anon + swap.current`를 재 보면 너무 좁은지가 바로 보인다
  - **표준 배포 compose에는 `${VAR:?}` 필수 보간을 두지 않는다.** `bin/deploy`는 실행 자리 `.env` 없이 러너 체크아웃에서 `compose build`를 하므로, 파일 전체 보간이 거기서 거부된다. 값 검증은 헬스(`/health`가 DB 연결까지 확인)에 맡긴다
  - **`/health`는 SPA 폴백을 의심한다.** nginx `try_files … /index.html`이면 없는 경로도 200을 돌려준다. `HEALTH_EXPECT`가 막는 거짓 통과가 바로 이것이었다
  - **neo4j JVM은 512m 컨테이너에서 힙 + 페이지캐시 + ~250MB를 쓴다.** 힙 192m · 페이지캐시 32m로도 상주 ~500MB였다
  - push를 멈춰 둔 레포를 전환할 때는 첫 배포에 무엇이 함께 나가는지(여기선 130커밋)부터 센다. 사람 결정 지점이다

## 문서 반영
- CONTEXT.md 승격: 없음 — 배포 배선은 도메인 용어가 아니다
- ADR 추가: 없음 — 결정의 무게는 infra 계약 v5와 ADR `261010-110220`에 있다. 굽기/RUNTIME_FILES 선택도 계약 v5 권고를 따랐을 뿐이다
- infra로 넘김: mem-report의 스왑 미집계, `:?` 보간과 체크아웃 빌드의 충돌(계약 4절에 한 줄 후보)
