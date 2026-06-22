import { apiGet } from './api'
import { easeOutCubic, ringPositions, ringLabels, buildEventGeoJSON, buildSpiderGeoJSON } from './mapGeo'
import { EMPTY_GEOJSON } from './mapLayers'

// MapView 사건 링/스파이더 애니메이션 컨트롤러 — 공유 가변 상태(animFrame/spiderState/expandedPlace 등)를
// 클로저에 캡슐화. 4개 함수 + destroy() 반환. expandedPlace는 호출 측 ref와 공유(registerEventHandlers 재클릭 판단).
export function createRingController(map, { expandedPlaceRef, setError }) {
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
    } catch (e) {
      if (e?.name !== 'AbortError' && !destroyed) setError(true) // 링 정보 로드 실패 — 무반응 대신 피드백
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


  function destroy() {
    destroyed = true
    if (animFrame) cancelAnimationFrame(animFrame)
    if (spiderAnimFrame) cancelAnimationFrame(spiderAnimFrame)
    if (expandAbortCtrl) expandAbortCtrl.abort()
  }

  return { collapseRing, collapseSpider, expandPlace, spiderifyPlaces, destroy }
}
