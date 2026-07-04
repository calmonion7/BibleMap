// 해시 URL ↔ 내비게이션 상태 (ADR-0009). 라우팅 라이브러리 없이 순수 문자열 매핑.
// state = { stage: 'hub'|'explore'|'overview', personSlug: string|null, exploreView: 'map'|'timeline' }
//   허브    #/            개요  #/books
//   탐험    #/person/<slug>      탐험(타임라인) #/person/<slug>/timeline

export function encodeHash({ stage, personSlug, exploreView }) {
  if (stage === 'overview') return '#/books'
  if (stage === 'explore' && personSlug) {
    const base = `#/person/${encodeURIComponent(personSlug)}`
    return exploreView === 'timeline' ? `${base}/timeline` : base
  }
  return '#/' // 허브 (또는 slug 없는 explore — 정상 흐름엔 없음)
}

// 알 수 없는 형태는 null → 호출부가 허브로 fallback.
export function parseHash(hash) {
  const h = (hash || '').replace(/^#/, '')
  if (h === '' || h === '/') return { stage: 'hub', personSlug: null, exploreView: 'map' }
  if (h === '/books') return { stage: 'overview', personSlug: null, exploreView: 'map' }
  const m = h.match(/^\/person\/([^/]+)(\/timeline)?$/)
  if (m) return { stage: 'explore', personSlug: decodeURIComponent(m[1]), exploreView: m[2] ? 'timeline' : 'map' }
  return null
}
