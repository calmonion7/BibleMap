import maplibregl from 'maplibre-gl'

export const EMPTY_GEOJSON = { type: 'FeatureCollection', features: [] }

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}

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
      ">${escapeHtml(label)}</div>
      <div style="
        font-size: 11px;
        color: #7c8db0;
        letter-spacing: 0.3px;
      ">${typeLabel}</div>
    </div>
  `
}

export function registerEventHandlers(map, { collapseRing, collapseSpider, expandPlace, spiderifyPlaces, onSelectNode, popupRef, expandedPlaceRef, onJourneyStopClick }) {
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

  map.on('click', 'places-cluster', async (e) => {
    const [feature] = e.features
    const zoom = await map.getSource('places-source').getClusterExpansionZoom(feature.properties.cluster_id)
    if (zoom != null) map.easeTo({ center: feature.geometry.coordinates, zoom, duration: 400 })
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

  map.on('click', 'journey-stop-circle', (e) => {
    const { seq } = e.features[0].properties
    if (onJourneyStopClick && seq != null) onJourneyStopClick(seq - 1) // seq는 1-based → 0-based 인덱스로
  })

  map.on('mouseenter', 'journey-stop-circle', () => {
    map.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', 'journey-stop-circle', () => {
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

export function setupMapSources(map) {
  // 여정선 레이어 — 마커 아래에 깔리도록 먼저 추가
  // lineMetrics:true 는 line-gradient(방향 그라데이션)에 필수
  map.addSource('journey-line-source', { type: 'geojson', data: EMPTY_GEOJSON, lineMetrics: true })
  map.addLayer({
    id: 'journey-line',
    type: 'line',
    source: 'journey-line-source',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: {
      'line-width': 3,
      'line-opacity': 0.85,
      // 파란색(시작) → 주황색(끝) 그라데이션으로 방향감 표현
      'line-gradient': [
        'interpolate', ['linear'], ['line-progress'],
        0, '#4a90d9',
        1, '#f5a623',
      ],
    },
  })

  // 여정선 방향 화살표 — 라인을 따라 진행 방향 표시. text-keep-upright:false로 선 방향을 그대로 따른다.
  map.addLayer({
    id: 'journey-line-arrows',
    type: 'symbol',
    source: 'journey-line-source',
    layout: {
      'symbol-placement': 'line',
      'symbol-spacing': 90,
      'text-field': '▶',
      'text-font': ['Noto Sans Regular'],
      'text-size': 13,
      'text-keep-upright': false,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
      'text-rotation-alignment': 'map',
      'text-pitch-alignment': 'viewport',
    },
    paint: {
      'text-color': '#c47a0a',
      'text-halo-color': 'rgba(255,255,255,0.9)',
      'text-halo-width': 1.5,
    },
  })

  // 여정 정차지 배지 — 순번 숫자 심볼
  map.addSource('journey-stops-source', { type: 'geojson', data: EMPTY_GEOJSON })
  map.addLayer({
    id: 'journey-stop-circle',
    type: 'circle',
    source: 'journey-stops-source',
    paint: {
      'circle-radius': ['case', ['any', ['get', 'isStart'], ['get', 'isEnd']], 10, 8],
      'circle-color': [
        'case',
        ['get', 'isStart'], '#4a90d9',   // 시작: 파랑
        ['get', 'isEnd'],   '#f5a623',   // 끝: 주황
        '#ffffff',                        // 중간: 흰색
      ],
      'circle-stroke-width': 2,
      'circle-stroke-color': [
        'case',
        ['get', 'isStart'], '#2563a8',
        ['get', 'isEnd'],   '#c47a0a',
        '#7c9cfc',
      ],
      'circle-opacity': 0.95,
    },
  })
  map.addLayer({
    id: 'journey-stop-label',
    type: 'symbol',
    source: 'journey-stops-source',
    layout: {
      'text-field': ['to-string', ['get', 'seq']],
      'text-font': ['Noto Sans Regular'],
      'text-size': 10,
      'text-anchor': 'center',
      'text-allow-overlap': true,
      'text-ignore-placement': true,
    },
    paint: {
      'text-color': [
        'case',
        ['any', ['get', 'isStart'], ['get', 'isEnd']], '#ffffff',
        '#1a1a2e',
      ],
    },
  })

  // 활성 정차지 강조 — 반전 배지(네이비 채움 + 흰 번호 + 주황 링, 확대)로 선택 정차지를 부각.
  map.addSource('journey-active-source', { type: 'geojson', data: EMPTY_GEOJSON })
  map.addLayer({
    id: 'journey-active-circle',
    type: 'circle',
    source: 'journey-active-source',
    paint: {
      'circle-radius': 13,
      'circle-color': '#1a1a2e',
      'circle-stroke-width': 3,
      'circle-stroke-color': '#f5a623',
    },
  })
  map.addLayer({
    id: 'journey-active-label',
    type: 'symbol',
    source: 'journey-active-source',
    layout: {
      'text-field': ['to-string', ['get', 'seq']],
      'text-font': ['Noto Sans Regular'],
      'text-size': 12,
      'text-anchor': 'center',
      'text-allow-overlap': true,
      'text-ignore-placement': true,
    },
    paint: { 'text-color': '#ffffff' },
  })

  map.addSource('places-source', {
    type: 'geojson',
    data: EMPTY_GEOJSON,
    cluster: true,
    clusterMaxZoom: 13,
    clusterRadius: 18, // 마커 원이 실제 겹칠 때만 클러스터 (마커 지름 ~21~27px) — task-76, 12~14 밑은 금지
    clusterMinPoints: 4, // 동일/근접 좌표 2~3개는 버블 대신 라벨 표시(task-84), 4개+만 클러스터
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
      'text-allow-overlap': false,
      'text-padding': 3,
    },
    paint: {
      'text-color': '#1a1a2e',
      'text-halo-color': 'rgba(255,255,255,0.95)',
      'text-halo-width': 2,
    },
  })

  // 여정 번호 배지·활성 강조를 장소 마커 위로 올린다(같은 좌표에서 장소 점이 배지를 덮는 것 방지).
  // event-ring 아래에 두어 장소 클릭 시 사건 링은 그대로 위에 보이게 한다.
  for (const id of ['journey-stop-circle', 'journey-stop-label', 'journey-active-circle', 'journey-active-label']) {
    if (map.getLayer(id)) map.moveLayer(id, 'event-ring-shadow')
  }
}
