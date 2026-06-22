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

export function registerEventHandlers(map, { collapseRing, collapseSpider, expandPlace, spiderifyPlaces, onSelectNode, popupRef, expandedPlaceRef }) {
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
}
