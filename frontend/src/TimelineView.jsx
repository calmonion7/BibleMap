import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function TimelineView({ onSelectNode, selectedNode }) {
  const svgRef = useRef(null)
  const [events, setEvents] = useState([])

  useEffect(() => {
    fetch(API_URL + '/events')
      .then(r => r.json())
      .then(setEvents)
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!events.length || !svgRef.current) return

    const container = svgRef.current.parentElement
    const W = container.clientWidth || 800
    const H = container.clientHeight || 400
    const margin = { top: 40, right: 40, bottom: 60, left: 40 }

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    svg.attr('width', W).attr('height', H)

    const xScale = d3.scaleLinear()
      .domain(d3.extent(events, d => d.sortKey))
      .range([margin.left, W - margin.right])

    const g = svg.append('g')

    const zoom = d3.zoom()
      .scaleExtent([0.1, 20])
      .on('zoom', event => { g.attr('transform', event.transform) })
    svg.call(zoom)

    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => d < 0 ? `BC ${Math.abs(Math.round(d))}` : `AD ${Math.round(d)}`)
    g.append('g')
      .attr('transform', `translate(0, ${H / 2})`)
      .call(xAxis)

    g.append('line')
      .attr('x1', margin.left).attr('x2', W - margin.right)
      .attr('y1', H / 2).attr('y2', H / 2)
      .attr('stroke', '#ccc').attr('stroke-width', 1)

    events.forEach((ev, i) => {
      const x = xScale(ev.sortKey)
      const above = i % 2 === 0
      const y = H / 2 + (above ? -30 : 30)

      g.append('circle')
        .attr('cx', x).attr('cy', H / 2)
        .attr('id', `ev-${ev.id}`)
        .attr('r', 5)
        .attr('fill', '#4a90d9')
        .attr('cursor', 'pointer')
        .on('click', () => onSelectNode(ev.id))

      g.append('text')
        .attr('x', x).attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#333')
        .attr('pointer-events', 'none')
        .text(ev.title.length > 15 ? ev.title.slice(0, 15) + '…' : ev.title)
    })
  }, [events, onSelectNode])

  // selectedNode 변경 시 하이라이트
  useEffect(() => {
    if (!events.length) return

    // 모든 원 초기화
    events.forEach(ev => {
      const el = document.getElementById(`ev-${ev.id}`)
      if (el) el.setAttribute('fill', '#4a90d9')
    })

    if (!selectedNode) return

    // 직접 Event 선택
    const direct = document.getElementById(`ev-${selectedNode}`)
    if (direct) {
      direct.setAttribute('fill', '#e03131')
      return
    }

    // Person/Place 선택 → 관련 Event 이웃 하이라이트
    const ctrl = new AbortController()
    fetch(`${API_URL}/node/${selectedNode}`, { signal: ctrl.signal })
      .then(r => r.json())
      .then(data => {
        ;(data.neighbors || [])
          .filter(n => n.label === 'Event')
          .forEach(n => {
            const el = document.getElementById(`ev-${n.id}`)
            if (el) el.setAttribute('fill', '#e03131')
          })
      })
      .catch(() => {})
    return () => ctrl.abort()
  }, [selectedNode, events])

  return (
    <div style={{ width: '100%', height: '100%', overflow: 'hidden', background: '#fafafa' }}>
      <svg ref={svgRef} style={{ display: 'block' }} />
    </div>
  )
}

export default TimelineView
