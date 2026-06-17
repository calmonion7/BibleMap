import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { convexHull } from './convexHull'
import { apiGet } from './api'

const EMPTY_GEOJSON = { type: 'FeatureCollection', features: [] }

function placesToGeoJSON(places) {
  return {
    type: 'FeatureCollection',
    features: places.map((p) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
      properties: { id: p.id, label: p.nameKo, isPrimary: p.isPrimary },
    })),
  }
}

export default function MapView({ onSelectNode, selectedNode }) {
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

    function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }

    function ringPositions(lng, lat, n, R) {
      return Array.from({ length: n }, (_, i) => {
        const angle = (2 * Math.PI / n) * i - Math.PI / 2
        return [lng + R * Math.cos(angle), lat + R * Math.sin(angle)]
      })
    }

    function buildEventGeoJSON(events, positions) {
      return {
        type: 'FeatureCollection',
        features: events.map((ev, i) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: positions[i] },
          properties: { id: ev.id, label: ev.nameKo || ev.name },
        })),
      }
    }

    function collapseRing() {
      if (!expandedPlace.current) return
      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null }

      const { lng, lat, events, targets } = expandedPlace.current
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
        map.getSource('event-ring-source').setData(buildEventGeoJSON(events, positions))
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
      if (expandAbortCtrl) expandAbortCtrl.abort()
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
      expandedPlace.current = { id: placeId, lng: placeLng, lat: placeLat, events, targets }

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
        map.getSource('event-ring-source').setData(buildEventGeoJSON(events, positions))
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
      // Hull polygon layers — added first so they render under all markers
      map.addSource('hull-source', { type: 'geojson', data: EMPTY_GEOJSON })
      map.addLayer({ id: 'hull-fill', type: 'fill', source: 'hull-source', paint: { 'fill-color': '#f97316', 'fill-opacity': 0.12 } })
      map.addLayer({ id: 'hull-outline', type: 'line', source: 'hull-source', paint: { 'line-color': '#f97316', 'line-opacity': 0.8, 'line-width': 5, 'line-dasharray': [1, 0] } })

      map.addSource('places-source', { type: 'geojson', data: EMPTY_GEOJSON })

      map.addLayer({
        id: 'places-circle-shadow',
        type: 'circle',
        source: 'places-source',
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
        layout: {
          'text-field': ['get', 'label'],
          'text-font': ['Noto Sans Regular'],
          'text-size': 13,
          'text-anchor': 'left',
          'text-offset': [1.2, 0],
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
          'text-anchor': 'left',
          'text-offset': [1.0, 0],
          'text-allow-overlap': false,
          'text-padding': 3,
        },
        paint: {
          'text-color': '#1a1a2e',
          'text-halo-color': 'rgba(255,255,255,0.95)',
          'text-halo-width': 2,
        },
      })

      map.on('click', 'places-circle', (e) => {
        const { id, label, isPrimary } = e.features[0].properties
        const coords = e.features[0].geometry.coordinates.slice()

        if (expandedPlace.current?.id === id) {
          // 같은 장소 재클릭 → 링 접힘
          collapseRing()
          return
        }

        // 다른 장소 클릭 → 기존 링 즉시 제거 후 새 링 펼침
        if (expandAbortCtrl) { expandAbortCtrl.abort(); expandAbortCtrl = null }
        if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null }
        if (expandedPlace.current) {
          expandedPlace.current = null
          map.getSource('event-ring-source').setData(EMPTY_GEOJSON)
        }

        expandPlace(id, coords[0], coords[1])

        if (popupRef.current) popupRef.current.remove()

        const typeLabel = isPrimary ? '📍 선택된 장소' : '📍 관련 장소'

        const popup = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: false,
          maxWidth: '220px',
          offset: 14,
        })
          .setLngLat(coords)
          .setHTML(`
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
          `)
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

      // 사건 버블 클릭 → 사건 상세로 이동, 링 유지
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
        if (!placeFeatures.length && !eventFeatures.length) {
          collapseRing()
          if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
        }
      })

      mapRef.current = map
      setMapLoaded(true)
    })

    return () => {
      destroyed = true
      if (animFrame) cancelAnimationFrame(animFrame)
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
        const isMobile = window.innerWidth <= 768
        const sheet = Math.round(window.innerHeight * 0.55) // App.jsx SHEET_VH=55vh와 일치
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
