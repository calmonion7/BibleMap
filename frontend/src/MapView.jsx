import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { apiGet } from './api'
import { MOBILE_BREAKPOINT, SHEET_VH } from './constants'
import { coreBounds, placesToGeoJSON, buildJourneyLineGeoJSON, buildJourneyStopsGeoJSON } from './mapGeo'
import { EMPTY_GEOJSON, registerEventHandlers, setupMapSources } from './mapLayers'
import { createRingController } from './mapRingController'

export default function MapView({ onSelectNode, selectedNode, personId, isVisible, journeyStops, activeStopIdx, onStopSelect }) {
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

    const ring = createRingController(map, { expandedPlaceRef, setError })
    expandPlaceRef.current = ring.expandPlace

    map.on('load', () => {
      setupMapSources(map)
      registerEventHandlers(map, { ...ring, onSelectNode, popupRef, expandedPlaceRef, onJourneyStopClick: onStopSelect })
      mapRef.current = map
      setMapLoaded(true)
    })

    return () => {
      ring.destroy()
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
      expandPlaceRef.current = null
      expandedPlaceRef.current = null
      mapRef.current = null
      setMapLoaded(false)
      map.remove()
    }
  }, [onSelectNode])

  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return

    // personId가 있으면 인물 기준 장소 fetch(장소 클릭으로 selectedNode가 바뀌어도 맵 장소 유지).
    // personId 없으면 selectedNode 기준 기존 거동.
    const fetchId = personId ?? selectedNode

    if (!fetchId) {
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
      map.getSource('places-source').setData(EMPTY_GEOJSON)
      return
    }

    const ctrl = new AbortController()
    let moveEndHandler = null
    let autoExpandTimer = null

    apiGet(`/node/${fetchId}/places`, { signal: ctrl.signal })
      .then(({ places }) => {
        if (mapRef.current !== map) return
        setError(false)
        // personId로 탐험 중이면 noLocation 안내 생략(맵 장소는 인물 기준으로 항상 있음)
        setNoLocation(!personId && places.length === 0) // async 콜백 — v7 OK
        map.getSource('places-source').setData(placesToGeoJSON(places))

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
        // personId 탐험 중: selectedNode가 Place면 그 장소를 primary로 강조, 아니면 isPrimary 폴백
        const primary = personId
          ? (places.find((p) => p.id === selectedNode) || places.find((p) => p.isPrimary))
          : places.find((p) => p.isPrimary)

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
          // outlier(원거리 장소)는 프레이밍에서 제외 — 근접 무리가 뭉치지 않게(마커는 그대로 렌더).
          map.fitBounds(coreBounds(places) || bounds, { padding, maxZoom: 10, duration: 600 })
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
  }, [personId, selectedNode, mapLoaded])

  // 여정선 + 정차지 배지 업데이트 (stops prop 변경 시)
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return
    const stops = journeyStops ?? []
    map.getSource('journey-line-source').setData(buildJourneyLineGeoJSON(stops))
    map.getSource('journey-stops-source').setData(buildJourneyStopsGeoJSON(stops))
    map.getSource('journey-active-source').setData(EMPTY_GEOJSON) // 새 인물 선택 시 강조 초기화
  }, [journeyStops, mapLoaded])

  // 활성 정차지 강조 + 카메라 이동 (activeStopIdx prop 변경 시)
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return
    if (activeStopIdx == null || !journeyStops) {
      map.getSource('journey-active-source').setData(EMPTY_GEOJSON)
      return
    }
    // stops 중 좌표 있는 것만 배지에 표시 → 동일 좌표 전체중복 제거한 deduped 기준 인덱스
    // buildJourneyStopsGeoJSON와 동일 로직으로 deduped 배열 재구성
    const withCoord = journeyStops.filter((s) => s.lng != null && s.lat != null)
    const coKey = (s) => `${s.lng},${s.lat}`
    const seen = []
    const dedupedMap = new Map()
    for (const s of withCoord) {
      const k = coKey(s)
      if (!dedupedMap.has(k)) seen.push(k)
      dedupedMap.set(k, s)
    }
    const deduped = seen.map((k) => dedupedMap.get(k))
    const stop = deduped[activeStopIdx]
    if (!stop) {
      map.getSource('journey-active-source').setData(EMPTY_GEOJSON)
      return
    }
    map.getSource('journey-active-source').setData({
      type: 'FeatureCollection',
      features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [stop.lng, stop.lat] }, properties: {} }],
    })
    map.easeTo({ center: [stop.lng, stop.lat], duration: 400 })
  }, [activeStopIdx, mapLoaded, journeyStops])

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
