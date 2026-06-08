import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function MapView({ onSelectNode }) {
  const mapContainer = useRef(null)

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
          const marker = new maplibregl.Marker()
            .setLngLat([place.lng, place.lat])
            .addTo(map)

          marker.getElement().addEventListener('click', () => {
            onSelectNode(place.id)
          })
        })
      })
      .catch(() => {})

    return () => map.remove()
  }, [onSelectNode])

  return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
}
