// 해시 URL ↔ 내비게이션 상태 (ADR-0009). 라우팅 라이브러리 없이 순수 문자열 매핑.
// state = { stage: 'hub'|'explore'|'overview'|'tours', personSlug|tourSlug: string|null, exploreView: 'map'|'timeline' }
//   허브    #/            개요  #/books        테마 목록  #/tours       인트로  #/intro
//   책 상세  #/book/<id>  (id = theographic_id, 책은 slug 없음)
//   본문 리더  #/read/<id>(장 그리드) · #/read/<id>/<n>(장 본문)
//   장소 페이지  #/place/<id>   통사 연표  #/timeline
//   탐험(인물)  #/person/<slug>     탐험(인물,타임라인) #/person/<slug>/timeline
//   탐험(투어)  #/tour/<slug>       탐험(투어,타임라인) #/tour/<slug>/timeline

export function encodeHash({ stage, personSlug, exploreView, tourSlug, bookId, familyId, wordsBookId, readerBookId, readerChapter, placeId }) {
  if (stage === 'intro') return '#/intro'
  if (stage === 'overview') return '#/books'
  if (stage === 'book' && bookId) return `#/book/${encodeURIComponent(bookId)}`
  if (stage === 'reader' && readerBookId) {
    const base = `#/read/${encodeURIComponent(readerBookId)}`
    return readerChapter ? `${base}/${readerChapter}` : base
  }
  if (stage === 'place' && placeId) return `#/place/${encodeURIComponent(placeId)}`
  if (stage === 'family' && familyId) return `#/family/${encodeURIComponent(familyId)}`
  if (stage === 'words' && wordsBookId) return `#/words/${encodeURIComponent(wordsBookId)}`
  if (stage === 'canon') return '#/timeline'
  if (stage === 'stats') return '#/stats'
  if (stage === 'topics') return '#/topics'
  if (stage === 'tours') return '#/tours'
  if (stage === 'explore' && tourSlug) {
    const base = `#/tour/${encodeURIComponent(tourSlug)}`
    return exploreView === 'timeline' ? `${base}/timeline` : base
  }
  if (stage === 'explore' && personSlug) {
    const base = `#/person/${encodeURIComponent(personSlug)}`
    if (exploreView === 'timeline') return `${base}/timeline`
    if (exploreView === 'relations') return `${base}/relations`
    if (exploreView === 'intro') return `${base}/intro`
    if (exploreView === 'reliance') return `${base}/reliance`
    return base
  }
  return '#/' // 허브 (또는 slug/tour 없는 explore — 정상 흐름엔 없음)
}

// 알 수 없는 형태는 null → 호출부가 허브로 fallback.
export function parseHash(hash) {
  const h = (hash || '').replace(/^#/, '')
  if (h === '' || h === '/') return { stage: 'hub', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/intro') return { stage: 'intro', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/books') return { stage: 'overview', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/timeline') return { stage: 'canon', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/stats') return { stage: 'stats', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/topics') return { stage: 'topics', personSlug: null, tourSlug: null, exploreView: 'map' }
  if (h === '/tours') return { stage: 'tours', personSlug: null, tourSlug: null, exploreView: 'map' }
  const bk = h.match(/^\/book\/([^/]+)$/)
  if (bk) return { stage: 'book', bookId: decodeURIComponent(bk[1]), personSlug: null, tourSlug: null, exploreView: 'map' }
  const rd = h.match(/^\/read\/([^/]+)(?:\/(\d+))?$/)
  if (rd) return { stage: 'reader', readerBookId: decodeURIComponent(rd[1]), readerChapter: rd[2] ? Number(rd[2]) : null, personSlug: null, tourSlug: null, exploreView: 'map' }
  const pl = h.match(/^\/place\/([^/]+)$/)
  if (pl) return { stage: 'place', placeId: decodeURIComponent(pl[1]), personSlug: null, tourSlug: null, exploreView: 'map' }
  const fm = h.match(/^\/family\/([^/]+)$/)
  if (fm) return { stage: 'family', familyId: decodeURIComponent(fm[1]), personSlug: null, tourSlug: null, exploreView: 'map' }
  const wd = h.match(/^\/words\/([^/]+)$/)
  if (wd) return { stage: 'words', wordsBookId: decodeURIComponent(wd[1]), personSlug: null, tourSlug: null, exploreView: 'map' }
  const t = h.match(/^\/tour\/([^/]+)(\/timeline)?$/)
  if (t) return { stage: 'explore', personSlug: null, tourSlug: decodeURIComponent(t[1]), exploreView: t[2] ? 'timeline' : 'map' }
  const m = h.match(/^\/person\/([^/]+)(\/timeline|\/relations|\/intro|\/reliance)?$/)
  if (m) return { stage: 'explore', personSlug: decodeURIComponent(m[1]), tourSlug: null, exploreView: m[2] === '/timeline' ? 'timeline' : m[2] === '/relations' ? 'relations' : m[2] === '/intro' ? 'intro' : m[2] === '/reliance' ? 'reliance' : 'map' }
  return null
}
