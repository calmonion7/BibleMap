import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLangTabs from './VerseLangTabs'
import { paperTextStyle } from './VerseLayer'

// 본문 리더(task#205) — 장 단위 통독 화면. chapter가 null이면 장 그리드(목차), 지정되면 그 장 본문.
// 본문 데이터는 프리베이크 정본 절 사전(/book/{id}/chapter/{n}, ADR-0003·0015) — 신규 저작 0.
// 장 그리드의 책 이름·장 수는 Book 노드(/node/{id})의 nameKo·chapterCount.
function ChapterReader({ bookId, chapter, onSelectChapter, verseLang, setVerseLang }) {
  const [bookMeta, setBookMeta] = useState(null)   // { nameKo, chapterCount } — 그리드·로딩 헤더용
  const [data, setData] = useState(null)           // /book/{id}/chapter/{n} 응답
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const ctrl = new AbortController()
    let alive = true
    Promise.resolve().then(() => { if (alive) setBookMeta(null) })
    apiGet(`/node/${encodeURIComponent(bookId)}`, { signal: ctrl.signal })
      .then(node => { if (alive) setBookMeta({ nameKo: node.nameKo, chapterCount: node.properties?.chapterCount }) })
      .catch(e => { if (e?.name !== 'AbortError') console.warn('[ChapterReader] 책 정보 로드 실패 — 그리드 헤더 미노출', e) })
    return () => { alive = false; ctrl.abort() }
  }, [bookId])

  useEffect(() => {
    if (chapter == null) return
    const ctrl = new AbortController()
    let alive = true
    // 장 전환 리셋 — effect 동기 setState 금지 규칙 회피(WordDistributionView 선례).
    Promise.resolve().then(() => { if (alive) { setData(null); setFailed(false) } })
    apiGet(`/book/${encodeURIComponent(bookId)}/chapter/${chapter}`, { signal: ctrl.signal })
      .then(d => { if (alive) setData(d) })
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[ChapterReader] 장 본문 로드 실패', e); setFailed(true) } })
    return () => { alive = false; ctrl.abort() }
  }, [bookId, chapter])

  const nameKo = data?.nameKo || bookMeta?.nameKo || ''
  const chapterCount = data?.chapterCount ?? bookMeta?.chapterCount ?? null

  const chapterBtnStyle = (disabled) => ({
    padding: '8px 16px', borderRadius: 999, cursor: disabled ? 'default' : 'pointer',
    border: '1px solid var(--line)', background: 'var(--bg-1)',
    color: disabled ? 'var(--ink-faint)' : 'var(--ink)', fontSize: 13, fontFamily: 'var(--serif)',
    opacity: disabled ? 0.5 : 1,
  })

  // 장 그리드(목차) — 장 번호 버튼만, 요약 노출은 task#206 별도.
  if (chapter == null) {
    return (
      <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '20px 16px 48px' }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 700, color: 'var(--ink)' }}>
              {nameKo || ' '}
            </div>
            {chapterCount != null && (
              <div style={{ fontSize: 12, color: 'var(--ink-dim)', marginTop: 4 }}>전 {chapterCount}장 — 장을 골라 읽기 시작</div>
            )}
          </div>
          {chapterCount == null ? (
            <Spinner />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(52px, 1fr))', gap: 8 }}>
              {Array.from({ length: chapterCount }, (_, i) => i + 1).map(n => (
                <button
                  key={n}
                  onClick={() => onSelectChapter(n)}
                  style={{
                    padding: '12px 0', borderRadius: 8, cursor: 'pointer',
                    border: '1px solid var(--line)', background: 'var(--bg-1)',
                    color: 'var(--ink)', fontSize: 14, fontFamily: 'var(--serif)',
                    transition: 'border-color var(--dur-fast), color var(--dur-fast)',
                  }}
                >{n}</button>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // 장 본문 — 양피지 카드(--paper*, 테마 불변) + 한/영 탭 + 이전/다음 장.
  // key={chapter}로 장 전환 시 스크롤 컨테이너 리마운트(항상 맨 위에서 시작).
  return (
    <div key={`${bookId}-${chapter}`} style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
      <div style={{ maxWidth: 640, margin: '0 auto', padding: '16px 16px 48px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 12 }}>
          <button
            onClick={() => onSelectChapter(null)}
            style={{
              border: 'none', background: 'none', cursor: 'pointer', padding: 0,
              fontSize: 12, color: 'var(--ink-dim)', display: 'inline-flex', alignItems: 'center', gap: 4,
            }}
          >☰ 목차</button>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 700, color: 'var(--ink)' }}>
            {nameKo} {chapter}장
          </div>
          <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
        </div>

        <div style={{
          background: 'var(--paper)', color: 'var(--paper-ink)', boxShadow: 'var(--shadow-2)',
          borderRadius: 10, padding: '20px 22px',
        }}>
          {failed ? (
            <div style={{ ...paperTextStyle, textAlign: 'center', padding: '24px 0' }}>본문을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.</div>
          ) : !data ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '32px 0' }}><Spinner /></div>
          ) : data.verses.length === 0 ? (
            <div style={{ ...paperTextStyle, textAlign: 'center', padding: '24px 0' }}>이 장에는 본문이 없어요.</div>
          ) : (
            data.verses.map(v => (
              <div key={v.verseId} style={{ ...paperTextStyle, marginBottom: 6 }}>
                <sup style={{ fontSize: 11, color: 'var(--paper-accent)', marginRight: 4, fontWeight: 600 }}>{v.v}</sup>
                {verseLang === 'ko' ? v.textKo : v.textEn}
              </div>
            ))
          )}
        </div>

        {chapterCount != null && (
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 16 }}>
            <button onClick={() => onSelectChapter(chapter - 1)} disabled={chapter <= 1} style={chapterBtnStyle(chapter <= 1)}>← 이전 장</button>
            <button onClick={() => onSelectChapter(chapter + 1)} disabled={chapter >= chapterCount} style={chapterBtnStyle(chapter >= chapterCount)}>다음 장 →</button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChapterReader
