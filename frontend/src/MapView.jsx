import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  const [mapLoaded, setMapLoaded] = useState(false)
  const [error, setError] = useState(false)

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
    const expandedPlace = { current: null } // { id, lng, lat, events, targets }
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
        const res = await fetch(`${API_URL}/node/${placeId}/neighbors/grouped`, { signal })
        if (!res.ok) return
        grouped = await res.json()
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

    map.on('load', () => {
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
      return
    }

    const ctrl = new AbortController()

    fetch(`${API_URL}/node/${selectedNode}/places`, { signal: ctrl.signal })
      .then((res) => res.ok ? res.json() : Promise.reject(res.status))
      .then((places) => {
        if (mapRef.current === map) {
          setError(false)
          map.getSource('places-source').setData(placesToGeoJSON(places))
          if (places.length > 0) {
            const bounds = places.reduce(
              (b, p) => b.extend([p.lng, p.lat]),
              new maplibregl.LngLatBounds([places[0].lng, places[0].lat], [places[0].lng, places[0].lat])
            )
            // 모바일은 하단 시트(App.jsx SHEET_VH=55vh)와 상단 네비가 지도를 가리므로,
            // 가려진 만큼 패딩을 더해 마커가 보이는 상단 띠 영역에 들어오게 한다. (0.55는 SHEET_VH와 일치)
            const isMobile = window.innerWidth <= 768
            const padding = isMobile
              ? { top: 70, bottom: Math.round(window.innerHeight * 0.55) + 20, left: 40, right: 40 }
              : 80
            map.fitBounds(bounds, { padding, maxZoom: 10, duration: 600 })
          }
        }
      })
      .catch((e) => {
        if (e?.name !== 'AbortError' && mapRef.current === map) setError(true)
      })

    return () => ctrl.abort()
  }, [selectedNode, mapLoaded])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      {error && selectedNode && (
        <div style={{
          position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(220,53,69,0.95)', color: 'white',
          padding: '8px 16px', borderRadius: 8, fontSize: 13, zIndex: 10,
          boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
        }}>
          장소를 불러오지 못했습니다
        </div>
      )}
    </div>
  )
}
