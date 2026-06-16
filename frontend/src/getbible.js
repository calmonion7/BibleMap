// getbible 한국어 성경 — 장(chapter) JSON 공유 fetch 헬퍼.
// getbible v2는 절 단위 엔드포인트가 없어 장 JSON을 받아 verses[]에서 절을 찾는다.
// 모듈 레벨 캐시로 같은 장 재fetch를 방지(노드·사건 무관, 동일 장 1회만 요청).
const _chapterCache = new Map()

// (bookOrder, chapter)의 장 JSON을 받아 캐시. 실패 시 null(캐시하지 않아 재시도 가능).
export async function fetchChapter(bookOrder, chapter) {
  const key = `${bookOrder}/${chapter}`
  if (_chapterCache.has(key)) return _chapterCache.get(key)
  try {
    const url = `https://api.getbible.net/v2/korean/${bookOrder}/${chapter}.json`
    const r = await fetch(url)
    if (!r.ok) return null
    const d = await r.json()
    _chapterCache.set(key, d)
    return d
  } catch {
    return null
  }
}
