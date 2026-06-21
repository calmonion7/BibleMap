import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { convexHull } from './convexHull'
import { apiGet } from './api'
import { MOBILE_BREAKPOINT, SHEET_VH } from './constants'

const EMPTY_GEOJSON = { type: 'FeatureCollection', features: [] }

function placePopupHTML(label, isPrimary) {
  const typeLabel = isPrimary ? '📍 선택된 장소' : '📍 관련 장소'
  return `
    <div style="
      font-family: system-ui, -apple-system, sans-serif;
      padding: 4px 2px;
    ">
      <div style="
        font-size: 15px;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 4px;
      ">${label}</div>
      <div style="
        font-size: 11px;
        color: #7c8db0;
        letter-spacing: 0.3px;
      ">${typeLabel}</div>
    </div>
  `
}

function registerEventHandlers(map, { collapseRing, collapseSpider, expandPlace, spiderifyPlaces, onSelectNode, popupRef, expandedPlaceRef }) {
  map.on('click', 'places-circle', (e) => {
    const overlapping = map.queryRenderedFeatures(e.point, { layers: ['places-circle'] })
    if (overlapping.length > 1) {
      spiderifyPlaces(overlapping, e.lngLat)
      return
    }

    collapseSpider()
    const { id, label, isPrimary } = e.features[0].properties
    const coords = e.features[0].geometry.coordinates.slice()

    if (expandedPlaceRef.current?.id === id) {
      collapseRing()
      return
    }

    expandPlace(id, coords[0], coords[1])

    if (popupRef.current) popupRef.current.remove()
    const popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      maxWidth: '220px',
      offset: 14,
    })
      .setLngLat(coords)
      .setHTML(placePopupHTML(label, isPrimary))
      .addTo(map)
    popupRef.current = popup
    if (id) onSelectNode(id)
  })

  map.on('mouseenter', 'places-circle', () => {
    map.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', 'places-circle', () => {
    map.getCanvas().style.cursor = ''
  })

  map.on('click', 'place-spider-circle', (e) => {
    const { id, label, isPrimary, originalLng, originalLat } = e.features[0].properties
    collapseSpider()
    expandPlace(id, originalLng, originalLat)
    if (popupRef.current) popupRef.current.remove()
    const popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      maxWidth: '220px',
      offset: 14,
    })
      .setLngLat([originalLng, originalLat])
      .setHTML(placePopupHTML(label, isPrimary))
      .addTo(map)
    popupRef.current = popup
    if (id) onSelectNode(id)
  })

  map.on('mouseenter', 'place-spider-circle', () => {
    map.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', 'place-spider-circle', () => {
    map.getCanvas().style.cursor = ''
  })

  map.on('click', 'places-cluster', (e) => {
    const [feature] = e.features
    const zoom = map.getSource('places-source').getClusterExpansionZoom(feature.properties.cluster_id)
    if (zoom) map.easeTo({ center: feature.geometry.coordinates, zoom, duration: 400 })
  })

  map.on('mouseenter', 'places-cluster', () => {
    map.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', 'places-cluster', () => {
    map.getCanvas().style.cursor = ''
  })

  map.on('click', 'event-ring-circle', (e) => {
    const { id } = e.features[0].properties
    if (id) onSelectNode(id)
  })

  map.on('mouseenter', 'event-ring-circle', () => {
    map.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', 'event-ring-circle', () => {
    map.getCanvas().style.cursor = ''
  })

  map.on('click', (e) => {
    const placeFeatures = map.queryRenderedFeatures(e.point, { layers: ['places-circle'] })
    const eventFeatures = map.queryRenderedFeatures(e.point, { layers: ['event-ring-circle'] })
    const spiderFeatures = map.queryRenderedFeatures(e.point, { layers: ['place-spider-circle'] })
    if (!placeFeatures.length && !eventFeatures.length && !spiderFeatures.length) {
      collapseRing()
      collapseSpider()
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
    }
  })
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
function ringLabels(lat, n) {
  const cosLat = Math.cos(lat * Math.PI / 180) || 1
  return Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI / n) * i - Math.PI / 2
    return outwardLabel(Math.cos(angle), Math.sin(angle) / cosLat)
  })
}

function placesToGeoJSON(places) {
  const cosLat = Math.cos((places[0]?.lat ?? 0) * Math.PI / 180) || 1
  return {
    type: 'FeatureCollection',
    features: places.map((p) => {
      // 최근접 이웃 반대쪽으로 라벨을 민다(화면 세로 cos(lat) 보정). 이웃 없으면 기본 우측.
      let best = null, bestD = Infinity
      for (const q of places) {
        if (q === p) continue
        const dx = q.lng - p.lng, dy = (q.lat - p.lat) / cosLat
        const d = dx * dx + dy * dy
        if (d < bestD) { bestD = d; best = q }
      }
      const { anchor, offset } = best
        ? outwardLabel(p.lng - best.lng, (p.lat - best.lat) / cosLat)
        : { anchor: 'left', offset: [1.2, 0] }
      return {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
        properties: { id: p.id, label: p.nameKo, isPrimary: p.isPrimary, anchor, offset },
      }
    }),
  }
}

function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }

function ringPositions(lng, lat, n, R) {
  return Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI / n) * i - Math.PI / 2
    return [lng + R * Math.cos(angle), lat + R * Math.sin(angle)]
  })
}

function buildEventGeoJSON(events, positions, anchors) {
  return {
    type: 'FeatureCollection',
    features: events.map((ev, i) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: positions[i] },
      properties: { id: ev.id, label: ev.nameKo || ev.name, anchor: anchors[i].anchor, offset: anchors[i].offset },
    })),
  }
}

function buildSpiderGeoJSON(features, positions, anchors) {
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

function setupMapSources(map) {
  // Hull polygon layers — added first so they render under all markers
  map.addSource('hull-source', { type: 'geojson', data: EMPTY_GEOJSON })
  map.addLayer({ id: 'hull-fill', type: 'fill', source: 'hull-source', paint: { 'fill-color': '#f97316', 'fill-opacity': 0.12 } })
  map.addLayer({ id: 'hull-outline', type: 'line', source: 'hull-source', paint: { 'line-color': '#f97316', 'line-opacity': 0.8, 'line-width': 5, 'line-dasharray': [1, 0] } })

  map.addSource('places-source', {
    type: 'geojson',
    data: EMPTY_GEOJSON,
    cluster: true,
    clusterMaxZoom: 13,
    clusterRadius: 40,
  })

  map.addLayer({
    id: 'places-circle-shadow',
    type: 'circle',
    source: 'places-source',
    filter: ['!', ['has', 'point_count']],
    paint: {
      'circle-radius': ['case', ['==', ['get', 'isPrimary'], true], 14, 11],
      'circle-color': 'rgba(0,0,0,0.2)',
      'circle-translate': [1, 2],
    },
  })

  map.addLayer({
    id: 'places-circle',
    type: 'circle',
    source: 'places-source',
    filter: ['!', ['has', 'point_count']],
    paint: {
      'circle-radius': ['case', ['==', ['get', 'isPrimary'], true], 11, 8],
      'circle-color': ['case', ['==', ['get', 'isPrimary'], true], '#f5a623', '#4a90d9'],
      'circle-stroke-width': 2.5,
      'circle-stroke-color': '#ffffff',
    },
  })

  map.addLayer({
    id: 'places-label',
    type: 'symbol',
    source: 'places-source',
    filter: ['!', ['has', 'point_count']],
    layout: {
      'text-field': ['get', 'label'],
      'text-font': ['Noto Sans Regular'],
      'text-size': 13,
      'text-anchor': ['get', 'anchor'],
      'text-offset': ['get', 'offset'],
      'text-justify': 'auto',
      'text-allow-overlap': false,
      'text-ignore-placement': false,
      'text-padding': 4,
    },
    paint: {
      'text-color': '#1a1a2e',
      'text-halo-color': 'rgba(255,255,255,0.95)',
      'text-halo-width': 2,
      'text-halo-blur': 0.5,
    },
  })

  map.addLayer({
    id: 'places-cluster',
    type: 'circle',
    source: 'places-source',
    filter: ['has', 'point_count'],
    paint: {
      'circle-radius': ['step', ['get', 'point_count'], 16, 5, 22, 10, 28],
      'circle-color': '#64748b',
      'circle-stroke-width': 2.5,
      'circle-stroke-color': '#ffffff',
    },
  })

  map.addLayer({
    id: 'places-cluster-count',
    type: 'symbol',
    source: 'places-source',
    filter: ['has', 'point_count'],
    layout: {
      'text-field': ['get', 'point_count_abbreviated'],
      'text-font': ['Noto Sans Regular'],
      'text-size': 13,
    },
    paint: { 'text-color': '#ffffff' },
  })

  map.addSource('place-spider-source', { type: 'geojson', data: EMPTY_GEOJSON })

  map.addLayer({
    id: 'place-spider-circle-shadow',
    type: 'circle',
    source: 'place-spider-source',
    paint: {
      'circle-radius': ['case', ['==', ['get', 'isPrimary'], true], 14, 11],
      'circle-color': 'rgba(0,0,0,0.2)',
      'circle-translate': [1, 2],
    },
  })

  map.addLayer({
    id: 'place-spider-circle',
    type: 'circle',
    source: 'place-spider-source',
    paint: {
      'circle-radius': ['case', ['==', ['get', 'isPrimary'], true], 11, 8],
      'circle-color': ['case', ['==', ['get', 'isPrimary'], true], '#f5a623', '#4a90d9'],
      'circle-stroke-width': 2.5,
      'circle-stroke-color': '#ffffff',
    },
  })

  map.addLayer({
    id: 'place-spider-label',
    type: 'symbol',
    source: 'place-spider-source',
    layout: {
      'text-field': ['get', 'label'],
      'text-font': ['Noto Sans Regular'],
      'text-size': 13,
      'text-anchor': ['get', 'anchor'],
      'text-offset': ['get', 'offset'],
      'text-justify': 'auto',
      'text-allow-overlap': false,
      'text-ignore-placement': false,
      'text-padding': 4,
    },
    paint: {
      'text-color': '#1a1a2e',
      'text-halo-color': 'rgba(255,255,255,0.95)',
      'text-halo-width': 2,
      'text-halo-blur': 0.5,
    },
  })

  // 사건 링 레이어
  map.addSource('event-ring-source', { type: 'geojson', data: EMPTY_GEOJSON })

  map.addLayer({
    id: 'event-ring-shadow',
    type: 'circle',
    source: 'event-ring-source',
    paint: {
      'circle-radius': 12,
      'circle-color': 'rgba(0,0,0,0.2)',
      'circle-translate': [1, 2],
    },
  })

  map.addLayer({
    id: 'event-ring-circle',
    type: 'circle',
    source: 'event-ring-source',
    paint: {
      'circle-radius': 9,
      'circle-color': '#9b59b6',
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ffffff',
    },
  })

  map.addLayer({
    id: 'event-ring-label',
    type: 'symbol',
    source: 'event-ring-source',
    layout: {
      'text-field': ['get', 'label'],
      'text-font': ['Noto Sans Regular'],
      'text-size': 12,
      'text-anchor': ['get', 'anchor'],
      'text-offset': ['get', 'offset'],
      'text-justify': 'auto',
      'text-allow-overlap': false,
      'text-padding': 3,
    },
    paint: {
      'text-color': '#1a1a2e',
      'text-halo-color': 'rgba(255,255,255,0.95)',
      'text-halo-width': 2,
    },
  })
}

export default function MapView({ onSelectNode, selectedNode, isVisible }) {
  const mapContainer = useRef(null)
  const mapRef = useRef(null)
  const popupRef = useRef(null)
  // 사건 링 펼침 제어 — selection effect가 자동 펼침을 위해 공유한다.
  const expandPlaceRef = useRef(null)        // (placeId, lng, lat) => 링 fly-out
  const expandedPlaceRef = useRef(null)      // 현재 펼쳐진 장소 { id, lng, lat, events, targets }
  const [mapLoaded, setMapLoaded] = useState(false)
  const [error, setError] = useState(false)
  const [noLocation, setNoLocation] = useState(false) // 선택 노드의 /places가 빈 배열일 때 안내

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapContainer.current,
      center: [35.22, 31.78],
      zoom: 5,
      style: {
        version: 8,
        glyphs: 'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf',
        sources: {
          esri: {
            type: 'raster',
            tiles: [
              'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
            ],
            tileSize: 256,
          },
        },
        layers: [{ id: 'esri-layer', type: 'raster', source: 'esri' }],
      },
    })

    // 애니메이션 상태 (React state 아님 — 프레임마다 리렌더 없음)
    let animFrame = null
    let expandAbortCtrl = null
    const expandedPlace = expandedPlaceRef // 컴포넌트 ref와 공유 — selection effect가 펼침 상태를 읽는다
    expandedPlace.current = null            // 맵 재초기화 시 초기화
    let destroyed = false
    let spiderState = null
    let spiderAnimFrame = null

    function collapseSpider() {
      if (!spiderState) return
      if (spiderAnimFrame) { cancelAnimationFrame(spiderAnimFrame); spiderAnimFrame = null }
      const { lng, lat, features, targets, anchors } = spiderState
      spiderState = null
      const start = performance.now()
      const DURATION = 400
      function animate(now) {
        if (destroyed) return
        const t = Math.min((now - start) / DURATION, 1)
        const factor = 1 - easeOutCubic(t)
        const positions = targets.map(([tlng, tlat]) => [
          lng + (tlng - lng) * factor,
          lat + (tlat - lat) * factor,
        ])
        map.getSource('place-spider-source').setData(buildSpiderGeoJSON(features, positions, anchors))
        if (t < 1) {
          spiderAnimFrame = requestAnimationFrame(animate)
        } else {
          spiderAnimFrame = null
          map.getSource('place-spider-source').setData(EMPTY_GEOJSON)
        }
      }
      spiderAnimFrame = requestAnimationFrame(animate)
    }

    function spiderifyPlaces(features, lngLat) {
      collapseSpider()
      collapseRing()
      const { lng, lat } = lngLat
      const center = map.project([lng, lat])
      const edgePoint = map.unproject([center.x + 80, center.y])
      const R = Math.abs(edgePoint.lng - lng)
      const targets = ringPositions(lng, lat, features.length, R)
      const anchors = ringLabels(lat, features.length)
      spiderState = { lng, lat, features, targets, anchors }
      if (spiderAnimFrame) { cancelAnimationFrame(spiderAnimFrame); spiderAnimFrame = null }
      const start = performance.now()
      const DURATION = 400
      function animate(now) {
        if (destroyed) return
        const t = Math.min((now - start) / DURATION, 1)
        const factor = easeOutCubic(t)
        const positions = targets.map(([tlng, tlat]) => [
          lng + (tlng - lng) * factor,
          lat + (tlat - lat) * factor,
        ])
        map.getSource('place-spider-source').setData(buildSpiderGeoJSON(features, positions, anchors))
        if (t < 1) {
          spiderAnimFrame = requestAnimationFrame(animate)
        }
      }
      spiderAnimFrame = requestAnimationFrame(animate)
    }

    function collapseRing() {
      if (!expandedPlace.current) return
      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null }

      const { lng, lat, events, targets, anchors } = expandedPlace.current
      expandedPlace.current = null

      const start = performance.now()
      const DURATION = 400

      function animate(now) {
        if (destroyed) return
        const t = Math.min((now - start) / DURATION, 1)
        const factor = 1 - easeOutCubic(t) // 1→0: 링 위치 → 중심
        const positions = targets.map(([tlng, tlat]) => [
          lng + (tlng - lng) * factor,
          lat + (tlat - lat) * factor,
        ])
        map.getSource('event-ring-source').setData(buildEventGeoJSON(events, positions, anchors))
        if (t < 1) {
          animFrame = requestAnimationFrame(animate)
        } else {
          animFrame = null
          map.getSource('event-ring-source').setData(EMPTY_GEOJSON)
        }
      }
      animFrame = requestAnimationFrame(animate)
    }

    async function expandPlace(placeId, placeLng, placeLat) {
      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null }
      if (expandedPlace.current) {
        expandedPlace.current = null
        map.getSource('event-ring-source').setData(EMPTY_GEOJSON)
      }
      if (expandAbortCtrl) { expandAbortCtrl.abort(); expandAbortCtrl = null }
      expandAbortCtrl = new AbortController()
      const signal = expandAbortCtrl.signal

      let grouped
      try {
        grouped = await apiGet(`/node/${placeId}/neighbors/grouped`, { signal })
      } catch {
        return
      }

      if (destroyed) return

      const events = (grouped.Event || []).filter(ev => ev.id)
      if (!events.length) return

      // zoom-adaptive 링 반경: 화면 80px를 현재 zoom에서 degrees로 변환
      const center = map.project([placeLng, placeLat])
      const edgePoint = map.unproject([center.x + 80, center.y])
      const R = Math.abs(edgePoint.lng - placeLng)

      const targets = ringPositions(placeLng, placeLat, events.length, R)
      const anchors = ringLabels(placeLat, events.length)
      expandedPlace.current = { id: placeId, lng: placeLng, lat: placeLat, events, targets, anchors }

      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null }
      const start = performance.now()
      const DURATION = 400

      function animate(now) {
        if (destroyed) return
        const t = Math.min((now - start) / DURATION, 1)
        const factor = easeOutCubic(t) // 0→1: 중심 → 링 위치
        const positions = targets.map(([tlng, tlat]) => [
          placeLng + (tlng - placeLng) * factor,
          placeLat + (tlat - placeLat) * factor,
        ])
        map.getSource('event-ring-source').setData(buildEventGeoJSON(events, positions, anchors))
        if (t < 1) {
          animFrame = requestAnimationFrame(animate)
        } else {
          animFrame = null
        }
      }
      animFrame = requestAnimationFrame(animate)
    }

    expandPlaceRef.current = expandPlace

    map.on('load', () => {
      setupMapSources(map)
      registerEventHandlers(map, { collapseRing, collapseSpider, expandPlace, spiderifyPlaces, onSelectNode, popupRef, expandedPlaceRef })
      mapRef.current = map
      setMapLoaded(true)
    })

    return () => {
      destroyed = true
      if (animFrame) cancelAnimationFrame(animFrame)
      if (spiderAnimFrame) cancelAnimationFrame(spiderAnimFrame)
      if (expandAbortCtrl) expandAbortCtrl.abort()
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
      expandPlaceRef.current = null
      expandedPlace.current = null
      mapRef.current = null
      setMapLoaded(false)
      map.remove()
    }
  }, [onSelectNode])

  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return

    if (!selectedNode) {
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
      map.getSource('places-source').setData(EMPTY_GEOJSON)
      map.getSource('hull-source').setData(EMPTY_GEOJSON)
      return
    }

    const ctrl = new AbortController()
    let moveEndHandler = null
    let autoExpandTimer = null

    apiGet(`/node/${selectedNode}/places`, { signal: ctrl.signal })
      .then(({ label, places }) => {
        if (mapRef.current !== map) return
        setError(false)
        setNoLocation(places.length === 0) // 위치 없는 노드면 안내, 있으면 해제 (async 콜백 — v7 OK)
        map.getSource('places-source').setData(placesToGeoJSON(places))

        // Hull polygon — Person이고 3개 이상 장소일 때만 표시
        if (label === 'Person' && places.length >= 3) {
          const pts = convexHull(places.map(p => ({ lng: p.lng, lat: p.lat })))
          if (pts.length >= 3) {
            const ring = [...pts.map(p => [p.lng, p.lat]), [pts[0].lng, pts[0].lat]]
            map.getSource('hull-source').setData({
              type: 'FeatureCollection',
              features: [{ type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] }, properties: {} }],
            })
          } else {
            map.getSource('hull-source').setData(EMPTY_GEOJSON)
          }
        } else {
          map.getSource('hull-source').setData(EMPTY_GEOJSON)
        }

        if (places.length === 0) return

        const bounds = places.reduce(
          (b, p) => b.extend([p.lng, p.lat]),
          new maplibregl.LngLatBounds([places[0].lng, places[0].lat], [places[0].lng, places[0].lat])
        )

        // 선택한 장소(isPrimary)의 사건 링을 펼친다.
        // 마커 클릭 경로는 클릭 핸들러에서 이미 "현재 줌"으로 링을 펼쳐 둔다(expandedPlace 선점).
        // 그 경우 여기서 카메라를 건드리지 않는다 → 클릭 시 줌이 튀지 않고 링이 그 자리에서 보인다.
        // 링 반경 R은 표시 줌에서 80px(고정 화면 반경)이라, 장소 점만 보이면 링도 자동으로 보인다.
        // 아직 안 펼친 primary(=검색·사이드패널 선택)만 적당한 줌으로 가져온 뒤 "정착된 줌"에서
        // 펼친다(R을 정착 줌에서 계산해야 화면 밖으로 안 날아간다 — task 15에서 어긋났던 지점).
        // 인물/집단 선택은 isPrimary가 없으므로 전체 장소만 한눈에 보여준다(기존 거동).
        const isMobile = window.innerWidth <= MOBILE_BREAKPOINT
        const sheet = Math.round(window.innerHeight * (SHEET_VH / 100))
        const primary = places.find((p) => p.isPrimary)

        if (primary && expandedPlaceRef.current?.id !== primary.id) {
          // 검색·사이드패널 선택 — 화면 밖일 수 있으니 적당한 줌으로 가져온 뒤 정착 후 펼침.
          // moveend는 카메라가 안 움직이면 미발화하므로 폴백 타이머(700ms)로 보장, fired로 단발.
          // (공유 source 동시 setData 충돌 회피 — radial-ring 회고)
          let fired = false
          const runExpand = () => {
            if (fired) return
            fired = true
            if (autoExpandTimer) { clearTimeout(autoExpandTimer); autoExpandTimer = null }
            if (moveEndHandler) { map.off('moveend', moveEndHandler); moveEndHandler = null }
            if (mapRef.current === map && expandedPlaceRef.current?.id !== primary.id) {
              expandPlaceRef.current?.(primary.id, primary.lng, primary.lat)
            }
          }
          moveEndHandler = runExpand
          map.once('moveend', moveEndHandler)
          autoExpandTimer = setTimeout(runExpand, 700)
          // 링(반경 ~80px)+라벨(오른쪽으로 뻗음) 여유 패딩 + 단일 장소 과도 확대 방지(maxZoom 7).
          const padding = isMobile
            ? { top: 100, bottom: sheet + 120, left: 90, right: 120 }
            : 140
          map.fitBounds(bounds, { padding, maxZoom: 7, duration: 600 })
        } else if (!primary) {
          // 인물/집단 — 전체 장소를 한눈에. 모바일은 하단 시트/상단 네비만큼 패딩.
          const padding = isMobile
            ? { top: 70, bottom: sheet + 20, left: 40, right: 40 }
            : 80
          map.fitBounds(bounds, { padding, maxZoom: 10, duration: 600 })
        }
        // primary가 이미 펼쳐져 있으면(마커 클릭으로 현재 줌에서 펼친 경우) 카메라를 건드리지 않는다.
      })
      .catch((e) => {
        if (e?.name !== 'AbortError' && mapRef.current === map) { setError(true); setNoLocation(false) }
      })

    return () => {
      ctrl.abort()
      if (moveEndHandler) map.off('moveend', moveEndHandler)
      if (autoExpandTimer) clearTimeout(autoExpandTimer)
    }
  }, [selectedNode, mapLoaded])

  useEffect(() => {
    if (isVisible && mapRef.current) mapRef.current.resize()
  }, [isVisible])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      {error && selectedNode && (
        <div style={{
          position: 'absolute', top: 60, left: '50%', transform: 'translateX(-50%)', // 플로팅 nav(48px) 아래
          background: 'rgba(220,53,69,0.95)', color: 'white',
          padding: '8px 16px', borderRadius: 8, fontSize: 13, zIndex: 10,
          boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
        }}>
          장소를 불러오지 못했습니다
        </div>
      )}
      {noLocation && selectedNode && (
        <div style={{
          position: 'absolute', top: 60, left: '50%', transform: 'translateX(-50%)', // 플로팅 nav(48px) 아래
          background: 'rgba(30,32,64,0.92)', color: 'white',
          padding: '8px 16px', borderRadius: 8, fontSize: 13, zIndex: 10,
          maxWidth: '82%', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
        }}>
          이 항목은 지도에 표시할 위치 정보가 없습니다 — 그래프·타임라인에서 살펴보세요
        </div>
      )}
    </div>
  )
}
