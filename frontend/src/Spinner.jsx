const style = `@keyframes spin { to { transform: rotate(360deg) } }`
export default function Spinner({ size = 28, color = 'var(--ink-faint)' }) {
  return (
    <>
      <style>{style}</style>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        // 트랙은 본색의 13% — color-mix라 hex뿐 아니라 var()·rgba도 받는다
        border: `3px solid color-mix(in srgb, ${color} 13%, transparent)`,
        borderTopColor: color,
        animation: 'spin 0.7s linear infinite',
        margin: '0 auto',
      }} />
    </>
  )
}
