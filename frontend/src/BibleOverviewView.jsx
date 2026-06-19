import { useState, useEffect } from 'react'
import { apiGet } from './api'

const OT_GENRE_ORDER = ['Pentateuch', 'Historical', 'Poetry-Wisdom', 'Major Prophets', 'Minor Prophets']
const NT_GENRE_ORDER = ['Gospels', 'Acts', 'Pauline Epistles', 'General Epistles', 'Revelation']

const GENRE_META = {
  'Pentateuch':       { displayName: '율법서',    description: '하나님의 창조와 언약, 율법의 기초' },
  'Historical':       { displayName: '역사서',    description: '가나안 정복부터 포로 귀환까지의 이스라엘 역사' },
  'Poetry-Wisdom':    { displayName: '시가·지혜서', description: '예배, 지혜, 인간의 고난에 대한 성찰' },
  'Major Prophets':   { displayName: '대선지서',  description: '하나님의 심판과 구원의 예언' },
  'Minor Prophets':   { displayName: '소선지서',  description: '회개와 회복을 촉구하는 하나님의 경고' },
  'Gospels':          { displayName: '복음서',    description: '예수 그리스도의 생애, 죽음, 부활' },
  'Acts':             { displayName: '사도행전',  description: '성령 강림과 초대교회의 복음 전파' },
  'Pauline Epistles': { displayName: '바울서신',  description: '교회와 신자를 향한 바울의 신학적 가르침' },
  'General Epistles': { displayName: '일반서신',  description: '신앙과 삶에 대한 다양한 사도들의 권면' },
  'Revelation':       { displayName: '계시록',    description: '종말의 심판과 새 창조의 비전' },
}

function BookCard({ book, onSelectNode }) {
  const [hovered, setHovered] = useState(false)
  const themes = (book.themes || []).slice(0, 3)
  const keyVerse = book.keyVerseTextKo
    ? (book.keyVerseTextKo.length > 40 ? book.keyVerseTextKo.slice(0, 40) + '…' : book.keyVerseTextKo)
    : null

  return (
    <div
      onClick={() => onSelectNode(book.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: '#1e2040',
        border: `1px solid ${hovered ? '#7c9cfc' : 'rgba(124,156,252,0.2)'}`,
        borderRadius: 10,
        padding: 12,
        width: 140,
        cursor: 'pointer',
        flexShrink: 0,
        transition: 'border-color 0.15s',
      }}
    >
      <div style={{ color: '#fff', fontWeight: 600, fontSize: 14, marginBottom: 6 }}>
        {book.nameKo}
      </div>
      {themes.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: keyVerse ? 6 : 0 }}>
          {themes.map((t, i) => (
            <span
              key={i}
              style={{
                background: 'rgba(124,156,252,0.15)',
                color: '#7c9cfc',
                fontSize: 10,
                padding: '2px 7px',
                borderRadius: 999,
              }}
            >
              {t}
            </span>
          ))}
        </div>
      )}
      {keyVerse && (
        <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: 11, marginTop: 6, lineHeight: 1.4 }}>
          {keyVerse}
        </div>
      )}
    </div>
  )
}

function GenreSection({ genre, books, isFirst, onSelectNode }) {
  const meta = GENRE_META[genre] || { displayName: genre, description: '' }
  const sorted = [...books].sort((a, b) => (a.bookOrder ?? 0) - (b.bookOrder ?? 0))

  return (
    <div style={{ marginTop: isFirst ? 0 : 20 }}>
      <div style={{ marginBottom: 8 }}>
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>{meta.displayName}</span>
        {meta.description && (
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, marginLeft: 8 }}>
            {meta.description}
          </span>
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {sorted.map(book => (
          <BookCard key={book.id} book={book} onSelectNode={onSelectNode} />
        ))}
      </div>
    </div>
  )
}

function Testament({ label, genreOrder, booksByGenre, onSelectNode }) {
  const genres = genreOrder.filter(g => booksByGenre[g] && booksByGenre[g].length > 0)

  return (
    <div>
      <div style={{ color: '#fff', fontWeight: 700, fontSize: 20, marginBottom: 12 }}>{label}</div>
      {genres.map((genre, i) => (
        <GenreSection
          key={genre}
          genre={genre}
          books={booksByGenre[genre]}
          isFirst={i === 0}
          onSelectNode={onSelectNode}
        />
      ))}
    </div>
  )
}

export default function BibleOverviewView({ onSelectNode }) {
  const [booksByTestamentGenre, setBooksByTestamentGenre] = useState({ OT: {}, NT: {} })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    apiGet('/books')
      .then(data => {
        if (cancelled) return
        const grouped = { OT: {}, NT: {} }
        for (const book of data) {
          const t = book.testament
          // Support both English (OT/NT) and Korean (구약/신약) testament values
          const key = (t === 'OT' || t === '구약') ? 'OT' : (t === 'NT' || t === '신약') ? 'NT' : null
          if (!key) continue
          const g = book.genre
          if (!grouped[key][g]) grouped[key][g] = []
          grouped[key][g].push(book)
        }
        setBooksByTestamentGenre(grouped)
        setLoading(false)
      })
      .catch(err => {
        if (cancelled) return
        setError(err.message || '불러오기 실패')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div style={{ color: 'rgba(255,255,255,0.5)', padding: 24, background: '#12122a', height: '100%' }}>
        불러오는 중…
      </div>
    )
  }
  if (error) {
    return (
      <div style={{ color: '#f87171', padding: 24, background: '#12122a', height: '100%' }}>
        오류: {error}
      </div>
    )
  }

  return (
    <div style={{
      background: '#12122a',
      padding: 16,
      height: '100%',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      <Testament
        label="구약"
        genreOrder={OT_GENRE_ORDER}
        booksByGenre={booksByTestamentGenre.OT}
        onSelectNode={onSelectNode}
      />
      <div style={{ marginTop: 32 }}>
        <Testament
          label="신약"
          genreOrder={NT_GENRE_ORDER}
          booksByGenre={booksByTestamentGenre.NT}
          onSelectNode={onSelectNode}
        />
      </div>
    </div>
  )
}
