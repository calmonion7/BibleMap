# 바이블 맵 (Bible Map) — 설계 문서

> 성경의 시기·인물관계·사건을 하나의 지식 그래프로 엮어, 지도·타임라인·관계도 세 가지로 탐색하는 통합 서비스.
> 범위: 성경 전체 / 대상: 개인 성경공부 · 교회·교육 · 일반 입문자 모두.

---

## 1. 핵심 원칙

1. **하나의 그래프, 세 가지 렌더링.** 지도·타임라인·관계도를 따로 만들지 않는다. 단일 지식 그래프를 세 방식으로 투영한다.
2. **전체를 적재하되, 전체를 그리지 않는다.** 데이터는 성경 전체를 담되, 화면은 항상 검색·진입점·이웃 노드 중심으로 일부만 렌더링한다. (인물 3,000명 동시 표시 = 금지)
3. **모든 노드는 구절(passage)로 앵커링된다.** 본문이 진실의 원천이며, 모든 탐색은 결국 구절로 돌아올 수 있어야 한다.
4. **그래프 DB 확정: Neo4j.** 데이터가 본질적으로 그래프이고 Theographic이 Neo4j export를 제공하므로, 중간 단계 없이 Neo4j로 직행한다.

---

## 2. 데이터

### 2.1 소스
- **Theographic / Viz.Bible** (robertrouse/theographic-bible-metadata): 인물·장소·시대·사건·구절 지식 그래프. JSON·CSV·Neo4j 제공. **`neo4j/` export를 적재 소스로 사용**(Neo4j 확정에 따라).
- **OpenBible.info Geo**: 장소 위경도 (Theographic 장소 데이터의 기반).

### 2.2 라이선스 ⚠️
- Theographic = **CC-BY-SA-4.0**.
  - **BY**: 출처 표기 필수 (앱 내 크레딧 페이지).
  - **SA**: 이 데이터를 가공·확장한 *데이터셋*은 동일 라이선스로 공개해야 할 수 있음.
- **결정 필요**: 가공 DB를 독점 자산으로 둘 계획이면 법률 검토. (본 문서는 법률 자문이 아님.)

### 2.3 데이터 모델 (엔티티 + 관계)

| 엔티티 | 핵심 필드 | 관계 |
|---|---|---|
| **Person** | id, 이름(원어/영문), 생몰, 성별 | parentOf / spouseOf / siblingOf (가계), participatesIn (사건) |
| **Place** | id, 이름, lat/lng, 지역분류(region/city/water) | locationOf (사건) |
| **Event** | id, 제목, 날짜, 기간, 선후(predecessors) | hasParticipant(Person), occursAt(Place), inPeriod(Period) |
| **Period** | id, 제목, 시작/끝 연도 | groups(Event) |
| **Passage** | book, chapter, verse | references(모든 엔티티) |

> 모든 엔티티에 `nameKo`(한글명) 필드를 추가하는 **한글 번역 매핑 테이블**을 원본 id에 붙인다. 원본 데이터는 영문이므로 이 레이어가 필수.

---

## 3. 아키텍처

### 3.1 프론트엔드 (React 19 + Vite)
- **지도 뷰**: MapLibre GL (무료, 역사 지도 타일 오버레이 가능)
- **관계도 뷰**: react-force-graph 또는 Cytoscape.js (focus+context 지원 중요)
- **타임라인 뷰**: vis-timeline 또는 D3 커스텀
- **공유 상태**: 현재 선택된 엔티티(selectedNode) 하나가 세 뷰를 동시에 구동. 인물 클릭 → 세 뷰가 동기화되어 갱신.

### 3.2 백엔드 (FastAPI / Python + Neo4j)
- **DB**: Neo4j. Theographic의 `neo4j/` export를 그대로 적재해 초기 데이터 확보.
- **호스팅**: 로컬 Docker self-host로 **확정**. `neo4j:5` 공식 이미지(arm64 지원 → Apple Silicon에서 Rosetta 불필요), 데이터는 볼륨 마운트로 영속화. **Mac 로컬 상시 가동 확정** (상세는 3.4).
- **드라이버**: `neo4j` 공식 Python 드라이버를 FastAPI에 연결. 그래프 순회(가계 N촌, 사건 선후 체인, 인물 간 최단 경로)는 Cypher로 직접 표현.
- API: `GET /node/{id}`, `GET /node/{id}/neighbors`, `GET /search?q=`, `GET /period/{id}/events` 등 → 내부적으로 Cypher 쿼리 실행.

### 3.3 한글 매핑 레이어

**기준 역본: 개역개정** (한국 개신교에서 가장 보편적). 표기 기준을 파일 단위로 선언해, 이후 새번역 등으로 교체·추가 가능.

**원칙**
- Theographic의 **안정적 id를 키로** 매핑(영문명은 동명이인·중복이 있어 키로 부적합).
- **고유명사(인명·지명)**와 **서술형 제목(사건·시대)**을 분리.
- 구절 본문 텍스트는 이 레이어에 **포함하지 않음** — 역본 텍스트는 저작권 대상(6번 리스크 참조).

**파일 구조** (`/data/names_ko/`)
```json
// people.json  (기준: 개역개정)
{
  "<theographic_person_id>": { "ko": "모세", "alias": ["모세스"] },
  "<theographic_person_id>": { "ko": "베드로", "alias": ["시몬", "시몬 베드로", "게바"] }
}
```
- `ko`: 기본 표시명 / `alias`: 검색용 이형·별칭(선택).
- 동일 구조로 `places.json`, `events.json`, `periods.json`.
- 사건·시대는 서술형 제목(예: `The Exodus` → `출애굽`)이고 수가 적으므로 **전수 큐레이션**. 인명·지명은 아래 단계적 채움.

**채움 전략** (인물 3,000+를 한 번에 번역 불가)

| 단계 | 대상 | 방법 |
|---|---|---|
| Tier 1 | 핵심 인물·지명 수백 개 | 개역개정 표기로 수동 큐레이션 (먼저 출시될 가시 영역) |
| Tier 2 | 나머지 롱테일 | 위키데이터(CC0) 한국어 라벨 또는 고유명사 색인으로 일괄 생성 후 검수 |
| Fallback | 매핑 없음 | 영문명 그대로 표시 + `nameKoMissing: true` 플래그 → UI에서 미번역 표시·제보 |

> 위키데이터는 성경 인물·지명에 한국어 라벨이 풍부하고 **CC0**라 라이선스가 깨끗함. Theographic이 외부 DB 링크를 제공하므로 QID 브리지로 Tier 2 자동화에 적합.

**Neo4j 반영** — 별도 JOIN 없이 노드 속성으로 적재(쿼리·검색 단순화). 매핑 파일은 레포에서 버전 관리(진실의 원천)하고, 로더가 idempotent하게 주입:
```cypher
// FastAPI 로더가 배치 실행 (APOC 불필요). 식별 속성명은 export 스키마에 맞춤.
UNWIND $rows AS row
MATCH (p:Person { theographic_id: row.id })
SET p.nameKo = row.ko, p.aliasesKo = row.alias;
```

**한글 검색** — full-text 인덱스로 한글·영문·별칭 동시 검색:
```cypher
CREATE FULLTEXT INDEX entityKo IF NOT EXISTS
FOR (n:Person|Place|Event|Period)
ON EACH [n.nameKo, n.name, n.aliasesKo];
// 조회: CALL db.index.fulltext.queryNodes('entityKo', $q) YIELD node, score RETURN node LIMIT 20
```

**API 응답 규칙** — `nameKo`가 있으면 그것을, 없으면 `name`(영문) + 미번역 플래그를 반환. 프론트는 플래그로 영문 표시·제보 UX를 처리.

### 3.4 배포 토폴로지 (PortfoliOn과 동일 방식)
- **프론트엔드**: Vercel 배포 (PortfoliOn 패턴).
- **백엔드 + DB**: Mac 로컬 Docker로 구동, **PortfoliOn과 동일한 터널링**으로 `https://biblemap.taebro.com` 노출.
- **상시 가동 (Docker 기준 — PortfoliOn과 메커니즘 차이)**: PortfoliOn은 launchd가 uvicorn 프로세스를 직접 KeepAlive했지만, 여기선 컨테이너이므로 조합이 다름:
  - 컨테이너: `restart: unless-stopped` (크래시·데몬 재시작 시 자동 복구). → launchd로 API를 띄울 필요 없음.
  - Docker Desktop: **로그인 시 자동 시작** 설정 → 재부팅 후 스택 자동 기동.
  - cloudflared: 기존 호스트 터널이 이미 상시 구동 중이므로 ingress 규칙만 추가하면 됨(별도 launchd 불필요).
  - 노트북 뚜껑 닫고 운용 시: 전원 연결 + `sudo pmset -c disablesleep 1` (클램셸 잠자기 차단).
- **⚠️ 핵심 차이점 — DB 노출 금지**: PortfoliOn은 JSON 파일 저장이라 외부 노출 대상 DB가 없었음. 바이블 맵은 Neo4j(상태 보유)가 생기므로:
  - 터널은 **FastAPI 앱 포트(예: 8000)만** 가리킨다.
  - Neo4j 포트(7474 HTTP / 7687 Bolt)는 **퍼블릭에 절대 노출하지 않는다.** Docker 네트워크 내부 통신만 허용하고, 호스트 포트 바인딩은 `127.0.0.1`로 제한(`127.0.0.1:7474:7474`)하거나 로컬 관리용으로만 사용.
  - FastAPI → Neo4j 연결은 compose 내부 서비스명(`bolt://neo4j:7687`)으로.
- **compose 구성(개념)**: `neo4j`(내부 전용) + `api`(FastAPI, 터널 대상) 두 서비스를 한 compose 네트워크에 묶기. 터널 클라이언트는 `api`만 바라봄.
- **Cloudflare Tunnel(cloudflared)**: 기존 PortfoliOn 터널에 public hostname만 추가. `~/.cloudflared/config.yml`의 `ingress`에 규칙 추가:
  ```yaml
  ingress:
    - hostname: biblemap.taebro.com
      service: http://localhost:8000      # api 컨테이너 publish 포트
    - hostname: portfolion.taebro.com      # 기존 규칙 유지
      service: http://localhost:8001
    - service: http_status:404             # catch-all, 반드시 맨 마지막
  ```
  그리고 DNS 라우트 등록: `cloudflared tunnel route dns <tunnel-name> biblemap.taebro.com`
  - cloudflared가 outbound로만 연결하므로 Mac에 인바운드 포트를 열지 않음 → ingress에 적은 것(api 8000)만 외부 접근 가능, Neo4j는 구조적으로 차단됨.

---

## 4. 전체 규모를 다루는 UX 전략 (털뭉치 방지)

1. **검색 우선 진입.** 첫 화면은 빈 그래프가 아니라 검색창 + 추천 진입점(주요 인물/사건 카드).
2. **Focus + Context.** 노드 선택 시 해당 노드와 직접 이웃(1~2촌)만 표시. 나머지는 흐리게/숨김.
3. **Level of Detail.** 지도/타임라인 줌 레벨에 따라 표시 밀도 조절 (멀리 = 시대 단위, 가까이 = 개별 사건).
4. **필터.** 책 / 시대 / 인물 그룹(족장·왕·사도 등) / 신구약으로 그래프 부분집합 추출.
5. **큐레이션된 투어.** 입문자용으로 "출애굽 경로", "예수의 생애", "바울의 전도여행" 같은 미리 짜인 동선 제공 (일반 대중 대상 충족).

---

## 5. 단계별 구현 플랜

```
Phase 0 — Neo4j 적재             → verify: Theographic neo4j export 적재 후 Cypher로 임의 인물의 가계·사건·장소가 조회됨
Phase 1 — 단일 엔티티 상세 페이지   → verify: /node/{id} 가 한글명 포함 이웃 목록 반환, 프론트에서 렌더
Phase 2 — 지도 뷰 (장소 투영)       → verify: 선택 사건의 발생지가 지도에 핀으로 표시, 클릭 시 사건 상세
Phase 3 — 타임라인 뷰 (시대/날짜)   → verify: 시대 축에 사건 정렬, 선택 시 지도·상세 동기화
Phase 4 — 관계도 뷰 (focus+context) → verify: 인물 선택 시 1~2촌만 표시, 털뭉치 없음
Phase 5 — 3뷰 동기화 + 검색 + 투어  → verify: 한 노드 선택이 세 뷰를 동시 갱신, 검색·큐레이션 투어 동작
```

각 Phase는 "검증 기준을 통과할 때까지 루프" 방식으로 진행. 다음 Phase 전 이전 Phase 검증 통과를 전제.

---

## 6. 열린 질문 / 리스크

- **라이선스(SA)**: 독점 DB 의도 시 충돌. → 초기 결정 필요.
- **연대 논쟁**: 성경 사건 연대는 학설마다 다름(특히 출애굽 시기). → 데이터 출처/학설을 명시하고 단일 정답처럼 보이지 않게.
- **한글 번역 표준**: 개역개정/새번역 등 역본별 인명·지명 표기 차이. → 기준 역본 1개 먼저 고정.
- **본문 저작권**: 성경 *데이터*는 자유롭지만 특정 *번역본 텍스트*는 저작권 있음. 구절 표시 시 퍼블릭 도메인 역본 또는 라이선스 확보 필요.

---

## 7. 첫 작업 (Claude Code 착수 지점)

1. `theographic-bible-metadata` 레포 clone, `neo4j/` export 구조 파악.
2. 로컬 Docker로 Neo4j 기동(`neo4j:5`, 포트 7474/7687, 볼륨 마운트) 후 export 적재.
3. FastAPI + `neo4j` 드라이버로 `/node/{id}` / `/node/{id}/neighbors` 구현 (Phase 0~1).
4. 임의 인물(예: 모세)로 Cypher 그래프 순회가 동작하는지 검증.
