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

      map.on('click', 'places-circle', (e) => {
        const { id, label, isPrimary } = e.features[0].properties
        const coords = e.features[0].geometry.coordinates.slice()

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

      map.on('click', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['places-circle'] })
        if (!features.length && popupRef.current) {
          popupRef.current.remove()
          popupRef.current = null
        }
      })

      mapRef.current = map
      setMapLoaded(true)
    })

    return () => {
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
            map.fitBounds(bounds, { padding: 80, maxZoom: 10, duration: 600 })
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
