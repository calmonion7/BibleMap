# 2026-06-16 — 리팩토링 3/4: 번들 코드 스플리팅 (단일 1.25MB 청크 분할)

## Plan vs actual
- What went as planned:
  - `frontend/vite.config.js`에 `manualChunks` 추가 → 단일 `index.js` 1,253.72kB가 `app(index) 33.44kB · vendor 191.86kB · maplibre 1,027.60kB`로 분리. 메인 앱 청크 약 37배 축소.
  - :8080(nginx가 `frontend/dist` 볼륨 마운트) 프로덕션 UAT 통과 — JS 청크 4개 모두 HTTP 200, 실패 요청 0, 콘솔 에러 0, 지도 렌더 정상. 동작 불변.
- Divergences:
  - **knob 형식**: 계획은 "object형 `manualChunks` 또는 `rolldownOptions`"를 후보로 두고 빌드로 확정하라 했음. 실제로는 **object형이 rolldown에서 거부됨**(`Invalid type: Expected Function but received Object` → `TypeError: manualChunks is not a function`). **함수형 `manualChunks(id)`만 동작**. `rolldownOptions`는 불필요, `rollupOptions.output.manualChunks` 함수형으로 충분.
  - **DoD의 ">500kB 경고 해소(가능하면)" 미달**: maplibre-gl 단독이 1,027kB라 분할만으로는 경고가 maplibre 청크 한 곳에 그대로 남음. 의도적으로 미해결(아래 결정 참조).

## Learnings
- Do differently next time:
  - **vite8/rolldown에서 `manualChunks`는 반드시 함수형으로 작성**한다. 과거 rollup 습관(object 맵 `{name: [pkgs]}`)은 빌드 에러. `id => id.includes('node_modules') ? ...` 패턴 사용. (다음 vite config 작업 시 바로 적용)
  - **maplibre-gl은 단일 >500kB 청크로 두는 것이 의도된 상태.** 경고를 없애려고 동적 import로 lazy-load하지 말 것 — BibleMap은 지도가 초기 화면 본체라 lazy-load 이득이 없고 로딩 동작만 바뀜("동작 불변" 위반). 내부 마이크로 분할도 non-goal. 따라서 빌드 시 maplibre 청크의 >500kB 경고는 정상이며, 진짜 회귀(앱/vendor 청크가 다시 비대해짐)와 구분해서 볼 것.
  - 분할로 얻은 실익은 총 바이트 감소가 아니라 **캐싱 입도 개선**(앱/vendor 변경이 1MB maplibre 청크 캐시를 무효화하지 않음). 재배포 빈번한 앱 코드와 안정적인 지도 라이브러리를 분리한 게 핵심.

## Doc updates
- CONTEXT.md promotion: none (빌드 툴링 사실로 도메인 용어 아님 — 글로사리 오염 방지)
- ADR added: none. 두 학습 모두 ADR 3요건(되돌리기 어려움 + 맥락 없이 난해 + 진짜 트레이드오프)을 모두 충족하진 않음 — knob은 툴 사실, "maplibre 단일 청크 유지"는 쉽게 되돌릴 수 있는 경량 결정. 둘 다 retro 로그에 남겨 다음 vite 작업의 fg-ask/fg-run이 읽도록 함.
