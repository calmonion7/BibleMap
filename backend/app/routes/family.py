"""GET /person/{id}/family — 인물 중심(ego-centric) 가계도 서브그래프.

조상선(위, 뿌리까지) + 자손(아래 2세대) + focus의 직계 형제·배우자를 반환한다.
프론트는 parentEdges를 focus에서 위/아래로 걸어 세대별 트리를 구성한다.

응답:
  focus:       요청 인물 id (그대로 에코)
  nodes:       서브그래프의 모든 Person [{id, name, nameKo, authored}]
  parentEdges: [[parentId, childId], ...] — 조상 트리 + 자손 2세대의 PARENT_OF 간선
  siblings:    focus의 직계 형제 id 목록
  partners:    focus의 직계 배우자 id 목록
  mothers:     {자식id: 다른부모id} — focus 자식의 어머니 그룹핑용(여성 부모 우선,
               focus가 어머니면 아버지가 담김). 매핑된 부모 노드는 nodes에 포함 보장.
존재하지 않는 인물 id는 빈 서브그래프로 폴백한다(404 아님).

노드 확장 필드(task#196): slug(인장 조회용 — 큐레이션 35 + 인장 보유 15, 없으면 None),
curated/hasIntro(미니 카드 데이터 계층 플래그), role(신분 한줄, ADR-0027),
lineage(예수 계보 마태1+눅3 — 아담의 자손 ∩ 예수의 조상 +양끝. 간선의 계보 여부는
양 끝 노드가 모두 lineage면 참으로 파생 — PARENT_OF로 이어진 두 계보 노드는 항상
아담→…→부모→자식→…→예수 경로를 이룬다).
"""
import json
import logging
from functools import lru_cache

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver
from ..overlays import _resolve

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_GENERATIONS = 100  # 조상선 상한 (아담→예수 ~76대 여유)


@lru_cache(maxsize=1)
def _family_role_pairs() -> dict:
    """person_relations '가족' 관계의 정본 role → {frozenset({idA,idB}): {id: role}}.

    role은 손큐레이션된 원근 라벨(맏아들·둘째 아들·편애한 아들·아버지 등, ADR 없음/ CONTEXT '인물 관계').
    theographic엔 출생순이 없어(children 배열 비정렬) 첫째/둘째는 이 큐레이션이 유일한 정본 원천이다.
    endpoints의 slug(둘 다 있는 관계만)를 theographic_id로 해석해 키를 만든다 — nameKo 문자열만 쓰면
    동명이인(theographic엔 다수 존재, 예: 요셉 6명)에게 다른 서사의 role이 잘못 유출된다(task#263).
    """
    path = _resolve("person_relations/relations.json")
    if path is None:
        return {}
    with open(path, encoding="utf-8") as f:
        rels = json.load(f).get("relations", [])
    slug_to_id = {slug: pid for pid, slug in _id_to_slug().items()}
    out: dict = {}
    for r in rels:
        if r.get("type") != "가족":
            continue
        eps = r.get("endpoints", [])
        if len(eps) != 2:
            continue
        a, b = eps[0], eps[1]
        ia, ib = slug_to_id.get(a.get("slug")), slug_to_id.get(b.get("slug"))
        if not ia or not ib or ia == ib:
            continue
        m = out.setdefault(frozenset({ia, ib}), {})
        if a.get("role"):
            m[ia] = a["role"]
        if b.get("role"):
            m[ib] = b["role"]
    return out


@lru_cache(maxsize=1)
def _id_to_slug() -> dict:
    """인장 조회용 id → slug. 큐레이션 35인(person_events/<slug>.json 신원 규약, persons._build_list)
    + 비큐레이션 인장 보유 인물(person_slugs/seal_slugs.json, ADR-0025). 큐레이션이 우선."""
    from .persons import _build_list
    out = {p["id"]: p["slug"] for p in _build_list()}
    path = _resolve("person_slugs/seal_slugs.json")
    if path is not None:
        with open(path, encoding="utf-8") as f:
            seals = json.load(f)
        for slug, pid in seals.items():
            if slug != "note":
                out.setdefault(pid, slug)
    return out


@lru_cache(maxsize=1)
def _curated_ids() -> frozenset:
    from .persons import _build_list
    return frozenset(p["id"] for p in _build_list())


_JESUS_ID = "recgkFqZovgbr3pAi"


@lru_cache(maxsize=1)
def _lineage_ids() -> frozenset:
    """예수 계보(마태1+눅3) 노드 집합 — 예수에서 남계(男系) 사슬만 따라 오른 조상들 + 마리아.

    마태1(요셉계)·눅3(마리아→헬리계)·창세기 계보(아브라함→아담)는 모두 부자(父子) 사슬이므로
    "여성 조상은 마리아만 허용, 나머지는 Male만 통과"가 정확히 두 사슬을 재현한다.
    단순 조상 교집합은 모계 우회(압살롬→다말→마아가→아비야)까지 과잉 마킹해 기각."""
    driver = get_driver()
    with driver.session() as session:
        mary = session.run(
            "MATCH (j:Person {theographic_id: $j})-[:CHILD_OF]->(m:Person {gender: 'Female'}) "
            "RETURN m.theographic_id AS id",
            j=_JESUS_ID,
        ).single()
        mary_id = mary["id"] if mary else ""
        rows = session.run(
            f"""
            MATCH p = (j:Person {{theographic_id: $j}})-[:CHILD_OF*1..{MAX_GENERATIONS}]->(a:Person)
            WHERE all(n IN nodes(p)[1..] WHERE n.gender = 'Male' OR n.theographic_id = $mary)
            RETURN DISTINCT a.theographic_id AS id
            """,
            j=_JESUS_ID, mary=mary_id,
        )
        ids = {r["id"] for r in rows}
    return frozenset(ids | {_JESUS_ID})


def _node(p) -> dict:
    props = dict(p)
    name = props.get("name") or props.get("title", "")
    name_ko = props.get("nameKo")
    pid = props.get("theographic_id", "")
    return {
        "id": pid,
        "name": name,
        "nameKo": name_ko if name_ko else name,
        "gender": props.get("gender"),
        "authored": bool(props.get("authored")),
        "slug": _id_to_slug().get(pid),
        "curated": pid in _curated_ids(),
        "hasIntro": props.get("intro") is not None,
        "role": props.get("role"),
        "lineage": pid in _lineage_ids(),
    }


@router.get("/person/{node_id}/family")
def get_person_family(node_id: str):
    driver = get_driver()
    with driver.session() as session:
        focus = session.run(
            "MATCH (f:Person {theographic_id: $id}) RETURN f",
            id=node_id,
        ).single()
        if not focus:
            return JSONResponse(
                content={"focus": node_id, "nodes": [], "parentEdges": [],
                         "siblings": [], "partners": []},
                headers={"Cache-Control": "max-age=300"},
            )

        # 조상 트리 간선: 각 조상 a의 PARENT_OF 자식이 focus이거나 다른 조상인 것만
        # (사촌·삼촌 계열은 제외 — 순수 조상선).
        ancestor_edges = session.run(
            f"""
            MATCH (f:Person {{theographic_id: $id}})
            OPTIONAL MATCH (f)-[:CHILD_OF*1..{MAX_GENERATIONS}]->(anc:Person)
            WITH f, collect(DISTINCT anc) AS ancs
            UNWIND ancs AS a
            MATCH (a)-[:PARENT_OF]->(child:Person)
            WHERE child = f OR child IN ancs
            RETURN a AS parent, child AS child
            """,
            id=node_id,
        )
        # 자손 2세대: focus→자녀, 자녀→손주
        descendant_edges = session.run(
            """
            MATCH (f:Person {theographic_id: $id})-[:PARENT_OF]->(c1:Person)
            OPTIONAL MATCH (c1)-[:PARENT_OF]->(c2:Person)
            RETURN f AS parent1, c1 AS child1, c2 AS grandchild
            """,
            id=node_id,
        )
        # 자식 → 다른 부모(어머니 그룹핑용): 여성 부모 우선, focus 자신은 제외
        other_parents = session.run(
            """
            MATCH (f:Person {theographic_id: $id})-[:PARENT_OF]->(c:Person)<-[:PARENT_OF]-(m:Person)
            WHERE m.theographic_id <> $id
            RETURN c.theographic_id AS childId, collect(m) AS parents
            """,
            id=node_id,
        )
        siblings = session.run(
            "MATCH (f:Person {theographic_id: $id})-[:SIBLING_OF]-(s:Person) RETURN DISTINCT s",
            id=node_id,
        )
        partners = session.run(
            "MATCH (f:Person {theographic_id: $id})-[:PARTNER_OF]-(pt:Person) RETURN DISTINCT pt",
            id=node_id,
        )

        nodes: dict[str, dict] = {}
        edges: list[list[str]] = []
        seen_edges: set[tuple[str, str]] = set()

        def add(p) -> str:
            n = _node(p)
            if n["id"]:
                nodes[n["id"]] = n
            return n["id"]

        def add_edge(pid: str, cid: str):
            if pid and cid and (pid, cid) not in seen_edges:
                seen_edges.add((pid, cid))
                edges.append([pid, cid])

        add(focus["f"])
        for r in ancestor_edges:
            add_edge(add(r["parent"]), add(r["child"]))
        for r in descendant_edges:
            pid = add(r["parent1"])
            cid = add(r["child1"])
            add_edge(pid, cid)
            if r["grandchild"] is not None:
                add_edge(cid, add(r["grandchild"]))

        mothers: dict[str, str] = {}
        for r in other_parents:
            parents = r["parents"]
            pick = next((p for p in parents if dict(p).get("gender") == "Female"), parents[0] if parents else None)
            if pick is not None:
                mothers[r["childId"]] = add(pick)

        sibling_ids = [sid for sid in (add(r["s"]) for r in siblings) if sid]
        partner_ids = [pid for pid in (add(r["pt"]) for r in partners) if pid]

        # focus 기준 큐레이션 정본 role(맏아들·둘째 아들 등) — 있으면 프론트가 gender 폴백 대신 표시.
        # theographic_id로 조회(task#263) — nameKo로 조회하면 동명이인 노드에 role이 잘못 유출된다.
        pairs = _family_role_pairs()
        roles = {}
        for nid in nodes:
            if nid == node_id:
                continue
            role = pairs.get(frozenset({nid, node_id}), {}).get(nid)
            if role:
                roles[nid] = role

        return JSONResponse(
            content={
                "focus": node_id,
                "nodes": list(nodes.values()),
                "parentEdges": edges,
                "siblings": sibling_ids,
                "partners": partner_ids,
                "mothers": mothers,
                "roles": roles,
            },
            headers={"Cache-Control": "max-age=300"},
        )
