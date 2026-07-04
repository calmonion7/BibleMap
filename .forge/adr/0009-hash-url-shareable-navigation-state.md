# 공유·북마크용 해시 기반 URL로 핵심 내비게이션 상태를 미러한다

기존 `App.jsx`는 라우팅 라이브러리 없이 `activeStage`/`exploreView`/`explorePersonId` 상태 머신으로만 화면을 전환해, "아브라함 여정"·특정 화면을 **URL로 북마크·공유할 수 없었다**(새로고침 시 항상 허브로). 모바일 묵상·공유 앱에서 실질적 공백.

**결정:** **해시 기반 URL**(`#/person/<slug>`·`#/person/<slug>/timeline`·`#/books`·`#/`=허브)로 핵심 내비게이션 상태(`activeStage` + 큐레이션 인물 slug + `exploreView`)를 미러한다. **라우팅 라이브러리를 도입하지 않고**(History API `replaceState` + `location.hash`만), 상태 변경 시 `replaceState`로 URL을 갱신하고 로드 시 해시를 파싱해 상태를 복원한다. 인물은 `/persons/curated`가 주는 slug↔id로 표현한다(explore 대상은 항상 큐레이션 인물).

## Considered Options
- **경로 기반**(`/person/abraham`): nginx가 이미 SPA fallback(`try_files $uri /index.html`)이라 가능하나, base-path·자산 경로·dev/prod 차이 처리가 필요해 해시보다 취약. 값 대비 비용 큼.
- **라우터 라이브러리**(react-router 등): 34개 파일·소수 의존성 원칙(YAGNI)에 어긋나는 신규 의존성. 상태가 단순해 불필요.
- **완전 히스토리 통합**(pushState + popstate + `useNodeSelection` 내부 히스토리 흡수): 매끄러운 뒤로가기를 주나 이중 히스토리 리팩터로 리스크 큼 → 이번 범위에서 제외(후속 후보).

## Consequences
- **공유된 해시 링크는 공개 계약**이다 — slug·경로 스킴을 바꾸면 이미 배포된 링크가 깨진다. 스킴 변경은 신중히.
- `selectedNode`(상세 시트)·`verseLang`은 URL에 **인코딩하지 않는다**(transient/취향) — 공유는 인물 여정·개요·뷰 단위까지.
- 브라우저 뒤로가기는 앱 내 이동에 관여하지 않는다(`replaceState`만) — 오늘 동작과 동일, 회귀 없음. 뒤로가기 UX가 필요하면 별도 작업.
- 로드 시 복원은 `/persons/curated`(slug↔id) 이후에만 가능하므로 그 로드에 의존한다.
