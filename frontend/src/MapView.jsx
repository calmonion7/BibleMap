import { useEffect, useRef } from 'react'
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

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapContainer.current,
      center: [35.22, 31.78],
      zoom: 5,
      style: {
        version: 8,
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
        id: 'places-circle',
        type: 'circle',
        source: 'places-source',
        paint: {
          'circle-radius': ['case', ['get', 'isPrimary'], 10, 7],
          'circle-color': ['case', ['get', 'isPrimary'], '#e03131', '#4a90d9'],
          'circle-stroke-width': ['case', ['get', 'isPrimary'], 2.5, 2],
          'circle-stroke-color': '#ffffff',
        },
      })

      map.addLayer({
        id: 'places-label',
        type: 'symbol',
        source: 'places-source',
        layout: {
          'text-field': ['get', 'label'],
          'text-size': 12,
          'text-anchor': 'left',
          'text-offset': [0.8, 0],
          'text-allow-overlap': false,
          'text-ignore-placement': false,
        },
        paint: {
          'text-color': '#1a1a2e',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1.5,
        },
      })

      map.on('click', 'places-circle', (e) => {
        const id = e.features[0].properties.id
        if (id) onSelectNode(id)
      })

      map.on('mouseenter', 'places-circle', () => {
        map.getCanvas().style.cursor = 'pointer'
      })
      map.on('mouseleave', 'places-circle', () => {
        map.getCanvas().style.cursor = ''
      })

      mapRef.current = map
    })

    return () => map.remove()
  }, [onSelectNode])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.getSource('places-source')) return

    if (!selectedNode) {
      map.getSource('places-source').setData(EMPTY_GEOJSON)
      return
    }

    const ctrl = new AbortController()

    fetch(`${API_URL}/node/${selectedNode}/places`, { signal: ctrl.signal })
      .then((res) => res.json())
      .then((places) => {
        map.getSource('places-source').setData(placesToGeoJSON(places))
      })
      .catch(() => {})

    return () => ctrl.abort()
  }, [selectedNode])

  return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
}
