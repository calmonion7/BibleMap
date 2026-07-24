# 2026-07-24 — Person 연대 위반 5건 교정 (task#252) [일괄 승급]

## Plan vs actual
- validate_event_chronology 5위반 → 0. events.json(Terah 3·Isaac 1) + persons.json(Samson·유다왕 Ahaziah·Jehoram). 세부는 `.forge/done/260724-103428-person-chronology-corrections/run.md`.

## Learnings
- Do differently next time:
  - **오래된 ADR의 전제는 코드 grep으로 재확인.** ADR-0014는 "Person birthYear/deathYear는 미사용·UI 미노출이라 교정 안 함"이라 했으나, 이후 추가된 `PersonIntro.jsx`(formatLifespan)·`PersonMiniCard.jsx`가 실제로 표시 → death<birth가 사용자에게 노출되는 실버그였다. ADR은 작성 시점 스냅샷 — 데이터/코드 교정 착수 전 "그 전제가 아직 사실인가"를 grep으로 검증.
  - **inject stale-intermediate footgun**: date_correction의 `newStartDate`만 바꾸면, DB가 이전 교정 결과(중간값)를 들고 있을 때 inject가 echo 불일치(oldStartDate≠DB, newStartDate≠DB)로 **무음 스킵**한다. `oldStartDate`는 theographic 원본 유지(재적재 안전)하되 현재 DB 중간값은 1회 직접 SET로 조정.
  - **오프셋 커버리지 점검**: 족장 +170 오프셋이 Abraham/Isaac/Jacob/Joseph만 적용되고 **Terah 누락** → 아비(데라)가 아들(아브라함)보다 늦게. 오프셋 교정 땐 그 시대 전체 이벤트(부모/조상 포함) 커버를 함께 확인.
  - **동명이인은 부모 관계로 식별**: 왕 Ahaziah(유다 rec83=Athaliah·Jehoram 子 / 이스라엘 rechG=Ahab·Jezebel 子)·Jehoram(유다=Jehoshaphat 子)을 CHILD_OF로 구분. inject_persons는 theographic_id 매칭이라 name 매칭 위험 없음.
  - **정렬 UI는 sortKey가 지배** — startDate와 sortKey를 함께 이동(정수부만 시프트해 분수 순서 보존).

## Doc updates
- ADR: **260724-111632** 신설 — Person 연도도 교정 대상으로 편입(ADR-0014 Person 조항 부분 개정, UI 노출 근거). ADR-0014에 back-pointer 추가.
- CONTEXT.md: 「사건 연대」는 기존 절이 이미 커버 — 신규 승급 없음(inject footgun은 구현 세부, 회고에 보존).
