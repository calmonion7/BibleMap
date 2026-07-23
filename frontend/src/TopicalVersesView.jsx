import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLayer, { paperTextStyle } from './VerseLayer'

// 주제별 큐레이션 성구 색인(task#250) — 믿음·사랑·용서 등 주제 카드 선택 시 그 주제의 성구를
// 구절 레이어(양피지, VerseLayer)로 본문(한/영)과 함께 보여준다. 데이터는 /topical-verses 1회 fetch(StatsView와 동형).
export default function TopicalVersesView({ verseLang, setVerseLang }) {
  const [topics, setTopics] = useState(null)
  const [failed, setFailed] = useState(false)
  const [active, setActive] = useState(null)

  useEffect(() => {
    let cancelled = false
    apiGet('/topical-verses')
      .then(d => { if (!cancelled) setTopics(d) })
      .catch(e => { if (!cancelled) { console.warn('[TopicalVerses] 주제 성구 로드 실패', e); setFailed(true) } })
    return () => { cancelled = true }
  }, [])

  if (failed) {
    return <div style={{ color: 'var(--danger)', padding: 24, background: 'var(--bg-0)', height: '100%' }}>주제 성구를 불러오지 못했습니다.</div>
  }
  if (!topics) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: 'var(--bg-0)' }}>
        <Spinner />
      </div>
    )
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
      <div style={{ maxWidth: 640, margin: '0 auto', padding: '16px 16px 64px' }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--ink)', fontFamily: 'var(--serif)' }}>주제별 성구</h2>
        <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginTop: 4 }}>삶의 주제를 따라 큐레이션한 성구입니다</div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 8, marginTop: 16 }}>
          {topics.map(t => (
            <button
              key={t.id}
              onClick={() => setActive(t)}
              className="pressable"
              style={{
                textAlign: 'left', font: 'inherit', cursor: 'pointer',
                background: 'var(--bg-1)', border: '1px solid var(--line)', borderRadius: 10,
                padding: 12,
              }}
            >
              <div style={{ color: 'var(--ink)', fontFamily: 'var(--serif)', fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{t.name}</div>
              <div style={{ color: 'var(--ink-faint)', fontSize: 11.5, lineHeight: 1.4 }}>{t.description}</div>
              <div style={{ color: 'var(--gold)', fontSize: 11, marginTop: 6 }}>{t.verses.length}구절</div>
            </button>
          ))}
        </div>
      </div>

      {active && (
        <VerseLayer
          title={active.name}
          refLine={active.description}
          dotColor="var(--gold)"
          onClose={() => setActive(null)}
          verseLang={verseLang}
          setVerseLang={setVerseLang}
        >
          {active.verses.map(v => (
            <div key={v.verseId} style={{ ...paperTextStyle, marginBottom: 14 }}>
              {(verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'}
            </div>
          ))}
        </VerseLayer>
      )}
    </div>
  )
}
