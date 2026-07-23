import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import { TYPE_COLOR } from './theme'

// 성경 통계 대시보드 — 그래프 집계(총계·최다 등장 인물·최장 여정·시대별 사건 분포·책별 장 수)를
// 카드/막대로 보여준다(task#248). 데이터는 /stats(백엔드 lru_cache 집계)를 1회 fetch.
// 차트 라이브러리 없이 RelianceView 랭킹 막대·WordDistributionView 패턴을 재사용(CSS 막대).

const TOP_N = 10

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--bg-1)', border: '1px solid var(--line)', borderRadius: 10,
      padding: '14px 16px', textAlign: 'center',
    }}>
      <div style={{ fontSize: 26, fontWeight: 700, color, fontFamily: 'var(--serif)' }}>{value.toLocaleString()}</div>
      <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginTop: 4 }}>{label}</div>
    </div>
  )
}

// 막대 행 — 라벨 + 막대(value/max 비례) + 수치. onClick 있으면 button(딥링크 항목), 없으면 div(순수 표시, 시대별 분포).
function BarRow({ label, value, max, color, onClick }) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 10, width: '100%',
        font: 'inherit', border: 'none', background: 'none', padding: '4px 0',
        cursor: onClick ? 'pointer' : 'default', textAlign: 'left',
      }}
    >
      <span style={{ width: 88, flexShrink: 0, fontSize: 12.5, color: 'var(--ink-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>
      <span style={{ flex: 1, height: 10, background: 'var(--bg-3)', borderRadius: 5, overflow: 'hidden' }}>
        <span className="bar-reveal" style={{ display: 'block', height: '100%', width: `${max ? (value / max) * 100 : 0}%`, background: color }} />
      </span>
      <span style={{ width: 34, flexShrink: 0, textAlign: 'right', fontSize: 12, fontWeight: 700, color }}>{value}</span>
    </Tag>
  )
}

function SectionTitle({ children }) {
  return <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--ink)', fontFamily: 'var(--serif)', margin: '24px 0 10px' }}>{children}</div>
}

export default function StatsView({ onSelectPerson, onSelectBook }) {
  const [data, setData] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    apiGet('/stats')
      .then(d => { if (!cancelled) setData(d) })
      .catch(e => { if (!cancelled) { console.warn('[Stats] 통계 로드 실패', e); setFailed(true) } })
    return () => { cancelled = true }
  }, [])

  if (failed) {
    return <div style={{ color: 'var(--danger)', padding: 24, background: 'var(--bg-0)', height: '100%' }}>통계를 불러오지 못했습니다.</div>
  }
  if (!data) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: 'var(--bg-0)' }}>
        <Spinner />
      </div>
    )
  }

  const topPersons = data.topPersons.slice(0, TOP_N)
  const longestJourneys = data.longestJourneys.slice(0, TOP_N)
  const maxTop = topPersons[0]?.count || 1
  const maxJourney = longestJourneys[0]?.stopCount || 1
  const maxEra = Math.max(...data.eraDistribution.map(e => e.count), 1)
  const maxChapter = Math.max(...data.books.map(b => b.chapterCount), 1)

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
      <div style={{ maxWidth: 640, margin: '0 auto', padding: '16px 16px 64px' }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--ink)', fontFamily: 'var(--serif)' }}>성경 통계</h2>
        <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginTop: 4 }}>그래프에서 집계한 수치입니다</div>

        {/* 헤드라인 총계 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8, marginTop: 16 }}>
          <StatCard label="인물" value={data.totals.persons} color={TYPE_COLOR.Person} />
          <StatCard label="사건" value={data.totals.events} color={TYPE_COLOR.Event} />
          <StatCard label="장소" value={data.totals.places} color={TYPE_COLOR.Place} />
          <StatCard label="성경책" value={data.totals.books} color={TYPE_COLOR.Book} />
        </div>

        {/* 최다 등장 인물 — 참여 사건 수 기준, 클릭 시 그 인물 탐험으로 딥링크 */}
        <SectionTitle>최다 등장 인물</SectionTitle>
        <div>
          {topPersons.map(p => (
            <BarRow key={p.id} label={p.nameKo} value={p.count} max={maxTop} color={TYPE_COLOR.Person} onClick={() => onSelectPerson(p.id)} />
          ))}
        </div>

        {/* 최장 여정 — 좌표 보유 정차지 수 기준, 클릭 시 그 인물 여정으로 딥링크 */}
        <SectionTitle>최장 여정</SectionTitle>
        <div>
          {longestJourneys.map(p => (
            <BarRow key={p.id} label={p.nameKo} value={p.stopCount} max={maxJourney} color={TYPE_COLOR.Place} onClick={() => onSelectPerson(p.id)} />
          ))}
        </div>

        {/* 시대별 사건 분포 — 순수 표시(드릴다운 없음) */}
        <SectionTitle>시대별 사건 분포</SectionTitle>
        <div>
          {data.eraDistribution.map(e => (
            <BarRow key={e.era} label={e.era} value={e.count} max={maxEra} color={TYPE_COLOR.Event} />
          ))}
        </div>

        {/* 책별 장 수 — 정경 순, 클릭 시 그 책 상세로 딥링크 */}
        <SectionTitle>책별 장 수</SectionTitle>
        {['구약', '신약'].map(t => (
          <div key={t} style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)', margin: '8px 0 4px' }}>{t}</div>
            {data.books.filter(b => b.testament === t).map(b => (
              <BarRow key={b.bookId} label={b.nameKo} value={b.chapterCount} max={maxChapter} color={TYPE_COLOR.Book} onClick={() => onSelectBook(b.bookId)} />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
