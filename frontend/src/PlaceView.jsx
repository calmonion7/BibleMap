import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { TYPE_COLOR } from './theme'

// 장소 페이지(task#270) — 이 곳의 배경·핵심 구절·거쳐 간 인물·그곳의 사건을 한 화면에.
// 데이터는 `/place/{id}` 하나(신규 저작 0). 컨텍스트 없는 좌표 전용 장소도 인물·사건만으로 열린다.
export default function PlaceView({ placeId, onSelectPerson, onSelectNode, verseLang }) {
  const [data, setData] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const ctrl = new AbortController()
    let alive = true
    Promise.resolve().then(() => { if (alive) { setData(null); setFailed(false) } })
    apiGet(`/place/${encodeURIComponent(placeId)}`, { signal: ctrl.signal })
      .then(d => { if (alive) setData(d) })
      .catch(e => {
        if (e?.name !== 'AbortError') { console.warn('[PlaceView] 장소 로드 실패', e); if (alive) setFailed(true) }
      })
    return () => { alive = false; ctrl.abort() }
  }, [placeId])

  const sectionTitle = {
    fontFamily: 'var(--serif)', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em',
    color: 'var(--gold)', margin: '22px 0 8px',
  }

  if (failed) {
    return <div style={{ padding: 24, color: 'var(--ink-dim)' }}>장소를 불러오지 못했어요.</div>
  }
  if (!data) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}><Spinner /></div>
  }

  return (
    <div data-place-view={data.placeId} style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
      <div style={{ maxWidth: 640, margin: '0 auto', padding: '20px 16px 48px' }}>
        <h1 style={{
          fontFamily: 'var(--serif)', fontSize: 24, fontWeight: 700, color: 'var(--ink)', margin: '0 0 4px',
        }}>{data.nameKo}</h1>
        {data.name && (
          <div style={{ fontSize: 12, color: 'var(--ink-faint)' }}>
            {data.name}{data.lat != null && data.lng != null ? ` · ${data.lat.toFixed(3)}, ${data.lng.toFixed(3)}` : ''}
          </div>
        )}

        {data.background && (
          <>
            <div style={sectionTitle}>배경</div>
            <p data-place-background style={{ fontSize: 14, color: 'var(--ink-dim)', lineHeight: 1.7, margin: 0 }}>
              {data.background}
            </p>
          </>
        )}

        {data.keyVerse && (
          <>
            <div style={sectionTitle}>핵심 구절</div>
            <div data-place-keyverse style={{
              background: 'var(--paper)', color: 'var(--paper-ink)', borderRadius: 10,
              padding: '14px 16px', boxShadow: 'var(--shadow-1)',
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--paper-accent)', marginBottom: 4 }}>{data.keyVerse}</div>
              <div style={{ fontSize: 14, lineHeight: 1.7 }}>
                {verseLang === 'en' ? (data.keyVerseTextEn || data.keyVerseTextKo) : data.keyVerseTextKo}
              </div>
            </div>
          </>
        )}

        {data.persons.length > 0 && (
          <>
            <div style={sectionTitle}>이곳을 지난 인물</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {data.persons.map(p => (
                <button
                  key={p.id}
                  data-place-person={p.slug}
                  onClick={() => onSelectPerson?.(p.id)}
                  style={{
                    padding: '6px 12px', borderRadius: 999, cursor: 'pointer',
                    border: '1px solid var(--line)', background: 'var(--bg-1)',
                    color: TYPE_COLOR.Person, fontFamily: 'var(--serif)', fontSize: 13,
                  }}
                >{p.nameKo}<span style={{ color: 'var(--ink-faint)', marginLeft: 6, fontSize: 11 }}>{p.era}</span></button>
              ))}
            </div>
          </>
        )}

        {data.events.length > 0 && (
          <>
            <div style={sectionTitle}>이곳에서 일어난 일</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {data.events.map(e => (
                <button
                  key={e.id}
                  data-place-event={e.id}
                  onClick={() => onSelectNode?.(e.id)}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '9px 10px', borderRadius: 8, cursor: 'pointer',
                    border: 'none', background: 'none', font: 'inherit',
                    borderLeft: '3px solid var(--gold-dim)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: 11, color: 'var(--ink-faint)', flexShrink: 0, minWidth: 62 }}>{e.yearLabel}</span>
                    <span style={{ fontFamily: 'var(--serif)', fontSize: 14, color: 'var(--ink)' }}>{e.nameKo}</span>
                  </div>
                  {e.personNameKo && (
                    <div style={{ fontSize: 11, color: TYPE_COLOR.Person, marginLeft: 70, marginTop: 2 }}>{e.personNameKo}</div>
                  )}
                </button>
              ))}
            </div>
          </>
        )}

        {!data.background && !data.keyVerse && data.persons.length === 0 && data.events.length === 0 && (
          <p style={{ fontSize: 13, color: 'var(--ink-faint)', marginTop: 24 }}>이 장소에 대해 아직 정리된 내용이 없어요.</p>
        )}
      </div>
    </div>
  )
}
