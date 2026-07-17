import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { TYPE_COLOR } from './theme'

// 책의 무대 미니맵(task#207) — 책 primary 사건들의 장소를 잠긴 소형 지도로 표시.
// 드래그·줌 인터랙션 전부 잠금(interactive: false — DOM 마커의 클릭은 유지), 전체 장소 fitBounds.
// 마커 탭 → onSelectPlace(기존 장소 상세 시트 흐름). 타일·오버레이는 MapView와 동일 NatGeo(테마 불변).
function BookStageMap({ places, onSelectPlace }) {
  const containerRef = useRef(null)
  // 콜백은 ref로 — 부모 리렌더마다 지도 재생성을 막는다(마운트 1회).
  const onSelectRef = useRef(onSelectPlace)
  useEffect(() => { onSelectRef.current = onSelectPlace }, [onSelectPlace])

  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current,
      interactive: false,
      style: {
        version: 8,
        sources: {
          esri: {
            // MapView와 동일 NatGeo 타일 — 현대 지도 대비로 성경 지리 이해(ADR-0013 지도 조항)
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

    const bounds = places.reduce(
      (b, p) => b.extend([p.lng, p.lat]),
      new maplibregl.LngLatBounds([places[0].lng, places[0].lat], [places[0].lng, places[0].lat])
    )
    map.fitBounds(bounds, { padding: 36, duration: 0, maxZoom: 8 })

    const markers = places.map(p => {
      const el = document.createElement('button')
      el.type = 'button'
      el.setAttribute('aria-label', p.nameKo || p.name)
      el.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:1px;background:none;border:none;cursor:pointer;padding:0'
      const dot = document.createElement('span')
      dot.style.cssText = `width:9px;height:9px;border-radius:50%;background:${TYPE_COLOR.Place};border:1.5px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4)`
      const label = document.createElement('span')
      label.textContent = p.nameKo || p.name
      // 지도 래스터 위 고정 대비(테마 불변) — 흰 헤일로 + 진한 잉크
      label.style.cssText = 'font-size:10px;font-weight:600;color:#2a2118;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 4px #fff;white-space:nowrap;line-height:1.2'
      el.appendChild(dot)
      el.appendChild(label)
      el.addEventListener('click', () => onSelectRef.current?.(p.id))
      return new maplibregl.Marker({ element: el, anchor: 'top', offset: [0, -6] })
        .setLngLat([p.lng, p.lat])
        .addTo(map)
    })

    return () => {
      markers.forEach(m => m.remove())
      map.remove()
    }
  }, [places])

  return <div ref={containerRef} style={{ height: 220, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--line-strong)' }} />
}

export default BookStageMap
