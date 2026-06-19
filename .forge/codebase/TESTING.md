---
last_mapped_commit: 06b4012804c00a45ea7dfda9761d014ac91b11fb
mapped: 2026-06-20
---

# TESTING.md

## 테스트 프레임워크

**프로젝트 소유 테스트 파일이 존재하지 않는다.**

- `frontend/node_modules/` 내부에만 `*.test.*`, `*.spec.*` 파일이 존재 (maplibre-gl 등 라이브러리 자체 테스트)
- `package.json` scripts에 테스트 러너 없음 (`dev`, `build`, `lint`, `preview`만 존재)
- `requirements.txt`에 pytest, coverage, 테스트 관련 라이브러리 없음
- Jest, Vitest 설정 파일 없음
- `conftest.py` 없음

## 테스트 파일 위치

프로젝트 소스 내 테스트 파일 없음. `frontend/node_modules/` 하위에만 존재.

## Playwright 사용 패턴 (수동 검증용)

프로젝트 메모리에 기록된 패턴 — `/opt/homebrew`에 설치된 Python Playwright 사용:

- **대상**: `localhost:8080` (nginx가 서빙하는 빌드 산출물)
- **검증 전 필수 빌드**: `cd frontend && npm run build` → `frontend/dist` 갱신 후 검증
  - 백엔드도 필요 시: `docker compose up -d --build api`
- **패턴**: 네트워크 캡처 + 스크린샷 조합
  - 네트워크 캡처: API 호출 인터셉트로 응답 확인
  - 스크린샷: UI 상태 시각적 검증
- `VITE_API_URL=/api`로 빌드 — 프론트는 `:8000` 직접 접근 불가, nginx `/api` 프록시 경유만 가능

## CI 설정

`/Users/calmonion/Project/BibleMap/.github/workflows/deploy.yml` 단일 워크플로우:

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: Pull & Deploy
        run: |
          cd /Users/calmonion/Project/BibleMap
          git fetch origin
          git reset --hard origin/main
          bash deploy.sh
```

- **self-hosted 러너만** 사용 — GitHub 관리 러너 없음
- **테스트 스텝 없음, lint 스텝 없음, 빌드 검증 없음**
- main 브랜치 push 시 `git reset --hard` + `bash deploy.sh` 직접 실행
- 자동화된 품질 게이트 없음

## 목(Mock) 패턴

테스트 인프라 없으므로 mocking 패턴 없음.

## 런타임 검증 방식

자동화 테스트 대신 다음 수동 검증 패턴이 사용됨:

1. `cd frontend && npm run build` — 프론트 빌드
2. `docker compose up -d --build api` — 백엔드 재빌드 (필요 시)
3. Python Playwright로 `localhost:8080` 접근, 네트워크 캡처 + 스크린샷으로 동작 확인

## ESLint

`/Users/calmonion/Project/BibleMap/frontend/eslint.config.js` — flat config 형식:
- `eslint-plugin-react-hooks` 포함 (훅 규칙 검사)
- Prettier 설정 없음 — 포매팅은 툴링으로 강제하지 않음
- `package.json` scripts에 `lint` 항목 존재
