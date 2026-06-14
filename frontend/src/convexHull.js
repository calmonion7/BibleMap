/**
 * convexHull(points) — 좌표 배열로 볼록 껍질 반환 (Graham scan).
 * @param {Array<{lng: number, lat: number}>} points
 * @returns {Array<{lng: number, lat: number}>}
 */
export function convexHull(points) {
  if (points.length === 0) return []
  if (points.length <= 2) return [...points]

  // 최하점(lat 최소, 동률이면 lng 최소)을 피벗으로 설정
  let pivot = points[0]
  for (const p of points) {
    if (p.lat < pivot.lat || (p.lat === pivot.lat && p.lng < pivot.lng)) pivot = p
  }

  function cross(O, A, B) {
    return (A.lng - O.lng) * (B.lat - O.lat) - (A.lat - O.lat) * (B.lng - O.lng)
  }

  function dist2(A, B) {
    const dx = A.lng - B.lng, dy = A.lat - B.lat
    return dx * dx + dy * dy
  }

  // 피벗 기준 극각 정렬
  const sorted = points
    .filter(p => p !== pivot)
    .sort((a, b) => {
      const c = cross(pivot, a, b)
      if (c !== 0) return -c // 반시계 우선
      return dist2(pivot, a) - dist2(pivot, b) // 같은 방향이면 가까운 것 먼저
    })

  // 중복 극각 중 마지막 것만 남김(같은 방향 중 가장 먼 것)
  const filtered = []
  for (let i = 0; i < sorted.length; i++) {
    while (i < sorted.length - 1 && cross(pivot, sorted[i], sorted[i + 1]) === 0) i++
    filtered.push(sorted[i])
  }

  if (filtered.length < 2) return [pivot, ...filtered]

  const stack = [pivot, filtered[0]]
  for (let i = 1; i < filtered.length; i++) {
    while (stack.length > 1 && cross(stack[stack.length - 2], stack[stack.length - 1], filtered[i]) <= 0) {
      stack.pop()
    }
    stack.push(filtered[i])
  }

  return stack
}
