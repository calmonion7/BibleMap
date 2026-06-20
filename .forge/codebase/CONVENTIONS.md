---
last_mapped_commit: ff728ccaffbb9b4e38f1f8f32859a50d3555b515
mapped: 2026-06-20
---

# 코드 컨벤션

## 1. 들여쓰기 및 포맷

- **스페이스 2칸** 들여쓰기. 탭 없음. 프론트엔드·백엔드 공통.
- **세미콜론 없음** (프론트엔드 JS/JSX). ASI(자동 세미콜론 삽입) 의존.
- 파일 끝 개행(newline) 유지.

## 2. 따옴표 스타일

| 영역 | 스타일 |
|------|--------|
| JavaScript / JSX 문자열 | 단일 따옴표 `'` 우선 |
| JSX 속성값 | 이중 따옴표 `"` (JSX 관례) |
| Python 문자열 | 이중 따옴표 `"` 우선, f-string 포함 |
| Python docstring | 삼중 이중 따옴표 `"""` |

단일 따옴표 안에 작은따옴표가 포함될 때만 이중 따옴표로 전환.

## 3. JSX 패턴

- **인라인 스타일 100%**. Tailwind, CSS Modules, 전역 CSS 클래스 없음.
  ```jsx
  // `frontend/src/components/SidePanel.jsx` 패턴
  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
  ```
- 스타일 오브젝트가 길면 JSX 밖 변수에 추출하지 않고 멀티라인으로 펼침.
- 조건 렌더링: 삼항 연산자 우선, 짧으면 `&&` 단락 평가.
  ```jsx
  {loading ? <Spinner /> : <Content />}
  {error && <ErrorMessage />}
  ```
- JSX 반환 직전에 계산 변수를 선언해 JSX를 간결하게 유지.

## 4. 네이밍 규칙

### 프론트엔드 (JS/JSX)

| 대상 | 규칙 | 예시 |
|------|------|------|
| 컴포넌트 파일 | PascalCase | `SidePanel.jsx`, `TimelineView.jsx` |
| 컴포넌트 함수 | PascalCase | `SidePanel`, `BookCard` |
| 커스텀 훅 파일 | camelCase, `use` 접두사 | `useNodeSelection.js`, `useSearch.js` |
| 유틸·API 파일 | camelCase | `api.js`, `theme.js`, `convexHull.js` |
| 이벤트 핸들러 | `handle` 접두사 + camelCase | `handleTabClick`, `handleKeyDown` |
| 전역 상수 | ALL_CAPS | `MOBILE_QUERY`, `SHEET_VH`, `NAV_H`, `SEARCH_LIMIT` |
| 일반 변수·함수 | camelCase, 동사 시작 | `selectNode`, `clearSearch`, `fmtYear` |
| 한국어 번역 필드 | `Ko` 접미사 | `nameKo`, `verse_textKo`, `keyVerseTextKo` |
| 번역 누락 플래그 | `Missing` 접미사 boolean | `nameKoMissing` |

### 백엔드 (Python)

| 대상 | 규칙 | 예시 |
|------|------|------|
| 함수·변수 | snake_case | `get_driver`, `load_events`, `name_ko` |
| 전역 상수 | ALL_CAPS | `NEO4J_URI`, `NEO4J_USER`, `SCRIPT_DIR` |
| 파일명 | snake_case | `bible_data.py`, `enrich_place_coords.py` |

클래스 없이 **모듈 + 함수** 중심 설계. 라우터는 `APIRouter`로 분리.

## 5. 에러 처리

### 프론트엔드

- `AbortError` 명시적 구분 후 조기 반환:
  ```js
  // `frontend/src/hooks/useSearch.js` 패턴
  } catch (e) {
    if (e.name === 'AbortError') return
    setSearchResults([]); setSearchError(true)
  }
  ```
- stale 응답 방지: `let cancelled = false` 플래그 + `useEffect` cleanup에서 `cancelled = true`.
- `AbortController`로 fetch 경쟁 조건 방지.
- 에러 상태는 내용 없이 `boolean` 플래그로만 저장(`setError(true)`).
- 단순 실패는 `.catch(() => setError(true))` 인라인 처리.

### 백엔드

- 환경변수 누락 → 모듈 최상위에서 즉시 `RuntimeError` raise:
  ```python
  # ETL 스크립트 공통 패턴
  if not NEO4J_PASSWORD:
      raise RuntimeError("NEO4J_PASSWORD 환경변수가 설정되지 않았습니다")
  ```
- 리소스 미발견 → `HTTPException(status_code=404, detail=...)`.
- 데이터 파싱 실패(float 변환 등) → `except (TypeError, ValueError): continue`.
- JSON 파싱 실패 → `except json.JSONDecodeError: return {}`.
- 치명적이지 않은 초기화 에러 → `logging.exception(...)` 후 계속 진행.

## 6. 주석 정책

- **JSDoc 없음**. 인라인 한국어 단행 주석만 사용.
- 파일 최상단: 역할 1줄 설명.
  ```js
  // 공유 API 클라이언트 — 모든 프론트 fetch의 단일 베이스 URL + GET 헬퍼.
  ```
- JSX 섹션 구분: 한국어 블록 주석.
  ```jsx
  {/* 내비게이션 바 */}
  {/* 오버레이 패널 */}
  ```
- 비직관적 동작·버그 방지 이유 설명:
  ```js
  // useCallback([])으로 참조를 안정화: selectedNode 변경 시 MapView 등의
  // useEffect가 재실행되어 expandPlace fetch가 abort되는 버그 방지
  ```
- ADR 참조: `ADR-0003`, `ADR-0005` 형식으로 주석에 명시.
- Python 함수 docstring: 1–2줄 간결하게. 모듈 레벨 docstring은 목적·제약 설명.

## 7. ESLint 설정

설정 파일: `frontend/eslint.config.js` (flat config 신형)

- 기반: `eslint/js` → `js.configs.recommended`
- 플러그인: `eslint-plugin-react-hooks` (`reactHooks.configs.flat.recommended`)
- 플러그인: `eslint-plugin-react-refresh` (`reactRefresh.configs.vite`)
- 대상: `**/*.{js,jsx}` — **TypeScript 파일 없음**
- 무시: `dist/`

Prettier 설정 파일 없음. 포맷 규칙은 관례 기반으로 유지.

## 8. 모듈 시스템

- 프론트엔드: ESM(`type: "module"`), named export 우선. default export는 컴포넌트 파일에 한정.
- 백엔드: 표준 Python import. 상대 import 없이 절대 경로 import.

## 9. ETL 스크립트 패턴

- `main()` 함수 + `if __name__ == "__main__": main()` 구조.
- Neo4j 적재: `MERGE` + `SET`으로 멱등(idempotent) 실행.
- 드라이버: `@functools.lru_cache(maxsize=1)` 또는 `get_driver()` 싱글턴 패턴.
- 파일 경로: `SCRIPT_DIR = Path(__file__).parent` 기준 상대 경로로 데이터 파일 참조.
