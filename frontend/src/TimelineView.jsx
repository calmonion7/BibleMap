import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function TimelineView({ onSelectNode }) {
  const svgRef = useRef(null)
  const [events, setEvents] = useState([])

  // 데이터 fetch
  useEffect(() => {
    fetch(API_URL + '/events')
      .then(r => r.json())
      .then(setEvents)
      .catch(() => {})
  }, [])

  // d3 렌더링
  useEffect(() => {
    if (!events.length || !svgRef.current) return

    const container = svgRef.current.parentElement
    const W = container.clientWidth || 800
    const H = container.clientHeight || 400
    const margin = { top: 40, right: 40, bottom: 60, left: 40 }

    // SVG 초기화
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    svg.attr('width', W).attr('height', H)

    // x 스케일: sortKey 기준
    const xScale = d3.scaleLinear()
      .domain(d3.extent(events, d => d.sortKey))
      .range([margin.left, W - margin.right])

    // 줌 그룹
    const g = svg.append('g')

    // 줌 동작
    const zoom = d3.zoom()
      .scaleExtent([0.1, 20])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })
    svg.call(zoom)

    // x축
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => d < 0 ? `BC ${Math.abs(Math.round(d))}` : `AD ${Math.round(d)}`)
    g.append('g')
      .attr('transform', `translate(0, ${H / 2})`)
      .call(xAxis)

    // 기준선
    g.append('line')
      .attr('x1', margin.left).attr('x2', W - margin.right)
      .attr('y1', H / 2).attr('y2', H / 2)
      .attr('stroke', '#ccc').attr('stroke-width', 1)

    // 이벤트 마커 (위아래 교대로)
    events.forEach((ev, i) => {
      const x = xScale(ev.sortKey)
      const above = i % 2 === 0
      const y = H / 2 + (above ? -30 : 30)

      // 원
      g.append('circle')
        .attr('cx', x).attr('cy', H / 2)
        .attr('r', 5)
        .attr('fill', '#4a90d9')
        .attr('cursor', 'pointer')
        .on('click', () => onSelectNode(ev.id))

      // 제목 텍스트
      g.append('text')
        .attr('x', x).attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#333')
        .attr('pointer-events', 'none')
        .text(ev.title.length > 15 ? ev.title.slice(0, 15) + '…' : ev.title)
    })
  }, [events, onSelectNode])

  return (
    <div style={{ width: '100%', height: '100%', overflow: 'hidden', background: '#fafafa' }}>
      <svg ref={svgRef} style={{ display: 'block' }} />
    </div>
  )
}

export default TimelineView
