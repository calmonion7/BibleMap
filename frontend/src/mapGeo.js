import maplibregl from 'maplibre-gl'

// 인물/집단 프레이밍용 — 원거리 outlier 장소(예: 모세-홍해)를 fitBounds 범위에서 제외한 core bounds.
// median 중심에서의 거리 중앙값×K(튜닝값)를 임계로 — 밀집 클러스터(medD≈0)는 제외 0 → null 반환(호출 측이 전체 bounds 폴백).
export function coreBounds(places) {
  if (places.length < 4) return null
  const med = (arr) => { const s = [...arr].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2 }
  const mlng = med(places.map((p) => p.lng)), mlat = med(places.map((p) => p.lat))
  const dist = (p) => Math.hypot(p.lng - mlng, p.lat - mlat)
  const medD = med(places.map(dist))
  if (medD < 0.01) return null // 거의 한 점에 모임 — 프레이밍 문제 없음
  const core = places.filter((p) => dist(p) <= medD * 3)
  if (core.length < 2 || core.length === places.length) return null // 제외 없음 → 전체 bounds
  return core.reduce((b, p) => b.extend([p.lng, p.lat]), new maplibregl.LngLatBounds([core[0].lng, core[0].lat], [core[0].lng, core[0].lat]))
}

// 라벨을 바깥 방향(이웃/링 중심 반대)으로 — 화면 기준 8방위 text-anchor + text-offset.
// ex: 동(+)/서(-) 화면 우측 성분, ny: 북(+)/남(-) 화면 상단 성분(호출 측에서 cos(lat) 보정).
function outwardLabel(ex, ny) {
  const ax = Math.abs(ex), ay = Math.abs(ny)
  const O = 1.2
  const h = ex >= 0 ? 'left' : 'right'   // 'left' 앵커 = 텍스트가 점 오른쪽
  const v = ny >= 0 ? 'bottom' : 'top'   // 'bottom' 앵커 = 텍스트가 점 위쪽
  const ox = ex >= 0 ? O : -O
  const oy = ny >= 0 ? -O : O            // 북(위) → text-offset 음수 y(위로)
  const RATIO = 2.5
  if (ax >= ay * RATIO) return { anchor: h, offset: [ox, 0] }      // 거의 수평
  if (ay >= ax * RATIO) return { anchor: v, offset: [0, oy] }      // 거의 수직
  return { anchor: `${v}-${h}`, offset: [ox * 0.85, oy * 0.85] }   // 대각
}

// 링 배치 라벨 — 링 중심에서 바깥(방사) 방향. lng 기준 R로 그린 링은 화면상 세로로 늘어나므로 sin을 cos(lat)로 보정.
export function ringLabels(lat, n) {
  const cosLat = Math.cos(lat * Math.PI / 180)
  return Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI / n) * i - Math.PI / 2
    return outwardLabel(Math.cos(angle), Math.sin(angle) / cosLat)
  })
}

export function placesToGeoJSON(places) {
  const cosLat = Math.cos((places[0]?.lat ?? 0) * Math.PI / 180)
  // 동일/근접 좌표 그룹(~1e-4° ≈ 11m) — 거리 0에서 outwardLabel이 퇴화(같은 앵커→충돌로 숨김)하므로
  // 그룹 내 라벨을 방사 배치(예: 호렙 위/시내산 아래). 단독 좌표는 기존 최근접-이웃 outward 유지.
  const coKey = (p) => `${p.lng.toFixed(4)},${p.lat.toFixed(4)}`
  const groups = new Map()
  for (const p of places) {
    const k = coKey(p)
    if (!groups.has(k)) groups.set(k, [])
    groups.get(k).push(p)
  }
  return {
    type: 'FeatureCollection',
    features: places.map((p) => {
      const group = groups.get(coKey(p))
      let anchor, offset
      if (group.length > 1) {
        // 동일좌표 그룹 — 방사 앵커로 분산(마커는 그대로 한 점, 라벨만 펼침)
        ;({ anchor, offset } = ringLabels(p.lat, group.length)[group.indexOf(p)])
      } else {
        // 단독 좌표 — 최근접 이웃 반대쪽으로 민다(화면 세로 cos(lat) 보정). 이웃 없으면 기본 우측.
        let best = null, bestD = Infinity
        for (const q of places) {
          if (q === p) continue
          const dx = q.lng - p.lng, dy = (q.lat - p.lat) / cosLat
          const d = dx * dx + dy * dy
          if (d < bestD) { bestD = d; best = q }
        }
        ;({ anchor, offset } = best
          ? outwardLabel(p.lng - best.lng, (p.lat - best.lat) / cosLat)
          : { anchor: 'left', offset: [1.2, 0] })
      }
      return {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
        properties: { id: p.id, label: p.nameKo, isPrimary: p.isPrimary, anchor, offset },
      }
    }),
  }
}

export function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }

export function ringPositions(lng, lat, n, R) {
  return Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI / n) * i - Math.PI / 2
    return [lng + R * Math.cos(angle), lat + R * Math.sin(angle)]
  })
}

export function buildEventGeoJSON(events, positions, anchors) {
  return {
    type: 'FeatureCollection',
    features: events.map((ev, i) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: positions[i] },
      properties: { id: ev.id, label: ev.nameKo || ev.name, anchor: anchors[i].anchor, offset: anchors[i].offset },
    })),
  }
}

export function buildSpiderGeoJSON(features, positions, anchors) {
  return {
    type: 'FeatureCollection',
    features: features.map((f, i) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: positions[i] },
      properties: {
        ...f.properties,
        originalLng: f.geometry.coordinates[0],
        originalLat: f.geometry.coordinates[1],
        anchor: anchors[i].anchor,
        offset: anchors[i].offset,
      },
    })),
  }
}
