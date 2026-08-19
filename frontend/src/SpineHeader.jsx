import { useState } from 'react'
import { Sun, Moon, Info, Search } from 'lucide-react'
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

// 헤더 브랜드 마크 — 나침반 장미(네 방위침 = 지도/아틀라스)와 십자가(길게 뻗은 네 침이
// 십자로 읽힘)를 인라인용으로 단순화한 플랫 금색 글리프. 원반 배경 없음, 장식이라 aria-hidden.
// 색은 var(--gold) 하나로 다크·라이트(Day Atlas) 양 테마에 자동 대응.
function CompassCrossMark({ size = 24 }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      aria-hidden="true" focusable="false"
      style={{ flexShrink: 0, display: 'block' }}
    >
      {/* 대각 방위침 — 짧고 옅게, 나침반 장미의 결 */}
      <path
        fill="var(--gold)" opacity="0.45"
        d="M16.24,7.76 L13.4,12 L12,12 L12,10.6 Z
           M16.24,16.24 L12,13.4 L12,12 L13.4,12 Z
           M7.76,16.24 L12,13.4 L12,12 L10.6,12 Z
           M7.76,7.76 L10.6,12 L12,12 L12,10.6 Z"
      />
      {/* 기본 방위침 — 길고 진하게, 네 침이 십자가로 읽힌다 */}
      <path
        fill="var(--gold)"
        d="M12,1.5 L13.2,10.8 L12,12 L10.8,10.8 Z
           M22.5,12 L13.2,13.2 L12,12 L13.2,10.8 Z
           M12,22.5 L13.2,13.2 L12,12 L10.8,13.2 Z
           M1.5,12 L10.8,10.8 L12,12 L10.8,13.2 Z"
      />
      {/* 중심 허브 */}
      <circle cx="12" cy="12" r="1.4" fill="var(--gold)" />
    </svg>
  )
}

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
export default function SpineHeader({ activeSection, onSelectSection, onOpenIntro, onOpenSearch, isMobile }) {
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
          display: 'flex', alignItems: 'center', gap: isMobile ? 7 : 9,
          background: 'none', border: 'none', cursor: 'pointer', padding: 0,
        }}
      >
        <CompassCrossMark size={isMobile ? 21 : 24} />
        <span style={{ display: 'flex', alignItems: 'baseline', gap: 7 }}>
          <span style={{
            fontFamily: 'var(--serif-display)',
            fontWeight: 400, // IM Fell English는 400만 제공 — faux-bold 방지
            fontSize: 18,
            letterSpacing: '0.01em',
          }}>
            <span style={{ color: 'var(--ink)' }}>Bible</span>
            <span style={{ color: 'var(--gold)' }}>Map</span>
          </span>
          {!isMobile && (
            <span style={{ color: 'var(--ink-faint)', fontSize: 11, letterSpacing: '0.06em' }}>
              성경 인물·장소·사건의 지도
            </span>
          )}
        </span>
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

      {/* 통합 검색 진입(task#267) — 이름·구절을 한 패널에서. `/` 단축키와 같은 자리 */}
      <button
        onClick={onOpenSearch}
        aria-label="검색 열기"
        title="검색 (/)"
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 28, height: 28, flexShrink: 0,
          marginRight: isMobile ? 6 : 8,
          borderRadius: '50%',
          border: '1px solid var(--line-strong)',
          background: 'var(--bg-2)',
          color: 'var(--gold)',
          cursor: 'pointer',
        }}
      >
        <Search size={14} />
      </button>

      {/* 인트로 재열람 — 사이트 소개(task#239). 인트로를 꺼도 여기서 언제든 다시 연다 */}
      <button
        onClick={onOpenIntro}
        aria-label="사이트 소개 보기"
        title="사이트 소개 보기"
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 28, height: 28, flexShrink: 0,
          marginRight: isMobile ? 6 : 8,
          borderRadius: '50%',
          border: '1px solid var(--line-strong)',
          background: 'var(--bg-2)',
          color: 'var(--gold)',
          cursor: 'pointer',
        }}
      >
        <Info size={14} />
      </button>

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
