import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function MapView({ onSelectNode, selectedNode }) {
  const mapContainer = useRef(null)
  const markersRef = useRef(new Map())

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
              'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'
            ],
            tileSize: 256,
          },
        },
        layers: [
          {
            id: 'esri-layer',
            type: 'raster',
            source: 'esri',
          },
        ],
      },
    })

    fetch(`${API_URL}/places`)
      .then((res) => res.json())
      .then((places) => {
        places.forEach((place) => {
          const el = document.createElement('div')
          el.style.cssText = 'width:12px;height:12px;border-radius:50%;background:#4a90d9;cursor:pointer;'
          markersRef.current.set(place.id, el)
          new maplibregl.Marker({ element: el }).setLngLat([place.lng, place.lat]).addTo(map)
          el.addEventListener('click', () => onSelectNode(place.id))
        })
      })
      .catch(() => {})

    return () => map.remove()
  }, [onSelectNode])

  useEffect(() => {
    markersRef.current.forEach((el) => {
      el.style.background = '#4a90d9'
      el.style.width = '12px'
      el.style.height = '12px'
    })

    if (!selectedNode) return

    const ctrl = new AbortController()

    fetch(`${API_URL}/node/${selectedNode}`, { signal: ctrl.signal })
      .then((res) => res.json())
      .then((data) => {
        if (data.label === 'Event') {
          const placeNeighbors = data.neighbors.filter((n) => n.label === 'Place')
          placeNeighbors.forEach((n) => {
            const el = markersRef.current.get(n.id)
            if (el) {
              el.style.background = '#e03131'
              el.style.width = '17px'
              el.style.height = '17px'
            }
          })
        } else if (data.label === 'Place') {
          const el = markersRef.current.get(selectedNode)
          if (el) {
            el.style.background = '#e03131'
            el.style.width = '17px'
            el.style.height = '17px'
          }
        }
      })
      .catch(() => {})

    return () => ctrl.abort()
  }, [selectedNode])

  return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
}
