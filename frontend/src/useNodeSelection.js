import { useState, useEffect, useCallback, useRef } from 'react'
import { apiGet } from './api'

export function useNodeSelection() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedNodeMeta, setSelectedNodeMeta] = useState(null)
  const [history, setHistory] = useState([])
  const [personEventIds, setPersonEventIds] = useState(null)
  const selectedNodeRef = useRef(null)
  useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])

  // 선택된 노드의 메타 정보(label, Book 연대) 조회 — SidePanel과 별도 fetch 없이 콜백으로 수신
  const handleNodeLoaded = useCallback((node) => {
    if (!node) return
    setSelectedNodeMeta({
      label: node.label,
      nameKo: node.nameKo,
      startYear: node.properties?.startYear ?? null,
      endYear: node.properties?.endYear ?? null,
    })
    if (node.label === 'Person') {
      apiGet(`/person/${node.id}/event-ids`)
        .then(data => setPersonEventIds(new Set(data.eventIds)))
        .catch(() => setPersonEventIds(null))
    } else {
      setPersonEventIds(null)
    }
  }, [])

  // 노드 선택 — 직전 노드를 히스토리에 쌓아 패널 뒤로가기를 지원
  // useCallback([])으로 참조를 안정화: selectedNode 변경 시 MapView 등의 useEffect가 재실행되어
  // expandPlace fetch가 abort되는 버그 방지 (selectedNodeRef로 최신값 읽음)
  const selectNode = useCallback((id) => {
    if (id === selectedNodeRef.current) return
    if (selectedNodeRef.current) setHistory(h => [...h, selectedNodeRef.current])
    setSelectedNode(id)
    setSelectedNodeMeta(null)
    setPersonEventIds(null)
  }, [])

  // 새 탐색 컨텍스트(검색 선택 등) — 히스토리 리셋 후 노드 선택
  function selectNodeFresh(id) {
    setHistory([])
    setSelectedNode(id)
    setSelectedNodeMeta(null)
    setPersonEventIds(null)
  }

  function goBack() {
    setSelectedNode(history[history.length - 1] ?? null)
    setHistory(h => h.slice(0, -1))
  }

  function closePanel() {
    setHistory([])
    setSelectedNode(null)
  }

  return {
    selectedNode, selectedNodeMeta, history, personEventIds, selectedNodeRef,
    handleNodeLoaded, selectNode, selectNodeFresh, goBack, closePanel,
  }
}
