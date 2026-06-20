const style = `@keyframes spin { to { transform: rotate(360deg) } }`
export default function Spinner({ size = 28, color = 'rgba(255,255,255,0.5)' }) {
  return (
    <>
      <style>{style}</style>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        border: `3px solid ${color}22`,
        borderTopColor: color,
        animation: 'spin 0.7s linear infinite',
        margin: '0 auto',
      }} />
    </>
  )
}
