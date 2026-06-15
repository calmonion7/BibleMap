# 2026-06-15 — 인물 성품 trait별 성경 원문 펼치기/접기 추가

## Plan vs actual
- What went as planned: S1~S4 전부 완료. 약어→bookOrder 66권 매핑, `resolveVerseRef`(범위→첫 절·다자 약어·매핑불가 처리), trait별 lazy fetch + 토글(▸/▾). :8080 실제 데이터(예수 5 trait)로 UAT 통과, 콘솔 에러 0.
- Divergences: **공용 헬퍼 `fetchVerseText`가 깨져 있던 것을 실행 중 발견·수정.** 플랜은 "기존 getbible fetch 패턴 재사용(검증됨)"을 전제하고 Book 대표구절을 non-goal로 뒀으나, 실제 호출이 세 군데 틀려 한 번도 동작하지 않았음: ①번역키 `kor`(없음, → `korean`) ②절 단위 엔드포인트 없음(→ 장 단위 `/v2/korean/{book}/{chapter}.json` fetch 후 verse find) ③응답 필드 `d.verse`(→ `verses[].text`). 공유 헬퍼라 수정했고, 부수 효과로 Book 대표구절 원문도 함께 복구됨. non-goal "위반"이 아니라 non-goal의 전제 자체가 사실이 아니었던 케이스.

## Learnings
- Do differently next time:
  - 플랜 전제가 "기존 X가 동작하니 재사용"일 때 — 특히 **외부 API** — 그릴링 단계에서 코드 존재만으로 "검증됨"이라 단정하지 말고 실제 1회 호출(curl 등)로 확인할 것. 이번 `fetchVerseText`는 코드가 있다는 이유만으로 검증됐다고 가정했고, 실제론 한 번도 성공한 적 없는 잠재 버그였음.
  - getbible v2 참조 사실(코드 주석에도 박아둠): 한국어 번역 키는 `korean`(`kor`/`bkr`/`koreankjv` 중 `korean` 사용), **절 단위 엔드포인트 없음** → 장 JSON(`/v2/korean/{bookOrder}/{chapter}.json`)을 받아 `verses[]`에서 `verse` 일치 항목의 `text`를 꺼낸다. book 번호는 canonical 1~66(theographic bookOrder == getbible book_nr).
  - 검증 경로: dev(:5173)는 API(:8000) 미노출이라 빌드 후 nginx :8080(API 동일출처 `/api`)에서 UAT. dist는 gitignore라 커밋 영향 없음.

## Doc updates
- CONTEXT.md promotion: none
- ADR added: none (버그 픽스 — 되돌리기 어려움·트레이드오프 요건 미충족)
