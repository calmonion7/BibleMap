# 인물 관계 데이터 저작 규칙 (AUTHORING.md)

BibleMap 「인물 관계」(CONTEXT.md 102~113) 데이터를 저작하기 위한 정본 규칙이다. 다윗 24관계로 검증된 패턴을 문서화한 것으로, 이후 모든 인물 관계 저작은 이 문서를 따른다.

- **데이터 위치**: `data/person_relations/relations.json` (단일 파일, append).
- **적재 경로**(ADR-0004): relations.json은 Neo4j에 넣지 않는다. `GET /person/{node_id}/relations`가 **런타임 오버레이**로 endpoint `slug` 매칭해 반환한다.
- **생성 방식**(ADR-0006): 관계·국면은 LLM이 성경 서사에 근거해 직접 저작한다(스크립트 자동 추출 아님).
- **본문 프리베이크**(ADR-0003): 구절/문맥 본문은 손으로 쓰지 않고 빌드타임에 getbible에서 받는다(아래 규칙 1).

---

## 스키마

### relObj (관계 하나 = pair당 1개)
```jsonc
{
  "type": "가족",                 // 관계 유형 1개 (아래 유형 어휘표). 관계마다 고정.
  "note": "택한 후계",             // 선택. 주로 가족 유형의 서열·역할 짧은 라벨.
  "endpoints": [                   // 두 당사자.
    { "nameKo": "다윗", "slug": "david" },     // 큐레이션 34인이면 slug 부여
    { "nameKo": "솔로몬", "slug": "solomon" }
  ],
  "phases": [ /* phaseObj 배열, 시간순 */ ]
}
```

### phaseObj (관계의 시간에 따른 국면)
저작 시 아래 5개(+선택 context)만 쓴다. **본문 필드(`verseTextKo/En`·`contextKo/En`)는 절대 손으로 쓰지 않는다** — 프리베이크가 채운다.
```jsonc
{
  "valence": "긍정",              // 긍정 | 부정 | 중립 — 국면마다 1개
  "label": "기름 부음",           // 국면 요지, 짧은 한글
  "verse": "삼상 16:13",          // 앵커 구절 참조 (개역 약어 + "장:절")
  "approxYear": -1025,            // 대략 연도. BC는 음수. 국면 시간순 정렬 키
  "context": "삼상 16:13-14"      // 선택. 문맥 범위 "장:절-절"(같은 장). 앵커 구절 포함
}
```
프리베이크가 채우는 필드: `verseTextKo`/`verseTextEn`(앵커 본문), `context`가 있으면 `contextKo`/`contextEn`(범위 절 배열, 앵커절은 `a:true`). `context` 없으면 프론트가 `verseTextKo/En`로 폴백.

### endpoint
```jsonc
{ "nameKo": "사무엘", "slug": "samuel" }   // 큐레이션 34인 → slug
{ "nameKo": "한나" }                       // 비큐레이션 → nameKo만
```

---

## 저작 규칙 (다윗 24관계에서 검증됨)

1. **저작 vs 프리베이크 분리** — LLM은 `verse`(앵커 참조)·`context`(문맥 범위)만 쓴다. 본문(`verseTextKo/En`·`contextKo/En`)은 **손으로 쓰지 않고** `generate_verse_text.py`가 getbible(한국어 개역 + KJV)에서 받는다(ADR-0003). 참조 형식 = 개역 약어 + "장:절"(예 `삼상 16:13`), 범위는 "장:절-절"(**같은 장 안에서만**).

2. **endpoint `slug` 규칙** — 상대가 큐레이션 34인이면 그 사람의 slug를 넣어 여정 점프(`withId`)를 살린다. 아니면 `nameKo`만. slug는 백엔드 큐레이션 로스터(`backend/app/routes/persons.py` `_NAME_KO`)와 정확히 일치해야 한다.

3. **정본 pair · 중복 금지** — 관계는 **pair당 1개만** 저장한다. 두 endpoint가 모두 큐레이션이면 그 관계는 백엔드 slug 매칭으로 **양쪽 상세에 자동으로 다 뜬다**. 새 인물 저작 시 **이미 있는 pair를 다시 만들지 말 것** — 기존 것을 재사용한다(예: 사무엘 저작 시 사무엘↔사울 pair를 만들었으면, 사울 저작 때는 재생성 금지).

4. **valence는 국면마다, type은 관계마다 (직교)** — `valence`(긍정/부정/중립)는 국면마다 부여하고, `type`(유형)은 관계 하나에 1개다. 관계는 시간에 따라 valence가 변할 수 있으므로(국면 배열) 변화를 국면으로 표현한다. valence가 변하지 않으면 국면 1개로 둔다.

5. **note** — 주로 `가족` 유형의 서열·역할 짧은 라벨(맏아들 / 택한 후계 / 둘째 딸 / 시모 등). 선택. 두 endpoint가 모두 큐레이션이면 **연장자·부모 관점**으로 쓴다.

6. **국면은 시간순** — `approxYear` 오름차순(BC는 음수). `label`은 국면 요지의 짧은 한글.

7. **밀도 비례 · 공백 강요 금지**(CONTEXT 97 「공백이 곧 정확」) — 서사가 뒷받침하고, **valence를 가지며 시간에 따라 변하거나 의미 있는** 관계만 저작한다. person_events 분량이 큰 인물(예수·바울·모세·아브라함·다윗)은 깊게, 얕은 인물(셋·아벨·에녹)은 1~3개 또는 **생략**한다. 억지 관계를 만들지 않는다. 장소·집단(니느웨·블레셋 등)은 인물 관계가 아니다.

8. **검증 파이프라인**(footgun 반영) — 저작 후 반드시:
   1. `python3 backend/scripts/generate_verse_text.py` — 멱등, 본문+문맥 채움. getbible UA 우회 내장.
   2. 유형 아이콘을 새로 추가했으면 `cd frontend && npm run build` (프론트 :8080은 `dist` 마운트, HMR 아님).
   3. `docker compose restart api` — 데이터는 마운트 오버레이라 재빌드 불필요하나, 백엔드가 관계 카탈로그를 `@functools.lru_cache`로 기동 시 메모리 캐시하므로 **반드시 재시작**해 캐시를 비운다. `docker compose up -d api`는 config 무변경 시 컨테이너를 재생성하지 않아("Running") 옛 데이터를 계속 서빙한다 → 신규 관계가 안 보인다.
   4. `/api/persons/curated`에서 node_id 확보 → `/api/person/{node_id}/relations`가 국면 반환 확인.
   5. Playwright로 `localhost:8080` 렌더 확인(:8000 미노출). 콘솔/네트워크 에러 0.

---

## 유형 어휘표 (`RelationsView.jsx` `TYPE_ICON`/`TYPE_ORDER`와 일치)

| 유형 | 아이콘(lucide) | 의미 |
| --- | --- | --- |
| 가족 | Users | 혈연·혼인 가족(부모·자녀·형제·부부 등). `note`로 서열 명시 권장 |
| 연인 | Heart | 배우자·연인 관계 |
| 친구 | Handshake | 동역·우정·동맹 동료 |
| 신하 | Shield | 섬김·종속(신하·부하·종) |
| 선지자 | Scroll | 선지자↔왕/백성(예언·기름부음·책망) |
| 스승제자 | GraduationCap | 스승↔제자·후계 계승(랍비-제자, 부름→승계) |
| 군주 | Crown | 왕·통치자(대등 군주·외국 왕 포함) |
| 대적 | Swords | 적대·전쟁·배신 관계 |

- 표시 순서(`TYPE_ORDER`) = 위 표 순서. 미등록 유형은 아이콘 없이 렌더된다(신규 유형 추가 시 프론트 등록 필수).
- 유형은 **관계의 지배적 성격** 하나를 고른다. valence(긍정/부정)는 국면으로 표현하므로 대적/신하를 유형으로 못 박지 않아도 된다.

---

## 저작 절차 요약

1. 대상 인물의 person_events 를 읽고 서사 밀도를 가늠한다(규칙 7).
2. 유의미한 관계 상대를 고른다 — 이미 있는 pair는 재사용(규칙 3).
3. 각 관계에 type 1개, 국면들(valence·label·verse·approxYear, 선택 context)을 시간순으로 저작한다.
4. relations.json 에 append (유효 JSON 유지).
5. 규칙 8 검증 파이프라인 실행.
