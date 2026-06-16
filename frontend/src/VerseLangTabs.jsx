// 절 본문 언어 전환 세그먼트 탭(한국어 | 영어). 공유 verseLang 상태에 바인딩 —
// 한 곳에서 바꾸면 타임라인·SidePanel의 모든 본문이 함께 전환된다(App.jsx verseLang).
function VerseLangTabs({ verseLang, setVerseLang, color = '#7c8db0' }) {
  return (
    <div style={{
      display: 'inline-flex', border: `1px solid ${color}`,
      borderRadius: 999, overflow: 'hidden',
    }}>
      {[['ko', '한국어'], ['en', '영어']].map(([k, label]) => {
        const active = verseLang === k
        return (
          <button
            key={k}
            onClick={(e) => { e.stopPropagation(); setVerseLang(k) }}
            style={{
              padding: '1px 9px', border: 'none', cursor: 'pointer', font: 'inherit',
              fontSize: 10, fontWeight: active ? 700 : 500,
              background: active ? color : 'transparent',
              color: active ? '#fff' : color,
            }}
          >{label}</button>
        )
      })}
    </div>
  )
}

export default VerseLangTabs
