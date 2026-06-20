---
last_mapped_commit: 42bd230af7e22bc1839023a1189d6ae696944188
mapped: 2026-06-20
---

# BibleMap — Codebase Concerns

## 1. Hardcoded / Exposed Credentials

### `.env` committed default password
`/Users/calmonion/Project/BibleMap/.env` is gitignored but exists locally with `NEO4J_PASSWORD=biblemap123`. This is a weak default password. If the file is accidentally staged or if the same password is reused in production, it becomes a secret-exposure risk. `.env.example` correctly shows a placeholder, but there is no enforcement that the actual file uses a different value.

### f-string Cypher in production route (low-risk today, fragile pattern)
`/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py` lines 168–170 interpolate a module-level Python constant (`NODE_NEIGHBOR_LIMIT`) directly into a Cypher string via an f-string. The constant is not user-supplied so there is no injection risk today, but the pattern looks like a parameterized value and could be mistakenly changed to accept external input in future.

`/Users/calmonion/Project/BibleMap/backend/app/routes/search.py` line 27 interpolates `SEARCH_LIMIT` the same way.

`/Users/calmonion/Project/BibleMap/backend/app/main.py` lines 15–18 build the `CREATE INDEX` statement with an f-string using a hardcoded list of label names. Labels come from a fixed Python list, so no injection path exists, but the pattern is inconsistent with parameterized usage elsewhere.

`/Users/calmonion/Project/BibleMap/backend/scripts/inject_ko_names.py` line 26 interpolates `label` (a Python variable resolved from a fixed list of strings) into a Cypher `MATCH` clause. Safe today because the caller controls the variable, but would become an injection point if the label were ever derived from request input.

### XSS in maplibre-gl popup via `setHTML`
`/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx` lines 447 and 491 call `.setHTML(...)` with `${label}` interpolated directly. `label` traces to `p.nameKo` from the GeoJSON `properties` object, which in turn comes from Neo4j. Because the data is internal (graph DB, not user-controlled input), the practical XSS surface is low. If nameKo values ever contain `<script>` or HTML tags (e.g., through a compromised script run), they would execute inside the popup. `.setText()` or HTML-escaping would eliminate this class of risk entirely.

## 2. Missing Authentication and Authorization

The FastAPI app (`/Users/calmonion/Project/BibleMap/backend/app/main.py`) has **no authentication middleware**. All API endpoints are publicly accessible to anyone who can reach port 8000. The CORS policy is `allow_origins=["*"]`, meaning any browser origin can query the API. For a read-only public bible reference tool this may be intentional, but there is no rate limiting, so the API can be scraped or used to DoS the Neo4j instance without throttling.

## 3. Performance Hotspots

### Full-graph scan on every search request
`/Users/calmonion/Project/BibleMap/backend/app/routes/search.py` runs `MATCH (n) WHERE n.nameKo CONTAINS $q OR ...` — a label-less full graph scan on every search. The `theographic_id` index created at startup does not help substring searches on `nameKo` or `name`. With the current dataset this is tolerable, but latency will grow linearly with graph size. No Neo4j full-text index is created for `nameKo` or `name`.

### All events loaded into process memory on first request, never evicted
`/Users/calmonion/Project/BibleMap/backend/app/routes/events.py` `_compute_events()` uses `@functools.lru_cache(maxsize=1)`. It fetches every Event node and all their Book relationships in one query, builds a Python list, and holds it in memory for the lifetime of the process. There is no TTL and no cache-clear endpoint. If the Neo4j data changes (e.g., a script is run to add events), the API must be restarted to reflect the change. The same applies to `_load_approx_book_index()` and all three overlay loaders in `backend/app/overlays.py`.

### `get_node_neighbors_grouped` fetches all neighbors before Python-level cap
`/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py` `get_node_neighbors_grouped()` issues `MATCH (n {theographic_id: $id})-[r]-(m) RETURN m, type(r) AS rel, labels(m) AS mlabels` with no Cypher-level `LIMIT`. Neo4j streams all neighbor records; Python then discards records once the per-type cap (`MAX_NEIGHBORS_PER_TYPE = 30`) is hit. For high-degree nodes this transfers and deserializes unnecessary rows from the DB driver.

### `/person/{node_id}/event-ids` has no LIMIT
`/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py` line 13–14: `MATCH (e:Event)-[:HAS_PARTICIPANT]->(n:Person {theographic_id: $id}) RETURN e.theographic_id AS id` — no LIMIT clause. A person with many event participations returns an unbounded result set. This list is then held in a `Set` in the browser (`useNodeSelection.js` `personEventIds`) and iterated over every timeline render to filter events.

### PeopleGroup places query does three hops without LIMIT
Lines 56–61 in `backend/app/routes/nodes.py`: the PeopleGroup path does `PeopleGroup ← MEMBER_OF ← Person ← HAS_PARTICIPANT ← Event → OCCURS_AT → Place`. For a large group this is a wide traversal with no LIMIT. The de-duplication (`seen` set) is applied in Python after the full result set is returned.

### N+1 write pattern in `inject_ko_names.py`
`/Users/calmonion/Project/BibleMap/backend/scripts/inject_ko_names.py` lines 31–32 run one `session.run()` per node in a loop (one transaction per node). For large mappings this is an N+1 write pattern. This is a one-off script so it does not affect runtime, but it is slow (no batching via `UNWIND`).

## 4. Fragile Areas / Missing Error Handling

### DB singleton has a race condition under concurrent startup
`/Users/calmonion/Project/BibleMap/backend/app/db.py` uses a module-level `_driver = None` with a check-then-set pattern. FastAPI with multiple worker processes (e.g., `--workers 4` with Uvicorn/Gunicorn) would create multiple driver instances. Within a single process the GIL prevents a literal race, but the pattern is not process-safe. The current Docker setup uses a single worker by default, so this is latent.

### `overlays._load` silently returns `{}` on JSON parse error
`/Users/calmonion/Project/BibleMap/backend/app/overlays.py` lines 23–27: `json.JSONDecodeError` is caught and returns an empty dict. An encoding error or truncated file causes the entire overlay to silently return no data — books will have no approximate years, events will have no verse overlays — with no log entry and no API error. `IOError` / `OSError` (e.g., permissions) is not caught and will propagate as a 500.

### `expandPlace` in MapView swallows all non-abort errors silently
`/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx` `expandPlace()` function: the catch block is `catch { return }` with no error state or user feedback. If the `/node/{id}/neighbors/grouped` call fails (network error, 500), the event ring simply does not appear with no indication to the user.

### Timeline `toggleVerseView` error path produces an empty verse box
`/Users/calmonion/Project/BibleMap/frontend/src/TimelineView.jsx` line 138: on fetch error, `eventVerses` is set to `{ id, data: { books: [] } }`, which renders the box with "표시할 구절이 없습니다". This is indistinguishable from a legitimate empty result — the user cannot tell whether the verse fetch failed or the event genuinely has no verses linked.

### `useNodeSelection` person event-ids error silently nulls the filter
`/Users/calmonion/Project/BibleMap/frontend/src/useNodeSelection.js` line 24: `.catch(() => setPersonEventIds(null))`. If the fetch fails, the Timeline person filter is silently disabled. The user sees all events rather than only that person's events, with no indication anything went wrong.

### `get_node` imports `json` inside a conditional branch
`/Users/calmonion/Project/BibleMap/backend/app/routes/nodes.py` around line 232: `import json as _json` is inside an `if label_val == "Person"` block. This is a minor style issue (module-level imports are conventional in Python) but repeated requests for Person nodes re-trigger the import machinery each call (CPython caches it in `sys.modules`, so it is not a performance issue, just fragile if someone adds logic around the import).

### `books.py` has two separate queries that both run `MATCH (b:Book) RETURN b ORDER BY b.bookOrder ASC`
`/Users/calmonion/Project/BibleMap/backend/app/routes/books.py` lines 15 and 40 both run the same full Book scan with no caching. Two endpoints (`/books-overview` and `/books`) each hit Neo4j independently. Neither is cached; `/books-overview` even sets `Cache-Control: no-store`.

## 5. Security — No Input Length Validation on Search

`/Users/calmonion/Project/BibleMap/backend/app/routes/search.py` only checks `if not q.strip()`. There is no maximum length check on the query parameter. A very long `q` value (e.g., 10,000 characters) is passed directly into the Cypher `CONTAINS` predicate, which will cause Neo4j to evaluate a full graph scan with a large string pattern. This is a low-severity DoS vector given the read-only nature of the API and no auth.

## 6. External Dependencies with No Fallback

### Map tile source is an external ESRI endpoint
`/Users/calmonion/Project/BibleMap/frontend/src/MapView.jsx` uses `https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}` as the sole tile source. If this endpoint is unavailable or rate-limited, the map renders with no tiles and no user feedback (maplibre-gl shows a blank canvas).

### Map font glyphs from protomaps.github.io
The `glyphs` URL also points to an external CDN (`https://protomaps.github.io/basemaps-assets/fonts/...`). Loss of this endpoint causes all map labels (place names, cluster counts) to silently disappear.
