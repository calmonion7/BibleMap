// 해시 URL ↔ 내비게이션 상태 (ADR-0009). 라우팅 라이브러리 없이 순수 문자열 매핑.
// state = { stage: 'hub'|'explore'|'overview'|'tours', personSlug|tourSlug: string|null, exploreView: 'map'|'timeline' }
//   허브    #/            개요  #/books        테마 목록  #/tours
//   탐험(인물)  #/person/<slug>     탐험(인물,타임라인) #/person/<slug>/timeline
//   탐험(투어)  #/tour/<slug>       탐험(투어,타임라인) #/tour/<slug>/timeline

export function encodeHash({ stage, personSlug, exploreView, tourSlug }) {
  if (stage === 'overview') return '#/books'
  if (stage === 'tours') return '#/tours'
  if (stage === 'explore' && tourSlug) {
    const base = `#/tour/${encodeURIComponent(tourSlug)}`
    return exploreView === 'timeline' ? `${base}/timeline` : base
  }
  if (stage === 'explore' && personSlug) {
    const base = `#/person/${encodeURIComponent(personSlug)}`
    return exploreView === 'timeline' ? `${base}/timeline` : base
  }
  return '#/' // 허브 (또는 slug/tour 없는 explore — 정상 흐름엔 없음)
}

// 알 수 없는 형태는 null → 호출부가 허브로 fallback.
export function parseHash(hash) {
  const h = (hash || '').replace(/^#/, '')
  if (h === '' || h === '/') return { stage: 'hub', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/books') return { stage: 'overview', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/tours') return { stage: 'tours', personSlug: null, tourSlug: null, exploreView: 'map' }
  const t = h.match(/^\/tour\/([^/]+)(\/timeline)?$/)
  if (t) return { stage: 'explore', personSlug: null, tourSlug: decodeURIComponent(t[1]), exploreView: t[2] ? 'timeline' : 'map' }
  const m = h.match(/^\/person\/([^/]+)(\/timeline)?$/)
  if (m) return { stage: 'explore', personSlug: decodeURIComponent(m[1]), tourSlug: null, exploreView: m[2] ? 'timeline' : 'map' }
  return null
}
