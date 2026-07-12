"""GET /person/{id}/family — 인물 중심(ego-centric) 가계도 서브그래프.

조상선(위, 뿌리까지) + 자손(아래 2세대) + focus의 직계 형제·배우자를 반환한다.
프론트는 parentEdges를 focus에서 위/아래로 걸어 세대별 트리를 구성한다.

응답:
  focus:       요청 인물 id (그대로 에코)
  nodes:       서브그래프의 모든 Person [{id, name, nameKo, authored}]
  parentEdges: [[parentId, childId], ...] — 조상 트리 + 자손 2세대의 PARENT_OF 간선
  siblings:    focus의 직계 형제 id 목록
  partners:    focus의 직계 배우자 id 목록
존재하지 않는 인물 id는 빈 서브그래프로 폴백한다(404 아님).
"""
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..db import get_driver

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_GENERATIONS = 100  # 조상선 상한 (아담→예수 ~76대 여유)


def _node(p) -> dict:
    props = dict(p)
    name = props.get("name") or props.get("title", "")
    name_ko = props.get("nameKo")
    return {
        "id": props.get("theographic_id", ""),
        "name": name,
        "nameKo": name_ko if name_ko else name,
        "authored": bool(props.get("authored")),
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

        sibling_ids = [sid for sid in (add(r["s"]) for r in siblings) if sid]
        partner_ids = [pid for pid in (add(r["pt"]) for r in partners) if pid]

        return JSONResponse(
            content={
                "focus": node_id,
                "nodes": list(nodes.values()),
                "parentEdges": edges,
                "siblings": sibling_ids,
                "partners": partner_ids,
            },
            headers={"Cache-Control": "max-age=300"},
        )
