import { useState } from 'react'
import { Sun, Moon } from 'lucide-react'
import { TYPE_COLOR } from './theme'

// 책등(spine) 전역 헤더 높이 — App의 사이드패널 top 오프셋 계산에 공유(ADR-0026).
export const HEADER_H = 40
// 활성 책갈피 리본이 헤더 아래로 드리워지는 깊이 — App이 이만큼 여백을 확보해 리본이 스테이지 내비 탭을 안 덮게 한다.
export const RIBBON_OVERHANG = 13

// 책갈피 리본 3부 — 어느 화면에서든 인물/성경책/투어 부(部)로 이동.
// accent: 인물·성경책은 골드(책의 금박), 투어는 기존 투어 색(Book 보라) 유지.
const RIBBONS = [
  { key: 'persons', label: '인물', accent: 'var(--gold)' },
  { key: 'books', label: '성경책', accent: 'var(--gold)' },
  { key: 'tours', label: '투어', accent: TYPE_COLOR.Book },
]

/**
 * SpineHeader — 전 화면 상시 표시되는 "책등" 헤더 (ADR-0026).
 *
 * Props:
 *   activeSection  'persons' | 'books' | 'tours' — 현재 펴고 있는 부(리본이 길게 드리워짐)
 *   onSelectSection(key)                         — 리본/제목 클릭 시 부 이동
 *   isMobile
 *
 * 테마 토글은 PersonHub에서 이관(전역 승격, ADR-0020 로직 동일).
 */
export default function SpineHeader({ activeSection, onSelectSection, isMobile }) {
  // 테마 전환은 CSS 변수만 갈아끼우므로 리렌더 불요 — state는 토글 아이콘(해/달) 표시용
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark')
  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    if (next === 'light') document.documentElement.dataset.theme = 'light'
    else delete document.documentElement.dataset.theme
    localStorage.setItem('biblemap-theme', next)
    setTheme(next)
  }

  return (
    <header style={{
      height: HEADER_H, flexShrink: 0,
      position: 'relative', zIndex: 30, // 스테이지 내비(20) 위 — 리본이 아래로 드리워진다
      display: 'flex', alignItems: 'center',
      padding: isMobile ? '0 10px 0 14px' : '0 16px 0 24px',
      background: 'var(--bg-1)',
      borderBottom: '1px solid var(--gold-dim)',
      boxShadow: 'var(--shadow-1)',
    }}>
      {/* 표제 — 책등의 제목. 클릭 시 대문(인물 목차)으로 */}
      <button
        onClick={() => onSelectSection('persons')}
        aria-label="대문으로 — BibleMap"
        style={{
          display: 'flex', alignItems: 'baseline', gap: 7,
          background: 'none', border: 'none', cursor: 'pointer', padding: 0,
        }}
      >
        <span style={{
          color: 'var(--ink)',
          fontFamily: 'var(--serif)',
          fontWeight: 700,
          fontSize: 16,
          letterSpacing: '0.02em',
        }}>
          BibleMap
        </span>
        {!isMobile && (
          <span style={{ color: 'var(--ink-faint)', fontSize: 11, letterSpacing: '0.06em' }}>
            성경 인물·장소·사건의 지도
          </span>
        )}
      </button>

      <div style={{ flex: 1 }} />

      {/* 책갈피 리본 — 헤더 위에서 드리워지고, 활성 부만 길게 내려온다 */}
      <div style={{
        display: 'flex', alignItems: 'flex-start', alignSelf: 'flex-start',
        gap: isMobile ? 5 : 8,
        marginRight: isMobile ? 8 : 14,
      }}>
        {RIBBONS.map(r => {
          const active = activeSection === r.key
          return (
            <button
              key={r.key}
              className="pressable"
              onClick={() => onSelectSection(r.key)}
              aria-current={active ? 'page' : undefined}
              style={{
                height: active ? HEADER_H + RIBBON_OVERHANG : HEADER_H + 3,
                padding: '0 11px 9px',
                display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
                border: 'none', cursor: 'pointer',
                background: active
                  ? `color-mix(in srgb, ${r.accent} 17%, var(--bg-2))`
                  : 'color-mix(in srgb, var(--ink) 5%, transparent)',
                color: active ? r.accent : 'var(--ink-faint)',
                fontFamily: 'var(--serif)',
                fontSize: 12, fontWeight: 700, letterSpacing: '0.08em',
                lineHeight: 1,
                // 리본 꼬리(하단 V자 노치)
                clipPath: 'polygon(0 0, 100% 0, 100% calc(100% - 6px), 50% 100%, 0 calc(100% - 6px))',
                // pressable의 transform을 병기 — 인라인 transition은 클래스 선언을 통째로 덮는다
                transition: 'height var(--dur-base) var(--ease-out), background var(--dur-fast), color var(--dur-fast), transform var(--dur-fast) var(--ease-out)',
              }}
            >
              {r.label}
            </button>
          )
        })}
      </div>

      {/* 테마 토글 — 라이트(Day Atlas)는 옵트인, 선택은 localStorage 유지(ADR-0020) */}
      <button
        onClick={toggleTheme}
        aria-label={theme === 'light' ? '다크 테마로 전환' : '라이트 테마로 전환'}
        title={theme === 'light' ? '다크 테마로 전환' : '라이트 테마로 전환'}
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 28, height: 28, flexShrink: 0,
          borderRadius: '50%',
          border: '1px solid var(--line-strong)',
          background: 'var(--bg-2)',
          color: 'var(--gold)',
          cursor: 'pointer',
        }}
      >
        {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
      </button>
    </header>
  )
}
