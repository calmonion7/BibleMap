import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: { ...globals.browser, __BUILD_ID__: 'readonly' }, // vite.config define 주입
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
  },
  {
    // 인물 정본(frontend/src/sketches/cast/*.jsx)은 별칭 선언(`export const aliases = [...]`,
    // ADR 260823-190821 1항)을 기본 컴포넌트 export와 같은 파일에 반드시 함께 둔다 — 검증기가
    // 그 소스 하나를 정적으로 읽어 별칭·좌표를 같이 뽑기 때문이다(파일 분리는 이 계약을 깬다).
    // fast refresh 대상도 아닌 정적 지오메트리 정의라 이 규칙을 여기서만 끈다.
    files: ['src/sketches/cast/**/*.jsx'],
    rules: { 'react-refresh/only-export-components': 'off' },
  },
])
