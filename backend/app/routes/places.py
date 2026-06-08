from fastapi import APIRouter
from ..db import get_driver

router = APIRouter()

@router.get("/places")
def get_places():
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (p:Place) WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL RETURN p"
        )
        places = []
        for record in result:
            p = record["p"]
            props = dict(p)
            name = props.get("name", "")
            name_ko = props.get("nameKo")
            places.append({
                "id": props.get("theographic_id", ""),
                "name": name,
                "nameKo": name_ko if name_ko else name,
                "nameKoMissing": name_ko is None,
                "lat": float(props.get("latitude", 0)),
                "lng": float(props.get("longitude", 0)),
            })
        return places
