import { useState, useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { createPortal } from 'react-dom'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLangTabs from './VerseLangTabs'

// 단어 분포 페이지 — 책(또는 성경 전체)의 상위 빈도 명사를 단일 타이포그래피 클라우드로 표시.
// 감정 극성(긍정/중립/부정)은 색+범례로만 구분(영역 분리 없음). 크기 ∝ √빈도,
// 단어 탭 → 해당 책의 포함 구절 양피지 레이어(사건·성품 구절 레이어와 동일 패턴).
// 데이터는 빌드타임 정본(word_distribution.json)을 /words API가 서빙(런타임 형태소 분석 없음).

const BANDS = [
  { key: 'positive', label: '긍정', color: 'var(--valence-pos)' },
  { key: 'neutral', label: '중립', color: 'var(--valence-neutral)' },
  { key: 'negative', label: '부정', color: 'var(--valence-neg)' },
]
const POLARITY_COLOR = Object.fromEntries(BANDS.map(b => [b.key, b.color]))

// 폰트 크기: √(빈도/최대빈도)로 13~34px — 선형이면 최고빈도어(하나님·여호와)가 화면을 삼킨다
function fontSize(count, max) {
  return Math.round(13 + 21 * Math.sqrt(count / max))
}

// 워드 클라우드 배치 — 빈도순으로 중앙에서 아르키메데스 나선을 따라 바깥으로,
// 이미 놓인 사각형과 겹치지 않는 첫 자리에 놓는다(라이브러리 없이 DOM 버튼 유지).
// 가로는 컨테이너 폭으로 제한, 세로는 필요한 만큼 늘어난다(y 0.55 압축 = 가로로 퍼진 구름꼴).
function layoutCloud(words, width, maxCount) {
  const ctx = document.createElement('canvas').getContext('2d')
  const serif = getComputedStyle(document.documentElement).getPropertyValue('--serif').trim() || 'serif'
  const placed = []
  const pad = 4
  const cx = width / 2
  for (const w of words) {
    const fs = fontSize(w.count, maxCount)
    ctx.font = `600 ${fs}px ${serif}`
    const ww = Math.ceil(ctx.measureText(w.word).width)
    const wh = Math.ceil(fs * 1.3)
    let x = Math.max(0, cx - ww / 2)
    let y = -wh / 2
    for (let t = 0; t < 900; t += Math.max(0.06, 8 / (1.5 * t + 1))) {
      const r = 1.5 * t
      x = cx + r * Math.cos(t) - ww / 2
      y = r * 0.55 * Math.sin(t) - wh / 2
      if (x < 0 || x + ww > width) continue
      if (!placed.some(p => x < p.x + p.w + pad && x + ww + pad > p.x && y < p.y + p.h + pad && y + wh + pad > p.y)) break
    }
    placed.push({ x, y, w: ww, h: wh, word: w })
  }
  const minY = Math.min(...placed.map(p => p.y))
  const maxY = Math.max(...placed.map(p => p.y + p.h))
  return { items: placed.map(p => ({ ...p, y: p.y - minY })), height: maxY - minY }
}

function WordDistributionView({ bookId, onSelectBook, verseLang, setVerseLang }) {
  const [data, setData] = useState(null)       // /words/{bookId} 응답
  const [failed, setFailed] = useState(false)
  const [books, setBooks] = useState(null)     // 책 선택 드롭다운(1회 로드)
  const [verseView, setVerseView] = useState(null) // { word, color, loading, total, verses } | null
  const cloudRef = useRef(null)
  const [cloudWidth, setCloudWidth] = useState(0) // 클라우드 내부 폭 — 배치 입력(리사이즈 추적)

  useLayoutEffect(() => {
    const el = cloudRef.current
    if (!el) return
    setCloudWidth(el.clientWidth)
    const ro = new ResizeObserver(entries => setCloudWidth(Math.floor(entries[0].contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [data])

  useEffect(() => {
    let cancelled = false
    apiGet('/books-overview')
      .then(list => { if (!cancelled) setBooks(list) })
      .catch(e => { if (!cancelled) console.warn('[WordDistribution] 책 목록 로드 실패 — 드롭다운 미노출', e) })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const ctrl = new AbortController()
    setData(null); setFailed(false); setVerseView(null)
    apiGet(`/words/${encodeURIComponent(bookId)}`, { signal: ctrl.signal })
      .then(setData)
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[WordDistribution] 단어 분포 로드 실패', e); setFailed(true) } })
    return () => ctrl.abort()
  }, [bookId])

  function openWord(word, color) {
    setVerseView({ word, color, loading: true, total: 0, verses: [] })
    apiGet(`/words/${encodeURIComponent(bookId)}/verses?w=${encodeURIComponent(word)}`)
      .then(({ total, verses }) => setVerseView(v => (v && v.word === word ? { ...v, loading: false, total, verses } : v)))
      .catch(e => { console.warn('[WordDistribution] 구절 검색 실패', e); setVerseView(v => (v && v.word === word ? { ...v, loading: false } : v)) })
  }

  const maxCount = data?.words?.length ? data.words[0].count : 1
  const title = bookId === 'all' ? '성경 전체' : (data?.nameKo || '')

  // 클라우드 배치 — 데이터·폭이 준비되면 계산(폭 0인 첫 프레임은 건너뜀)
  const cloud = useMemo(
    () => (data?.words?.length && cloudWidth ? layoutCloud(data.words, cloudWidth, maxCount) : null),
    [data, cloudWidth, maxCount]
  )

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)', position: 'relative' }}>
      <div style={{ maxWidth: 720, margin: '0 auto', padding: '16px 16px 64px' }}>
        {/* 헤더 — 제목 + 책 선택 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--ink)', fontFamily: 'var(--serif)' }}>
            {title} 단어 분포
          </h2>
          {books && (
            <select
              value={bookId}
              onChange={e => onSelectBook(e.target.value)}
              style={{
                font: 'inherit', fontSize: 13, padding: '5px 8px', borderRadius: 8,
                background: 'var(--bg-2)', color: 'var(--ink-dim)', border: '1px solid var(--line-strong)',
              }}
            >
              <option value="all">성경 전체</option>
              {books.map(b => <option key={b.id} value={b.id}>{b.nameKo}</option>)}
            </select>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginBottom: 18 }}>
          자주 나오는 단어일수록 크게 표시됩니다 · 단어를 누르면 그 단어가 나오는 구절을 보여줍니다
        </div>

        {failed && <div style={{ color: 'var(--danger)', fontSize: 13 }}>단어 분포를 불러오지 못했습니다.</div>}
        {!data && !failed && <Spinner />}

        {data && (
          <div key={bookId}>
            {/* 범례 — 극성은 색으로만 구분(영역 분리 없음) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
              {BANDS.map(band => (
                <span key={band.key} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 9, height: 9, borderRadius: '50%', background: band.color }} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: band.color }}>{band.label}</span>
                  <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{data.words.filter(w => w.polarity === band.key).length}</span>
                </span>
              ))}
            </div>
            {/* 워드 클라우드 — 중앙-나선 배치(빈도 큰 단어가 중심), 단어별 스태거 등장 */}
            <div className="cloud-in" style={{
              padding: '14px 14px', borderRadius: 12,
              background: 'var(--bg-1)', border: '1px solid var(--line)',
            }}>
              <div ref={cloudRef} style={{ position: 'relative', height: cloud ? cloud.height : 240 }}>
                {cloud && cloud.items.map(({ x, y, w: ww, h: wh, word: w }, i) => (
                  <button
                    key={w.word}
                    className="word-in"
                    onClick={() => openWord(w.word, POLARITY_COLOR[w.polarity])}
                    title={`${w.count}회`}
                    style={{
                      position: 'absolute', left: x, top: y, width: ww, height: wh,
                      border: 'none', background: 'none', cursor: 'pointer', padding: 0, whiteSpace: 'nowrap',
                      fontFamily: 'var(--serif)', fontWeight: 600, lineHeight: 1.3,
                      fontSize: fontSize(w.count, maxCount), color: POLARITY_COLOR[w.polarity],
                      // 등장 keyframe의 종료 opacity(--w-op)로 빈도 농도를 전달 — fill:both가 inline opacity를 덮으므로 var 경유
                      '--w-op': 0.55 + 0.45 * Math.sqrt(w.count / maxCount),
                      animationDelay: `${Math.min(i * 20, 600)}ms`,
                    }}
                  >{w.word}</button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 구절 레이어 — 사건·성품 구절 레이어와 동일한 양피지 포털 모달(SidePanel 패턴 복제) */}
      {verseView && createPortal(
        <div
          onClick={() => setVerseView(null)}
          className="overlay-in" style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,26,40,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
        >
          <div onClick={e => e.stopPropagation()} className="modal-in" style={{ background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 'var(--r-m)', maxWidth: 520, width: '100%', maxHeight: '80%', overflowY: 'auto', boxShadow: 'var(--shadow-2)', padding: '18px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span style={{ fontWeight: 700, fontSize: 15, flex: 1, fontFamily: 'var(--serif)', color: verseView.color }}>{verseView.word}</span>
              <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
              <button
                onClick={() => setVerseView(null)}
                aria-label="닫기"
                style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--paper-accent)', lineHeight: 1, padding: '0 2px' }}
              >×</button>
            </div>
            {!verseView.loading && (
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--paper-accent)', marginBottom: 8 }}>
                {verseView.total}구절{verseView.total > verseView.verses.length ? ` 중 ${verseView.verses.length}` : ''}
              </div>
            )}
            {verseView.loading ? (
              <div style={{ padding: '12px 0' }}><Spinner size={20} color="var(--paper-accent)" /></div>
            ) : verseView.verses.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--paper-accent)', padding: '4px 0' }}>구절을 찾지 못했습니다.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {verseView.verses.map(v => (
                  <div key={v.ref + v.textKo.slice(0, 8)} style={{ fontFamily: 'var(--serif)', fontSize: 15.5, lineHeight: 1.8, color: 'var(--paper-ink)' }}>
                    <span style={{ fontWeight: 700, color: 'var(--paper-accent)', marginRight: 6 }}>{v.ref}</span>
                    {verseLang === 'en' && v.textEn ? v.textEn : v.textKo}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default WordDistributionView
