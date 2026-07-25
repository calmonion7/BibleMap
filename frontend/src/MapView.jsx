import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { apiGet } from './api'
import { MOBILE_BREAKPOINT, SHEET_VH, JOURNEY_SHEET_VH } from './constants'
import { coreBounds, placesToGeoJSON, buildJourneyLineGeoJSON, buildJourneyStopsGeoJSON, journeyStopGroups, buildParablesMiraclesGeoJSON } from './mapGeo'
import { EMPTY_GEOJSON, registerEventHandlers, setupMapSources } from './mapLayers'
import { createRingController } from './mapRingController'
import { PM_TYPE_COLOR } from './theme'

// 비유·기적 필터 칩(task#249) — 지도 토글·연표 섹션(TimelineView)이 동일 순서·라벨 공유.
const PM_FILTERS = [['all', '전체'], ['parable', '비유'], ['miracle', '기적']]

// fitBounds 패딩 합이 컨테이너 실효 크기를 넘으면 maplibre가 bounds를 못 맞춰 줌을 최소로
// 클램프한다(모바일에서 지도가 성지 대신 세계축소 뷰로 튀던 선재 버그, task#251). 각 축 패딩 합을
// 컨테이너 크기의 60% 이내로 제한해 최소 40% 가시영역을 남긴다. 데스크톱(큰 컨테이너)에선 무변화.
function clampPadding(map, padding) {
  const c = map.getContainer()
  const w = c.clientWidth, h = c.clientHeight
  const p = typeof padding === 'number'
    ? { top: padding, bottom: padding, left: padding, right: padding }
    : { top: 0, bottom: 0, left: 0, right: 0, ...padding }
  const capAxis = (a, b, size) => {
    const max = size * 0.6
    const sum = a + b
    if (!size || sum <= max || sum === 0) return [a, b]
    const k = max / sum
    return [Math.round(a * k), Math.round(b * k)]
  }
  const [top, bottom] = capAxis(p.top, p.bottom, h)
  const [left, right] = capAxis(p.left, p.right, w)
  return { top, bottom, left, right }
}

export default function MapView({ onSelectNode, selectedNode, personId, pmEnabled = false, isVisible, journeyStops, activeStopIdx, onStopSelect, playbackIdx = null }) {
  const mapContainer = useRef(null)
  const mapRef = useRef(null)
  const popupRef = useRef(null)
  const pmPopupRef = useRef(null) // 비유·기적 팝업 — popupRef와 분리(생명주기가 달라 outside-click 정리도 별도)
  // 사건 링 펼침 제어 — selection effect가 자동 펼침을 위해 공유한다.
  const expandPlaceRef = useRef(null)        // (placeId, lng, lat) => 링 fly-out
  const expandedPlaceRef = useRef(null)      // 현재 펼쳐진 장소 { id, lng, lat, events, targets }
  const [mapLoaded, setMapLoaded] = useState(false)
  const [error, setError] = useState(false)
  const [noLocation, setNoLocation] = useState(false) // 선택 노드의 /places가 빈 배열일 때 안내
  // 비유·기적 색인 레이어(task#249) — 인물/투어 선택과 무관하게 1회 fetch, 토글로 켜고 종류로 거른다.
  const [pmItems, setPmItems] = useState([])
  const [pmVisible, setPmVisible] = useState(false)
  const [pmFilter, setPmFilter] = useState('all')

  useEffect(() => {
    apiGet('/parables-miracles')
      .then(setPmItems)
      .catch(e => { console.warn('[MapView] 비유·기적 로드 실패', e); setPmItems([]) })
  }, [])

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
            // NatGeo 현대 지도 유지 — 무라벨 지형(World_Terrain_Base)으로 바꿨다가 실사용 피드백으로 원복:
            // 현대 지도와 대비해 보는 것이 성경 지리 이해에 더 낫다(ADR-0013 지도 조항 개정판 참조)
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
      registerEventHandlers(map, { ...ring, onSelectNode, popupRef, expandedPlaceRef, onJourneyStopClick: onStopSelect, pmPopupRef })
      // 컨테이너 실효 크기로 캔버스 동기화 — 모바일 최초 진입 시 캔버스가 미확정 크기로 생성돼
      // fitBounds가 세계축소로 클램프되던 문제 방지(task#251). setMapLoaded 전에 호출해 프레이밍 effect보다 선행.
      map.resize()
      mapRef.current = map
      setMapLoaded(true)
    })

    return () => {
      ring.destroy()
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
      if (pmPopupRef.current) { pmPopupRef.current.remove(); pmPopupRef.current = null }
      expandPlaceRef.current = null
      expandedPlaceRef.current = null
      mapRef.current = null
      setMapLoaded(false)
      map.remove()
    }
  }, [onSelectNode, onStopSelect])

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
          map.fitBounds(bounds, { padding: clampPadding(map, padding), maxZoom: 7, duration: 600 })
        } else if (!primary) {
          // 인물/집단 — 전체 장소를 한눈에. 모바일은 하단 시트/상단 네비만큼 패딩.
          const padding = isMobile
            ? { top: 70, bottom: sheet + 20, left: 40, right: 40 }
            : 80
          // outlier(원거리 장소)는 프레이밍에서 제외 — 근접 무리가 뭉치지 않게(마커는 그대로 렌더).
          map.fitBounds(coreBounds(places) || bounds, { padding: clampPadding(map, padding), maxZoom: 10, duration: 600 })
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

    // 투어 모드(personId 없음)는 places fetch가 프레이밍을 안 하므로 여기서 정차지에 맞춘다.
    // (인물 모드는 personId 기반 places effect가 fitBounds → 중복 방지 위해 제외.)
    if (!personId) {
      const coord = stops.filter((s) => s.lng != null && s.lat != null)
      if (coord.length > 0) {
        const bounds = coord.reduce(
          (b, s) => b.extend([s.lng, s.lat]),
          new maplibregl.LngLatBounds([coord[0].lng, coord[0].lat], [coord[0].lng, coord[0].lat]),
        )
        const isMobile = window.innerWidth <= MOBILE_BREAKPOINT
        const sheet = Math.round(window.innerHeight * (JOURNEY_SHEET_VH / 100))
        const padding = isMobile ? { top: 70, bottom: sheet + 20, left: 40, right: 40 } : 80
        map.fitBounds(bounds, { padding: clampPadding(map, padding), maxZoom: 10, duration: 600 })
      }
    }
  }, [journeyStops, mapLoaded, personId])

  // 재생 점진 경로선(task#223) — 현재 정차지까지의 좌표만 그려 진행에 따라 선이 자라난다.
  // playbackIdx null(재생 종료·이탈) 시 전체 선 복원. 무좌표 정차지는 slice에 포함돼도 필터돼 선 유지.
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return
    const stops = journeyStops ?? []
    const lineStops = playbackIdx != null ? stops.slice(0, playbackIdx + 1) : stops
    map.getSource('journey-line-source').setData(buildJourneyLineGeoJSON(lineStops))
  }, [playbackIdx, mapLoaded, journeyStops])

  // 활성 정차지 강조 + 카메라 이동 (activeStopIdx prop 변경 시)
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return
    if (activeStopIdx == null || !journeyStops) {
      map.getSource('journey-active-source').setData(EMPTY_GEOJSON)
      return
    }
    // 장소 단위 그룹(좌표 중복 합침) — activeStopIdx는 이 그룹 기준 인덱스(JourneyList와 동일).
    // seqLabel은 그 장소 사건번호 범위(예 "6-8")로 지도 배지와 일치.
    const groups = journeyStopGroups(journeyStops)
    const g = groups[activeStopIdx]
    if (!g) {
      map.getSource('journey-active-source').setData(EMPTY_GEOJSON)
      return
    }
    map.getSource('journey-active-source').setData({
      type: 'FeatureCollection',
      features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [g.lng, g.lat] }, properties: { seqLabel: g.seqLabel } }],
    })
    // 모바일: 하단 여정 시트(JOURNEY_SHEET_VH dvh)가 지도 하단을 덮으므로 정차지를 시트 위 가시영역 중앙으로 올린다.
    // offset[1] 음수 = 대상 좌표가 컨테이너 중앙보다 시트 높이의 절반만큼 위에 오도록 카메라를 내림.
    const isMobile = window.innerWidth <= MOBILE_BREAKPOINT
    // offset 키를 undefined로 명시하면 maplibre easeTo의 기본값(Point 0,0) 병합이 깨져
    // Point.convert(undefined)가 던지고 React 루트가 언마운트된다 — 모바일일 때만 키를 싣는다.
    const offset = isMobile ? [0, -Math.round(window.innerHeight * JOURNEY_SHEET_VH / 100) / 2] : null
    // prefers-reduced-motion: 카메라 즉시 점프(ADR-0024 — 재생·수동 이동 공통)
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    map.easeTo({ center: [g.lng, g.lat], ...(offset ? { offset } : {}), duration: reduceMotion ? 0 : 400 })
  }, [activeStopIdx, mapLoaded, journeyStops])

  // 비유·기적 소스 데이터(task#249) — 인물/투어 선택과 무관하게 fetch 결과가 오면 1회 반영.
  useEffect(() => {
    if (!mapLoaded) return
    mapRef.current?.getSource('pm-source').setData(buildParablesMiraclesGeoJSON(pmItems))
  }, [pmItems, mapLoaded])

  // 비유·기적 표시 토글·종류 필터 — 레이어 visibility + circle filter만 갱신(소스 재계산 없음).
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current
    if (!map) return
    // pmEnabled(신약 era 게이트, task#256) 포함 — 토글 켠 채 비신약 인물로 전환해도 레이어가 잔류하지 않는다.
    map.setLayoutProperty('pm-circle', 'visibility', pmEnabled && pmVisible ? 'visible' : 'none')
    map.setFilter('pm-circle', pmFilter === 'all' ? null : ['==', ['get', 'type'], pmFilter])
  }, [pmEnabled, pmVisible, pmFilter, mapLoaded])

  useEffect(() => {
    if (isVisible && mapRef.current) mapRef.current.resize()
  }, [isVisible, mapLoaded])

  // 위치 없는 비유·기적 건수(task#251) — placeId·직접 좌표 둘 다 없어 지도에 못 얹는 항목.
  // 연표(TimelineView)는 전건을 노출하므로 지도↔연표 커버리지 간극을 이 수치로 명시화한다.
  const pmNoLocCount = pmItems.filter((it) => it.lng == null || it.lat == null).length

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
      {/* 비유·기적 색인 토글(task#249) — 신약 era 컨텍스트에서만 노출(task#256). 켜면 종류 필터 칩 노출. */}
      {pmEnabled && pmItems.length > 0 && (
        // 우측 상단은 selectedNode 시트(SidePanel, zIndex:10)가 데스크톱에서 덮으므로 좌측 상단에 배치.
        <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 6, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 6 }}>
          <button className="pressable" onClick={() => setPmVisible(v => !v)} style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 999,
            background: pmVisible ? PM_TYPE_COLOR.parable : 'var(--bg-1)', color: pmVisible ? '#fff' : 'var(--ink)',
            border: '1px solid var(--line)', cursor: 'pointer', fontSize: 12, fontWeight: 600, font: 'inherit',
            boxShadow: 'var(--shadow-1)',
          }}>✨ 비유·기적</button>
          {pmVisible && (
            <div style={{ display: 'flex', gap: 4, background: 'var(--bg-1)', border: '1px solid var(--line)', borderRadius: 999, padding: 4, boxShadow: 'var(--shadow-1)' }}>
              {PM_FILTERS.map(([key, label]) => (
                <button key={key} onClick={() => setPmFilter(key)} style={{
                  padding: '4px 10px', borderRadius: 999, border: 'none', cursor: 'pointer', font: 'inherit', fontSize: 11.5,
                  background: pmFilter === key ? 'var(--ink)' : 'transparent',
                  color: pmFilter === key ? 'var(--bg-1)' : 'var(--ink-dim)',
                  fontWeight: pmFilter === key ? 700 : 500,
                }}>{label}</button>
              ))}
            </div>
          )}
          {/* 지도↔연표 커버리지 간극 명시화(task#251) — 장소 없는 "가르침" 비유는 지도에 못 얹으므로 연표로 안내. */}
          {pmVisible && pmNoLocCount > 0 && (
            <div style={{
              maxWidth: 220, fontSize: 11, lineHeight: 1.4, color: 'var(--ink-dim)',
              background: 'var(--bg-1)', border: '1px solid var(--line)', borderRadius: 8,
              padding: '6px 10px', boxShadow: 'var(--shadow-1)',
            }}>
              위치 없는 비유 {pmNoLocCount}건은 연표에서 확인
            </div>
          )}
        </div>
      )}
    </div>
  )
}
