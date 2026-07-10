# CONTAINS_BOOK에 발생(primary) vs 회고 인용 구분을 도입

`Book-[:CONTAINS_BOOK]->Event`는 사건의 모든 성경 참조(발생 위치 + 다른 책의 회고 인용)를 구분 없이 연결한다 — 사건의 `verses`(theographic) 또는 `books`(authored person_events) 배열이 여러 책에 걸치기 때문이다. 그 결과 Book "주요 사건"(`/node/{id}` topEvents)과 Book 연대 범위(`startYear`/`endYear`)가 회고 인용 사건에 오염된다(예: 사도행전의 topEvents 1위가 스데반 설교가 인용한 BC2091 아브라함 부름; 누가복음 topEvents에 눅3장 족보가 인용한 "Birth of Seth"). **결정: CONTAINS_BOOK 관계에 `primary` 불리언을 부여한다 — 각 사건의 첫 참조(authored=`books[0]`, theographic=`verses[0]`의 책)가 발생(primary=true), 나머지는 회고 인용(primary=false).** topEvents와 range 집계는 `primary` 관계만 쓴다.

## Considered Options

- **(채택) CONTAINS_BOOK에 `primary` 불리언 태그** — 기존 관계 타입 유지, 속성만 추가. 첫 참조=발생 규약(authored books[0]·theographic verses[0])으로 결정. topEvents·range가 `WHERE r.primary` 필터. 비용: 기존 관계 1회 마이그레이션(속성 부여) + 시드 스크립트 2개(load_person_events·load_books) 수정 + nodes.py 쿼리 1곳. 관계 타입 불변이라 CONTAINS_BOOK을 쓰는 다른 소비처(있다면)는 무영향.
- **(반려) 별도 관계 타입 `OCCURS_IN_BOOK` vs `CITED_IN_BOOK`** — 더 명시적이나 스키마 변경이 크고, CONTAINS_BOOK을 쓰는 모든 쿼리를 갈라 써야 해 표면 과다. 인용/발생은 같은 "책↔사건" 관계의 속성이지 별개 관계가 아니다.
- **(반려) 런타임 휴리스틱(재시드·마이그레이션 없음)** — nodes.py에서 연도 아웃라이어를 배제하는 등. 발생 위치를 실제로 모르므로 "아브라함이 창세기 사건인데 사도행전에 인용됨"을 신뢰성 있게 구분 불가. 취약하고 오탐.

## Consequences

- **되돌리기 비용 중간**: 관계 속성이라 제거는 쉽지만, topEvents·range가 `primary`에 의존하기 시작하면 되돌릴 때 두 소비처와 마이그레이션을 함께 손봐야 한다 → ADR로 남긴다.
- **`primary` 태깅은 기존 라이브 관계 마이그레이션 1회 필요**(authored 335 + theographic 608 관계). 시드 스크립트도 수정해 향후 재시드가 `primary`를 세팅한다(CONCERNS의 "재현 자동화 부재"는 이 태스크가 해소하지 않음 — 마이그레이션+시드수정만).
- **task#151 #2(Book range) 라이브 교정을 잠금 해제한다**: primary-only 집계로 range를 재계산하면 회고 인용이 빠져 사도행전 등 범위가 정상화된다(task#151에서 #4 얽힘으로 철회했던 그 교정).
- **범위 밖(잔존)**: 발생 사건만 남겨도 topEvents가 연도 오름차순 top-10이라 책 앞부분 사건에 치우치는 "대표성 절단" 편향은 남는다(별개 curation 이슈, 후속). verse_events(단일 book_id) 사건은 애초에 인용 다중연결이 없어 무영향.
