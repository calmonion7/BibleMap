# BibleMap Cypher × Apache AGE 호환성 점검 (task#340)

판정: 막힘

- 실행: 2026-10-10 10:13 · 기준 neo4j 5.26.26 · AGE 1.6.0 / PostgreSQL 16.10 (Debian 16.10-1.pgdg13+1) · 재실행 `python3 scripts/age_compat/run_check.py`
- 호출 지점 94: 그대로 통과 62 · 순서만 다름 21 · 기계적 치환 7 · 막힘 4 · 미실행 0
- 지연(판정 무관): AGE가 10배 이상 느린 엔드포인트 9/45 — 최악 `/person/{jesus}/family` 24.4s (neo4j 48ms)
- 판정 규칙: 막힘 0 · 미실행 0 → 통과 / 막힘 ≥1 → 막힘 / 막힘 0인데 미실행 ≥1 → 미판정

## 막힌 구문 목록

| 파일:줄 | 구문 | AGE 오류(또는 차이) | 재작성안 | 어디서 |
|---|---|---|---|---|
| backend/app/routes/family.py:97 | `MATCH p = (j:Person {theographic_id: $j})-[:CHILD_OF*1..100]->(a:Person) WHERE all(n IN nodes(p)[1..] WHERE n.gender = 'Male' OR n.theographic_id = $mary) RETURN DISTINCT a.theographic_id AS id` | SyntaxError: syntax error at or near "(" | 리스트 술어 `all(n IN nodes(p)[1..] WHERE c)` 미지원(리스트 컴프리헨션 안 속성 접근도 실패) → `WITH p, a UNWIND nodes(p)[1..] AS n WITH p, a, sum(CASE WHEN c THEN 0 ELSE 1 END) AS bad WHERE bad = 0` — 묶음 키에 시작 노드까지 넣으면 AGE가 메모리 6GB↑로 강제 종료(실측), 맞는 형태도 예수 기준 ~20초 (재작성 실행: 순서만 다르고 일치) | API |
| backend/app/routes/nodes.py:175 | `MATCH (n {theographic_id: $id})-[r]-(m) WITH m, labels(m) AS mlabels, CASE WHEN type(r) IN ['PARENT_OF', 'CHILD_OF'] THEN (CASE WHEN (type(r) = 'PARENT_OF') XOR (startNode(r) = n) THEN 'PARENT_OF' ELSE 'CHILD_OF' END) EL…` | InternalError_: unknown type of agtype container 0 | 노드+리스트를 담은 맵을 ~80개 넘게 collect하면 AGE 내부 오류(`unknown type of agtype container`) → 키마다 병렬 `collect(m), collect(rel), collect(mlabels)` 후 앱에서 zip (재작성 실행: 순서만 다르고 일치) | API |
| backend/app/routes/search.py:23 | `MATCH (n) WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)) AND n.theographic_id IS NOT NULL AND (n.status IS NULL OR n.status <> 'wip') WITH n, labels(n) AS labels, CASE WHEN n.nameKo = $q OR toLower(…` | 결과 불일치: 첫 차이 neo4j {"labels": ["Event"], "n": {"__node__": ["Event"], "props": {"authored": true, "context": "사울을 피해 달아난 다윗이 제사장 아히멜렉에게 진설병과 골리앗의 칼을 받음 (1Sam 21:1–9).", "nameKo": … vs AGE {"labels": ["Event"], "n": {"__node__": ["Event"], "props": {"authored":… | AGE는 agtype 문자열을 neo4j(코드포인트 사전순)와 다르게 정렬한다 → 문자열 정렬을 cypher() 밖 SQL로: `… AS (…, k agtype) ORDER BY k::text COLLATE "C" LIMIT n` (재작성 실행: neo4j와 일치) | API |
| backend/scripts/apply_event_dedupe.py:45 | `MATCH (r:Event {theographic_id: $rid}), (k:Event {theographic_id: $kid}) // 나가는 연결 이관 (자기참조 제외) CALL (r, k) { MATCH (r)-[:PART_OF]->(p) WHERE p <> k MERGE (k)-[:PART_OF]->(p) } CALL (r, k) { MATCH (r)-[:OCCURS_AT]->(pl) …` | SyntaxError: syntax error at or near "," | `CALL (r, k) { … }` 서브쿼리 미지원 → 서브쿼리마다 `MATCH (r …), (k …) MATCH … MERGE …` 독립 문장으로 쪼개 차례 실행 후 `DETACH DELETE`(한 트랜잭션으로 묶을 것). `NOT (b)-[…]->(k)` 패턴 술어는 `NOT EXISTS((b)-[…]->(k))` (재작성 실행: neo4j와 일치) | 재생:apply_event_dedupe |

## 기계적 치환

| 파일:줄 | 구문 | AGE 오류(또는 차이) | 재작성안 | 어디서 |
|---|---|---|---|---|
| backend/app/main.py:33 | `CREATE INDEX person_tid IF NOT EXISTS FOR (n:Person) ON (n.theographic_id)` | SyntaxError: syntax error at or near "person_tid" | Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g."L" USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"p"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)` (재작성 실행: neo4j와 일치) | API |
| backend/app/routes/family.py:145 | `MATCH (f:Person {theographic_id: $id}) OPTIONAL MATCH (f)-[:CHILD_OF*1..100]->(anc:Person) WITH f, collect(DISTINCT anc) AS ancs UNWIND ancs AS a MATCH (a)-[:PARENT_OF]->(child:Person) WHERE child = f OR child IN ancs RE…` | DuplicateAlias: variable 'a' already exists | UNWIND로 받은 변수를 MATCH 패턴에 다시 쓰면 DuplicateAlias — 새 변수로 받고 `WHERE id(a_u) = id(a)`로 잇는다 (재작성 실행: 순서만 다르고 일치) | API |
| backend/app/routes/nodes.py:214 | `MATCH (b:Book {theographic_id: $id})-[rel:CONTAINS_BOOK]->(e:Event) WHERE rel.primary MATCH (e)-[:HAS_PARTICIPANT]->(p:Person) WHERE p.theographic_id IS NOT NULL AND p.name <> 'God' WITH p, count(e) AS cnt ORDER BY cnt D…` | UndefinedColumn: could not find rte for cnt | 집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt` (재작성 실행: 순서만 다르고 일치) | API |
| backend/app/routes/persons.py:121 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(:Person {theographic_id: $id}) MATCH (e)-[:HAS_PARTICIPANT]->(p2:Person) WHERE p2.theographic_id <> $id AND p2.name <> 'God' RETURN p2.theographic_id AS id, count(DISTINCT e) AS share…` | UndefinedColumn: could not find rte for shared | 집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt` (재작성 실행: 순서만 다르고 일치) | API |
| backend/app/routes/stats.py:66 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(p:Person) WHERE p.theographic_id IS NOT NULL AND p.name <> 'God' WITH p, count(DISTINCT e) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN p.theographic_id AS id, p.name AS name, p.nameKo AS…` | SyntaxError: syntax error at or near "count" | 집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt` / AGE 문법에서 `count`는 예약어 — 별칭을 백틱으로: ``cnt AS `count` `` (재작성 실행: 순서만 다르고 일치) | API |
| backend/scripts/load_books.py:150 | `CREATE INDEX book_tid IF NOT EXISTS FOR (n:Book) ON (n.theographic_id)` | SyntaxError: syntax error at or near "book_tid" | Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g."L" USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"p"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)` (재작성 실행: neo4j와 일치) | 재생:load_books |
| backend/scripts/load_theographic.py:90 | `CREATE INDEX person_tid IF NOT EXISTS FOR (n:Person) ON (n.theographic_id)` | SyntaxError: syntax error at or near "person_tid" | Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g."L" USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"p"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)` (재작성 실행: neo4j와 일치) | 재생:load_theographic |

## 호출 지점 표

분류는 그 지점의 실행 중 가장 나쁜 것. 실행 수 = AGE 재생 + API(dual) 호출 수.

| 파일:줄 | 분류 | 실행 수 | 구문 | AGE 오류(또는 차이) | 재작성안 |
|---|---|---|---|---|---|
| backend/app/main.py:33 | 기계적 치환 | 5 | `CREATE INDEX person_tid IF NOT EXISTS FOR (n:Person) ON (n.theographic_id)` | SyntaxError: syntax error at or near "person_tid" | Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g."L" USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"p"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)` (재작성 실행: neo4j와 일치) |
| backend/app/routes/books.py:17 | 그대로 통과 | 1 | `MATCH (b:Book) RETURN b ORDER BY b.bookOrder ASC` |  |  |
| backend/app/routes/books.py:48 | 순서만 다름 | 1 | `MATCH (b:Book) RETURN b.theographic_id AS id, b.nameKo AS nameKo, b.chapterCount AS chapterCount` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/events.py:112 | 순서만 다름 | 1 | `MATCH (b:Book) WHERE b.theographic_id IS NOT NULL RETURN b.theographic_id AS id, b.nameKo AS nameKo, b.name AS name` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/events.py:23 | 순서만 다름 | 1 | `MATCH (b:Book) WHERE b.theographic_id IN $ids RETURN b.theographic_id AS id, b.nameKo AS nameKo, b.name AS name, b.bookOrder AS bookOrder` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/events.py:60 | 순서만 다름 | 1 | `MATCH (e:Event) WHERE e.startDate IS NOT NULL OPTIONAL MATCH (b:Book)-[:CONTAINS_BOOK]->(e) WITH e, b ORDER BY b.bookOrder ASC WITH e, colle…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/family.py:132 | 그대로 통과 | 2 | `MATCH (f:Person {theographic_id: $id}) RETURN f` |  |  |
| backend/app/routes/family.py:145 | 기계적 치환 | 2 | `MATCH (f:Person {theographic_id: $id}) OPTIONAL MATCH (f)-[:CHILD_OF*1..100]->(anc:Person) WITH f, collect(DISTINCT anc) AS ancs UNWIND ancs…` | DuplicateAlias: variable 'a' already exists | UNWIND로 받은 변수를 MATCH 패턴에 다시 쓰면 DuplicateAlias — 새 변수로 받고 `WHERE id(a_u) = id(a)`로 잇는다 (재작성 실행: 순서만 다르고 일치) |
| backend/app/routes/family.py:158 | 순서만 다름 | 2 | `MATCH (f:Person {theographic_id: $id})-[:PARENT_OF]->(c1:Person) OPTIONAL MATCH (c1)-[:PARENT_OF]->(c2:Person) RETURN f AS parent1, c1 AS ch…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/family.py:167 | 순서만 다름 | 2 | `MATCH (f:Person {theographic_id: $id})-[:PARENT_OF]->(c:Person)<-[:PARENT_OF]-(m:Person) WHERE m.theographic_id <> $id RETURN c.theographic_…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/family.py:175 | 순서만 다름 | 2 | `MATCH (f:Person {theographic_id: $id})-[:SIBLING_OF]-(s:Person) RETURN DISTINCT s` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/family.py:179 | 순서만 다름 | 2 | `MATCH (f:Person {theographic_id: $id})-[:PARTNER_OF]-(pt:Person) RETURN DISTINCT pt` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/family.py:91 | 그대로 통과 | 1 | `MATCH (j:Person {theographic_id: $j})-[:CHILD_OF]->(m:Person {gender: 'Female'}) RETURN m.theographic_id AS id` |  |  |
| backend/app/routes/family.py:97 | 막힘 | 1 | `MATCH p = (j:Person {theographic_id: $j})-[:CHILD_OF*1..100]->(a:Person) WHERE all(n IN nodes(p)[1..] WHERE n.gender = 'Male' OR n.theograph…` | SyntaxError: syntax error at or near "(" | 리스트 술어 `all(n IN nodes(p)[1..] WHERE c)` 미지원(리스트 컴프리헨션 안 속성 접근도 실패) → `WITH p, a UNWIND nodes(p)[1..] AS n WITH p, a, sum(CASE WHEN c THEN 0 ELSE 1 END) AS bad WHERE bad = 0` — 묶음 키에 시작 노드까지 넣으면 AGE가 메모리 6GB↑로 강제 종료(실측), 맞는 형태도 예수 기준 ~20초 (재작성 실행: 순서만 다르고 일치) |
| backend/app/routes/journey.py:24 | 그대로 통과 | 35 | `UNWIND $ids AS tid MATCH (p:Place {theographic_id: tid}) RETURN p.theographic_id AS id, p.longitude AS lng, p.latitude AS lat, coalesce(p.na…` |  |  |
| backend/app/routes/nodes.py:120 | 순서만 다름 | 1 | `MATCH (n {theographic_id: $id})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/nodes.py:155 | 그대로 통과 | 6 | `MATCH (n {theographic_id: $id}) RETURN n, labels(n) AS labels` |  |  |
| backend/app/routes/nodes.py:17 | 순서만 다름 | 1 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(n:Person {theographic_id: $id}) RETURN e.theographic_id AS id` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/nodes.py:175 | 막힘 | 6 | `MATCH (n {theographic_id: $id})-[r]-(m) WITH m, labels(m) AS mlabels, CASE WHEN type(r) IN ['PARENT_OF', 'CHILD_OF'] THEN (CASE WHEN (type(r…` | InternalError_: unknown type of agtype container 0 | 노드+리스트를 담은 맵을 ~80개 넘게 collect하면 AGE 내부 오류(`unknown type of agtype container`) → 키마다 병렬 `collect(m), collect(rel), collect(mlabels)` 후 앱에서 zip (재작성 실행: 순서만 다르고 일치) |
| backend/app/routes/nodes.py:214 | 기계적 치환 | 1 | `MATCH (b:Book {theographic_id: $id})-[rel:CONTAINS_BOOK]->(e:Event) WHERE rel.primary MATCH (e)-[:HAS_PARTICIPANT]->(p:Person) WHERE p.theog…` | UndefinedColumn: could not find rte for cnt | 집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt` (재작성 실행: 순서만 다르고 일치) |
| backend/app/routes/nodes.py:248 | 순서만 다름 | 1 | `MATCH (b:Book {theographic_id: $id})-[rel:CONTAINS_BOOK]->(e:Event) WHERE e.theographic_id IS NOT NULL AND rel.primary RETURN e.theographic_…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/nodes.py:28 | 그대로 통과 | 5 | `MATCH (n {theographic_id: $id}) RETURN labels(n) AS labels` |  |  |
| backend/app/routes/nodes.py:39 | 순서만 다름 | 1 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(n {theographic_id: $id}) MATCH (e)-[:OCCURS_AT]->(p:Place) WHERE p.latitude IS NOT NULL AND p.longitude…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/nodes.py:49 | 그대로 통과 | 1 | `MATCH (n {theographic_id: $id})-[:OCCURS_AT]->(p:Place) WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL RETURN p, true AS isPrimary` |  |  |
| backend/app/routes/nodes.py:58 | 순서만 다름 | 1 | `MATCH (n:PeopleGroup {theographic_id: $id})<-[:MEMBER_OF]-(person:Person) MATCH (e:Event)-[:HAS_PARTICIPANT]->(person) MATCH (e)-[:OCCURS_AT…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/nodes.py:69 | 순서만 다름 | 1 | `MATCH (n:Book {theographic_id: $id})-[rel:CONTAINS_BOOK]->(e:Event) WHERE rel.primary MATCH (e)-[:OCCURS_AT]->(p:Place) WHERE p.latitude IS …` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/nodes.py:80 | 그대로 통과 | 1 | `MATCH (p:Place {theographic_id: $id}) WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL RETURN p, true AS isPrimary` |  |  |
| backend/app/routes/persons.py:121 | 기계적 치환 | 1 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(:Person {theographic_id: $id}) MATCH (e)-[:HAS_PARTICIPANT]->(p2:Person) WHERE p2.theographic_id <> $id…` | UndefinedColumn: could not find rte for shared | 집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt` (재작성 실행: 순서만 다르고 일치) |
| backend/app/routes/search.py:23 | 막힘 | 2 | `MATCH (n) WHERE (n.nameKo CONTAINS $q OR toLower(n.name) CONTAINS toLower($q)) AND n.theographic_id IS NOT NULL AND (n.status IS NULL OR n.s…` | 결과 불일치: 첫 차이 neo4j {"labels": ["Event"], "n": {"__node__": ["Event"], "props": {"authored": true, "context": "사울을 피해 달아난 다윗이 제사장 아히멜렉에게 진설병과 골리앗의 칼을 받음 (1Sam 21:1–9).", "nameKo": … vs AGE {"labels": [… | AGE는 agtype 문자열을 neo4j(코드포인트 사전순)와 다르게 정렬한다 → 문자열 정렬을 cypher() 밖 SQL로: `… AS (…, k agtype) ORDER BY k::text COLLATE "C" LIMIT n` (재작성 실행: neo4j와 일치) |
| backend/app/routes/stats.py:45 | 그대로 통과 | 1 | `MATCH (p:Person) WITH count(p) AS persons MATCH (e:Event) WITH persons, count(e) AS events MATCH (pl:Place) WITH persons, events, count(pl) …` |  |  |
| backend/app/routes/stats.py:66 | 기계적 치환 | 1 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(p:Person) WHERE p.theographic_id IS NOT NULL AND p.name <> 'God' WITH p, count(DISTINCT e) AS cnt ORDER…` | SyntaxError: syntax error at or near "count" | 집계 별칭을 같은 절에서 ORDER BY 하지 말고 절을 하나 나눈다: `WITH p, count(e) AS cnt WITH p, cnt ORDER BY cnt` / AGE 문법에서 `count`는 예약어 — 별칭을 백틱으로: ``cnt AS `count` `` (재작성 실행: 순서만 다르고 일치) |
| backend/app/routes/stats.py:87 | 순서만 다름 | 1 | `MATCH (e:Event) WHERE e.sortKey IS NOT NULL RETURN e.sortKey AS sortKey` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/app/routes/stats.py:95 | 그대로 통과 | 1 | `MATCH (b:Book) RETURN b.theographic_id AS bookId, b.nameKo AS nameKo, b.testament AS testament, b.bookOrder AS bookOrder, b.chapterCount AS …` |  |  |
| backend/app/routes/verses.py:28 | 그대로 통과 | 1 | `MATCH (p:Person) WHERE p.theographic_id IN $ids RETURN p.theographic_id AS id, p.nameKo AS nameKo, coalesce(p.displayTitle, p.name) AS name,…` |  |  |
| backend/scripts/apply_event_dedupe.py:182 | 그대로 통과 | 1 | `MATCH (e:Event) RETURN count(e) AS n` |  |  |
| backend/scripts/apply_event_dedupe.py:186 | 그대로 통과 | 1 | `MATCH (e:Event) RETURN count(e) AS n` |  |  |
| backend/scripts/apply_event_dedupe.py:187 | 그대로 통과 | 1 | `MATCH (e:Event) WHERE e.theographic_id IN $ids RETURN count(e) AS n` |  |  |
| backend/scripts/apply_event_dedupe.py:40 | 그대로 통과 | 108 | `MATCH (r:Event {theographic_id: $rid}) RETURN count(r) AS n` |  |  |
| backend/scripts/apply_event_dedupe.py:45 | 막힘 | 81 | `MATCH (r:Event {theographic_id: $rid}), (k:Event {theographic_id: $kid}) // 나가는 연결 이관 (자기참조 제외) CALL (r, k) { MATCH (r)-[:PART_OF]->(p) WHER…` | SyntaxError: syntax error at or near "," | `CALL (r, k) { … }` 서브쿼리 미지원 → 서브쿼리마다 `MATCH (r …), (k …) MATCH … MERGE …` 독립 문장으로 쪼개 차례 실행 후 `DETACH DELETE`(한 트랜잭션으로 묶을 것). `NOT (b)-[…]->(k)` 패턴 술어는 `NOT EXISTS((b)-[…]->(k))` (재작성 실행: neo4j와 일치) |
| backend/scripts/enrich_place_coords.py:41 | 그대로 통과 | 86 | `MERGE (pl:Place {theographic_id: $id}) SET pl.name = $name, pl.title = $name, pl.nameKo = $nameKo, pl.latitude = $lat, pl.longitude = $lng, …` |  |  |
| backend/scripts/enrich_place_coords.py:63 | 그대로 통과 | 11 | `MATCH (pl:Place {theographic_id: $id}) WITH pl, (pl.latitude <> $lat OR pl.longitude <> $lng) AS differs SET pl.latitude = $lat, pl.longitud…` |  |  |
| backend/scripts/generate_book_events.py:38 | 순서만 다름 | 1 | `MATCH (e:Event) WHERE e.startDate IS NOT NULL RETURN e.theographic_id AS id, coalesce(e.nameKo, e.title) AS name, e.sortKey AS sortKey ORDER…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/scripts/inject_book_context.py:45 | 그대로 통과 | 1 | `UNWIND $rows AS row MATCH (b:Book {theographic_id: row.theographic_id}) SET b.background = row.background, b.themes = row.themes, b.keyVerse…` |  |  |
| backend/scripts/inject_book_context.py:63 | 그대로 통과 | 1 | `MATCH (b:Book) WHERE b.background IS NOT NULL RETURN count(b) AS c` |  |  |
| backend/scripts/inject_book_context.py:69 | 그대로 통과 | 1 | `MATCH (b:Book {slug: 'gen'}) RETURN b.background AS bg LIMIT 1` |  |  |
| backend/scripts/inject_date_corrections.py:106 | 순서만 다름 | 1 | `MATCH (b:Book)-[:CONTAINS_BOOK]->(e:Event) WHERE e.startDate IS NOT NULL RETURN b.theographic_id AS bid, collect(e.startDate) AS dates` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/scripts/inject_date_corrections.py:113 | 그대로 통과 | 1 | `UNWIND $rows AS row MATCH (b:Book {theographic_id: row.bid}) SET b.startYear = row.startYear, b.endYear = row.endYear` |  |  |
| backend/scripts/inject_date_corrections.py:36 | 그대로 통과 | 256 | `MATCH (e:Event {theographic_id: $id}) RETURN e.title AS title, e.startDate AS startDate` |  |  |
| backend/scripts/inject_date_corrections.py:55 | 그대로 통과 | 256 | `MATCH (e:Event {theographic_id: $id}) SET e.startDate = $newStartDate, e.sortKey = $newSortKey` |  |  |
| backend/scripts/inject_date_corrections.py:68 | 그대로 통과 | 4 | `MATCH (p:Person {theographic_id: $id}) RETURN p.name AS name, p.deathYear AS value` |  |  |
| backend/scripts/inject_date_corrections.py:88 | 그대로 통과 | 4 | `MATCH (p:Person {theographic_id: $id}) SET p.deathYear = $newValue` |  |  |
| backend/scripts/inject_ko_names.py:32 | 그대로 통과 | 1795 | `MATCH (p:Person {theographic_id: $id}) SET p.nameKo = $ko, p.aliasesKo = $alias` |  |  |
| backend/scripts/inject_person_context.py:38 | 그대로 통과 | 1 | `UNWIND $rows AS row MATCH (p:Person {theographic_id: row.theographic_id}) SET p.role = row.role, p.intro = row.intro, p.verses = row.verses_…` |  |  |
| backend/scripts/inject_person_context.py:46 | 그대로 통과 | 1 | `MATCH (p:Person) WHERE p.role IS NOT NULL RETURN count(p) AS c` |  |  |
| backend/scripts/inject_person_traits.py:36 | 그대로 통과 | 1 | `UNWIND $rows AS row MATCH (p:Person {theographic_id: row.theographic_id}) SET p.traits = row.traits_json` |  |  |
| backend/scripts/inject_person_traits.py:44 | 그대로 통과 | 1 | `MATCH (p:Person) WHERE p.traits IS NOT NULL RETURN count(p) AS c` |  |  |
| backend/scripts/inject_place_context.py:38 | 그대로 통과 | 1 | `UNWIND $rows AS row MATCH (p:Place {theographic_id: row.theographic_id}) SET p.background = row.background, p.keyVerse = row.keyVerse, p.key…` |  |  |
| backend/scripts/inject_place_context.py:49 | 그대로 통과 | 1 | `MATCH (p:Place) WHERE p.background IS NOT NULL RETURN count(p) AS c` |  |  |
| backend/scripts/inject_place_context.py:55 | 그대로 통과 | 1 | `MATCH (p:Place {theographic_id: 'authored-place-bethlehem'}) RETURN p.background AS bg LIMIT 1` |  |  |
| backend/scripts/load_authored_events.py:33 | 그대로 통과 | 7 | `MERGE (e:Event {theographic_id: $id}) SET e.authored = true, e.title = $title, e.nameKo = $nameKo, e.startDate = $startDate, e.sortKey = $so…` |  |  |
| backend/scripts/load_authored_events.py:54 | 그대로 통과 | 4 | `MATCH (e:Event {theographic_id: $id}) MATCH (p:Place {theographic_id: $place_id}) MERGE (e)-[:OCCURS_AT]->(p)` |  |  |
| backend/scripts/load_authored_events.py:65 | 그대로 통과 | 5 | `MATCH (e:Event {theographic_id: $id}) MATCH (p:Person {theographic_id: $person_id}) MERGE (e)-[:HAS_PARTICIPANT]->(p)` |  |  |
| backend/scripts/load_authored_events.py:76 | 그대로 통과 | 1 | `MATCH (e:Event) WHERE e.authored = true RETURN count(e) AS c` |  |  |
| backend/scripts/load_authored_events.py:79 | 그대로 통과 | 1 | `MATCH (e:Event)-[r:OCCURS_AT]->(:Place) WHERE e.authored = true RETURN count(r) AS c` |  |  |
| backend/scripts/load_authored_events.py:83 | 그대로 통과 | 1 | `MATCH (e:Event)-[r:HAS_PARTICIPANT]->(:Person) WHERE e.authored = true RETURN count(r) AS c` |  |  |
| backend/scripts/load_authored_genealogy.py:38 | 그대로 통과 | 1 (탐침) | `MERGE (p:Person {theographic_id: $id}) SET p.authored = true, p.name = $name, p.nameKo = $nameKo` |  |  |
| backend/scripts/load_authored_genealogy.py:50 | 그대로 통과 | 1 | `UNWIND $pairs AS pair MATCH (parent:Person {theographic_id: pair.parentId}) MATCH (child:Person {theographic_id: pair.childId}) MERGE (paren…` |  |  |
| backend/scripts/load_authored_genealogy.py:64 | 그대로 통과 | 1 | `MATCH (t:Person {theographic_id: $tail}) RETURN EXISTS { (t)-[:CHILD_OF*]->(:Person {theographic_id: $head}) } AS ok` |  |  |
| backend/scripts/load_authored_mothers.py:33 | 그대로 통과 | 1 | `UNWIND $pairs AS pair MATCH (m:Person {theographic_id: pair.motherId}) MATCH (c:Person {theographic_id: pair.childId}) MERGE (m)-[:PARENT_OF…` |  |  |
| backend/scripts/load_authored_persons.py:36 | 그대로 통과 | 2 | `MERGE (p:Person {theographic_id: $id}) SET p.authored = true, p.name = $name, p.nameKo = $nameKo` |  |  |
| backend/scripts/load_authored_persons.py:49 | 그대로 통과 | 1 | `MATCH (p:Person) WHERE p.authored = true RETURN count(p) AS c` |  |  |
| backend/scripts/load_books.py:150 | 기계적 치환 | 1 | `CREATE INDEX book_tid IF NOT EXISTS FOR (n:Book) ON (n.theographic_id)` | SyntaxError: syntax error at or near "book_tid" | Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g."L" USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"p"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)` (재작성 실행: neo4j와 일치) |
| backend/scripts/load_books.py:155 | 그대로 통과 | 1 | `UNWIND $rows AS row MERGE (b:Book {theographic_id: row.theographic_id}) SET b.name = row.name, b.nameKo = row.nameKo, b.testament = row.test…` |  |  |
| backend/scripts/load_books.py:173 | 그대로 통과 | 1 | `MATCH (b:Book) RETURN count(b) AS c` |  |  |
| backend/scripts/load_books.py:179 | 그대로 통과 | 2 | `UNWIND $rels AS rel MATCH (b:Book {theographic_id: rel.book_id}) MATCH (e:Event {theographic_id: rel.event_id}) MERGE (b)-[r:CONTAINS_BOOK]-…` |  |  |
| backend/scripts/load_books.py:189 | 그대로 통과 | 1 | `MATCH ()-[r:CONTAINS_BOOK]->() RETURN count(r) AS c` |  |  |
| backend/scripts/load_person_events.py:101 | 그대로 통과 | 1 | `MATCH (e:Event) WHERE e.authored = true RETURN count(e) AS c` |  |  |
| backend/scripts/load_person_events.py:105 | 그대로 통과 | 1 | `MATCH (e:Event) WHERE e.theographic_id IN $ids RETURN count(e) AS c` |  |  |
| backend/scripts/load_person_events.py:109 | 그대로 통과 | 1 | `MATCH (e:Event)-[:OCCURS_AT]->(:Place) WHERE e.theographic_id IN $ids RETURN count(e) AS c` |  |  |
| backend/scripts/load_person_events.py:114 | 그대로 통과 | 1 | `MATCH (e:Event)-[:HAS_PARTICIPANT]->(:Person) WHERE e.theographic_id IN $ids RETURN count(e) AS c` |  |  |
| backend/scripts/load_person_events.py:119 | 그대로 통과 | 1 | `MATCH (:Book)-[:CONTAINS_BOOK]->(e:Event) WHERE e.theographic_id IN $ids RETURN count(e) AS c` |  |  |
| backend/scripts/load_person_events.py:30 | 그대로 통과 | 327 | `MERGE (e:Event {theographic_id: $id}) SET e.authored = true, e.title = $title, e.nameKo = $nameKo, e.startDate = $startDate, e.sortKey = $so…` |  |  |
| backend/scripts/load_person_events.py:51 | 그대로 통과 | 305 | `MATCH (e:Event {theographic_id: $id}) MATCH (p:Place {theographic_id: $place_id}) MERGE (e)-[:OCCURS_AT]->(p)` |  |  |
| backend/scripts/load_person_events.py:62 | 그대로 통과 | 347 | `MATCH (e:Event {theographic_id: $id}) MATCH (p:Person {theographic_id: $person_id}) MERGE (e)-[:HAS_PARTICIPANT]->(p)` |  |  |
| backend/scripts/load_person_events.py:74 | 그대로 통과 | 338 | `MATCH (b:Book {theographic_id: $book_id}) MATCH (e:Event {theographic_id: $ev_id}) MERGE (b)-[r:CONTAINS_BOOK]->(e) SET r.primary = $primary` |  |  |
| backend/scripts/load_theographic.py:90 | 기계적 치환 | 4 | `CREATE INDEX person_tid IF NOT EXISTS FOR (n:Person) ON (n.theographic_id)` | SyntaxError: syntax error at or near "person_tid" | Cypher 인덱스 DDL 대신 SQL: `create_vlabel(g,'L')` 후 `CREATE INDEX … ON g."L" USING btree (agtype_access_operator(VARIADIC ARRAY[properties, '"p"'::agtype]))` + 속성맵 MATCH용 `USING gin (properties)` (재작성 실행: neo4j와 일치) |
| backend/scripts/load_theographic.py:96 | 그대로 통과 | 15 | `UNWIND $rows AS row MERGE (p:Person {theographic_id: row.id}) SET p.name = row.name, p.gender = row.gender, p.birthYear = row.birthYear, p.d…` |  |  |
| backend/scripts/load_verse_events.py:38 | 그대로 통과 | 13 | `MERGE (e:Event {theographic_id: $id}) SET e.authored = true, e.title = $title, e.nameKo = $nameKo, e.startDate = $startDate, e.sortKey = $so…` |  |  |
| backend/scripts/load_verse_events.py:60 | 그대로 통과 | 13 | `MATCH (b:Book {theographic_id: $book_id}) MATCH (e:Event {theographic_id: $ev_id}) MERGE (b)-[r:CONTAINS_BOOK]->(e) RETURN count(r) AS c` |  |  |
| backend/scripts/load_verse_events.py:73 | 그대로 통과 | 1 | `MATCH (e:Event) WHERE e.theographic_id STARTS WITH 'verse-event-' RETURN count(e) AS c` |  |  |
| backend/scripts/validate_event_chronology.py:101 | 순서만 다름 | 1 | `MATCH (e:Event)-[:PART_OF]->(parent:Event) WHERE e.theographic_id STARTS WITH 'rec' RETURN parent.theographic_id AS parentId, parent.title A…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/scripts/validate_event_chronology.py:81 | 순서만 다름 | 1 | `MATCH (e:Event) RETURN e.theographic_id AS id, e.title AS title, e.startDate AS startDate, e.sortKey AS sortKey, e.nameKo AS nameKo, e.autho…` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/scripts/validate_event_chronology.py:88 | 순서만 다름 | 1 | `MATCH (p:Person) RETURN p.theographic_id AS id, p.name AS name, p.nameKo AS nameKo, p.birthYear AS birthYear, p.deathYear AS deathYear` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |
| backend/scripts/validate_event_chronology.py:95 | 순서만 다름 | 1 | `MATCH (ev:Event)-[:HAS_PARTICIPANT]->(p:Person) RETURN ev.theographic_id AS eventId, p.theographic_id AS personId` | ORDER BY 없는 결과(또는 collect)의 순서 차이 |  |

## 적재 스크립트 재생

| 스크립트 | neo4j rc · 초 | AGE rc · 초 | 출력 일치 | AGE 오류 꼬리 |
|---|---|---|---|---|
| load_theographic | 0 · 2.9 | 0 · 4.8 | 예 |  |
| load_books | 0 · 0.9 | 0 · 1.0 | 예 |  |
| load_authored_persons | 0 · 0.3 | 0 · 0.3 | 예 |  |
| load_authored_events | 0 · 0.4 | 0 · 0.3 | 예 |  |
| load_authored_genealogy | 0 · 0.3 | 0 · 0.3 | 예 |  |
| load_authored_mothers | 0 · 0.3 | 0 · 0.3 | 예 |  |
| load_person_events | 0 · 3.2 | 0 · 3.5 | 예 |  |
| load_verse_events | 0 · 0.4 | 0 · 0.4 | 예 |  |
| apply_event_dedupe | 0 · 0.8 | 0 · 1.8 | 예 |  |
| enrich_place_coords | 0 · 0.6 | 0 · 0.4 | 예 |  |
| inject_ko_names | 0 · 2.5 | 0 · 3.8 | 아니오 |  |
| inject_date_corrections | 0 · 1.0 | 0 · 1.0 | 예 |  |
| inject_book_context | 0 · 0.3 | 0 · 0.3 | 예 |  |
| inject_person_context | 0 · 0.3 | 0 · 1.1 | 예 |  |
| inject_person_traits | 0 · 0.3 | 0 · 0.3 | 예 |  |
| inject_place_context | 0 · 0.3 | 0 · 0.3 | 예 |  |
| generate_book_events | 0 · 0.6 | 0 · 0.5 | 예 |  |
| validate_event_chronology | 0 · 0.4 | 0 · 0.4 | 순서만 다름 |  |

## 개수 대조 (기준 neo4j ↔ AGE 재생 그래프 `biblemap_loaders`)

| 종류 | 이름 | neo4j | AGE | 차 |
|---|---|---|---|---|
| 노드 | Book | 66 | 66 | +0 |
| 노드 | Event | 713 | 713 | +0 |
| 노드 | PeopleGroup | 23 | 23 | +0 |
| 노드 | Person | 1234 | 1234 | +0 |
| 노드 | Place | 257 | 257 | +0 |
| 관계 | CHILD_OF | 1174 | 1174 | +0 |
| 관계 | CONTAINS_BOOK | 857 | 857 | +0 |
| 관계 | HAS_PARTICIPANT | 1068 | 1068 | +0 |
| 관계 | MEMBER_OF | 99 | 99 | +0 |
| 관계 | OCCURS_AT | 492 | 492 | +0 |
| 관계 | PARENT_OF | 1174 | 1174 | +0 |
| 관계 | PARTNER_OF | 86 | 86 | +0 |
| 관계 | PART_OF | 201 | 201 | +0 |
| 관계 | SIBLING_OF | 1878 | 1878 | +0 |

내용 지문(라벨+전체 속성 / 유형+양끝 theographic_id+속성) 대칭차: 노드 0 · 관계 0. 다중 라벨 노드(AGE는 라벨 1개): 0.

## 엔드포인트 대조 · 지연

앱을 neo4j 단독·AGE 단독으로 각각 띄워 같은 요청의 JSON을 비교. 지연은 기록만(판정 무관), AGE가 10배 이상 느리면 `느림`.

| 엔드포인트 | 상태 neo4j/AGE | JSON | neo4j ms | AGE ms | 비고 |
|---|---|---|---|---|---|
| `/books-overview` | 200/200 | 같음 | 6 | 7 |  |
| `/book/{book}/chapters` | 200/200 | 같음 | 4 | 4 |  |
| `/book/{book}/quotations` | 200/200 | 같음 | 32 | 30 |  |
| `/book/{book}/chapter/1` | 200/200 | 같음 | 1 | 1 |  |
| `/events` | 200/200 | 순서만 다름 | 42 | 54 |  |
| `/covenants` | 200/200 | 같음 | 1 | 1 |  |
| `/messianic-prophecies` | 200/200 | 같음 | 1 | 1 |  |
| `/topical-verses` | 200/200 | 같음 | 1 | 1 |  |
| `/parables-miracles` | 200/200 | 같음 | 1 | 1 |  |
| `/event/{event}/verses` | 200/200 | 같음 | 8 | 3 |  |
| `/event/{authored}/verses` | 200/200 | 같음 | 0 | 0 |  |
| `/node/{authored}` | 200/200 | 순서만 다름 | 5 | 763 | 느림 |
| `/person/{jesus}/journey` | 200/200 | 같음 | 7 | 9 |  |
| `/person/{david}/journey` | 200/200 | 같음 | 1 | 3 |  |
| `/person/{jesus}/family` | 200/200 | 순서만 다름 | 48 | 24409 | 느림 |
| `/person/{david}/family` | 200/200 | 순서만 다름 | 12 | 809 | 느림 |
| `/person/{jesus}/event-ids` | 200/200 | 순서만 다름 | 3 | 3 |  |
| `/node/{jesus}/places` | 200/200 | 순서만 다름 | 5 | 8 |  |
| `/node/{event}/places` | 200/200 | 같음 | 3 | 2 |  |
| `/node/{group}/places` | 200/200 | 순서만 다름 | 6 | 14 |  |
| `/node/{book}/places` | 200/200 | 순서만 다름 | 3 | 2 |  |
| `/node/{place}/places` | 200/200 | 같음 | 2 | 1 |  |
| `/node/{jesus}/neighbors/grouped` | 200/200 | 다름(상한 절단) | 4 | 364 | 느림 ORDER BY 없는 이웃을 상한에서 자름 — 총수·길이·나머지 필드 같음, 고른 원소만 다름 |
| `/node/{jesus}` | 200/200 | 다름(상한 절단) | 5 | 739 | 느림 ORDER BY 없는 이웃을 상한에서 자름 — 총수·길이·나머지 필드 같음, 고른 원소만 다름 |
| `/node/{book}` | 200/200 | 순서만 다름 | 6 | 745 | 느림 |
| `/node/{place}` | 200/200 | 다름(상한 절단) | 5 | 731 | 느림 ORDER BY 없는 이웃을 상한에서 자름 — 총수·길이·나머지 필드 같음, 고른 원소만 다름 |
| `/node/{event}` | 200/200 | 순서만 다름 | 7 | 733 | 느림 |
| `/node/{group}` | 200/200 | 순서만 다름 | 4 | 739 | 느림 |
| `/person/{jesus}/reliance` | 200/200 | 같음 | 2 | 11 |  |
| `/reliance/ranking` | 200/200 | 같음 | 0 | 1 |  |
| `/persons/curated` | 200/200 | 같음 | 0 | 1 |  |
| `/keypeople-cards` | 200/200 | 같음 | 6 | 8 |  |
| `/person/{jesus}/connections` | 200/200 | 순서만 다름 | 2 | 4 |  |
| `/person/{david}/relations` | 200/200 | 같음 | 5 | 5 |  |
| `/place/{place}/curated-persons` | 200/200 | 같음 | 1 | 1 |  |
| `/place/{place}` | 200/200 | 같음 | 1 | 1 |  |
| `/search?q=다윗` | 200/200 | 다름 | 12 | 17 | neo4j {"nodes": [{"id": "rec1ZMFtfbEvoGC73", "label": "Person", "name": "David", "nameKo": "다윗"}, {"id": "authored-saul-gibeah-spear", "label": "Event", "name": "Saul… vs AGE {"nodes": [{"id": "rec1ZM… |
| `/search?q=Jerusalem` | 200/200 | 같음 | 11 | 14 |  |
| `/tours` | 200/200 | 같음 | 1 | 2 |  |
| `/tour/david-united-kingdom` | 200/200 | 같음 | 3 | 4 |  |
| `/stats` | 200/200 | 순서만 다름 | 42 | 62 |  |
| `/verse/09017049/persons` | 200/200 | 같음 | 4 | 10 |  |
| `/timeline/canon` | 200/200 | 순서만 다름 | 1 | 2 |  |
| `/words/{book}` | 200/200 | 같음 | 2 | 4 |  |
| `/words/{book}/verses?w=하나님` | 200/200 | 같음 | 2 | 2 |  |

## 점검 범위와 한계

- 앱·스크립트 코드는 고치지 않았다. `neo4j.GraphDatabase.driver`를 바꿔치기한 어댑터(`age_adapter.py`)가 같은 코드를 AGE에서 돌린다 — 이전 시 실제 드라이버(psycopg + `cypher()` 감싸기)도 같은 일을 해야 한다.
- 탐침: 데이터에 해당 항목이 없어 실제 체인·API에서 한 번도 안 불린 지점은 소스의 쿼리 리터럴을 꺼내 가짜 인자(`'agecheck-probe'`)로 양쪽에서 실행 후 롤백했다 — 구문 호환성 증거이지 실제 데이터 경로 증거는 아니다. 호출 지점 표에서는 실행 수 뒤에 `(탐침)`으로 표시한다.
- `apply_event_dedupe`는 `data/` 임시 사본에서, `generate_book_events`는 DB 부분(`load_events`)만 돌렸다(LLM 호출 제외).
- 점검 후 레포 `data/` 변경: 없음.
- 결과 비교는 노드/관계를 (라벨·유형 + 속성)으로 정규화해 엔진 내부 id 차이를 무시한다. `순서만 다름` = 리스트를 깊이 정렬하면 같음(ORDER BY 없는 결과·collect 순서).
