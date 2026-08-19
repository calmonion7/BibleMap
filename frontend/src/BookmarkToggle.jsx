import { Bookmark } from 'lucide-react'

// 저장 토글(task#268) — 지금 보고 있는 화면을 이 기기에 저장/해제한다.
// entry = { hash, type, label }; 저장 여부는 호출부가 bookmarks에서 판정해 넘긴다.
export default function BookmarkToggle({ saved, onToggle, size = 16 }) {
  return (
    <button
      onClick={onToggle}
      aria-pressed={saved}
      aria-label={saved ? '저장 해제' : '저장하기'}
      title={saved ? '저장 해제' : '저장하기 — 이 기기에 저장됩니다'}
      data-bookmark-toggle={saved ? 'on' : 'off'}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 30, height: 30, flexShrink: 0,
        borderRadius: '50%',
        border: '1px solid var(--line-strong)',
        background: 'var(--bg-2)',
        color: saved ? 'var(--gold)' : 'var(--ink-faint)',
        cursor: 'pointer',
        transition: 'color var(--dur-fast)',
      }}
    >
      <Bookmark size={size} fill={saved ? 'var(--gold)' : 'none'} />
    </button>
  )
}
