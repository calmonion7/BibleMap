// 스테이지 하위 내비 바 — 전역 책등 헤더(ADR-0026) 밑에 붙는 9개 스테이지의 공용 껍데기.
//
// 합성형(slot) 구성이다: 9개 내비의 편차가 커서(탐험은 동적 탭 배열 + 인장 + 색 분기 + 모바일 조건부
// 보조라벨, 가계도는 PersonSymbol, 통계·주제는 lucide 아이콘, 투어는 이모지 + TYPE_COLOR.Book)
// 선언형 config로 모델링하면 "config를 해석하는 분기"가 복붙했던 분량만큼 되살아난다. 그래서 실제로
// 반복되는 스타일 3덩어리(껍데기 · 뒤로버튼 · 탭버튼 활성/비활성)만 컴포넌트로 갖고 조립은 호출부에 남긴다.
export const NAV_H = 48

const SHELL = {
  height: NAV_H, flexShrink: 0,
  display: 'flex', alignItems: 'center',
  background: 'var(--bg-1)', borderBottom: '1px solid var(--gold-dim)',
  zIndex: 20, boxShadow: 'var(--shadow-1)',
  gap: 0,
}

const BACK = {
  display: 'flex', alignItems: 'center', gap: 6,
  padding: '0 14px', height: '100%',
  background: 'none', border: 'none', cursor: 'pointer',
  color: 'var(--ink-dim)',
  borderRight: '1px solid var(--line)',
  flexShrink: 0,
}

// 우측 슬롯 행 — 탭 나열(탭형 5종)과 정적 타이틀(Title 4종)이 공유한다.
const ROW = { display: 'flex', alignItems: 'center', height: '100%' }

/**
 * onBack·backLabel — 좌측 복귀 버튼(모든 스테이지 공통). backLabel은 13px 본문 라벨.
 * lead — 복귀 버튼의 ← 뒤에 끼우는 슬롯(인장·색 있는 제목 등). 탐험 내비 전용.
 * auxLabel — lead 뒤의 11px 보조 라벨. 넘기지 않으면 미노출(모바일 인물 모드에서 인장 폭 회수).
 * children — 우측 슬롯: StageNav.Tab 나열 또는 StageNav.Title.
 * trailing — 내비 맨 오른쪽에 붙는 슬롯(저장 토글 등, task#268). 넘기지 않으면 미노출.
 */
export default function StageNav({ onBack, backLabel, lead, auxLabel, children, trailing }) {
  return (
    <div style={SHELL}>
      <button onClick={onBack} style={BACK}>
        <span style={{ fontSize: 13 }}>←</span>
        {lead}
        {backLabel && <span style={{ fontSize: 13 }}>{backLabel}</span>}
        {auxLabel && <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{auxLabel}</span>}
      </button>
      <div style={ROW}>{children}</div>
      {trailing && <div style={{ ...ROW, marginLeft: 'auto', paddingRight: 10 }}>{trailing}</div>}
    </div>
  )
}

// 하위 메뉴 탭. onClick 없으면 현재 위치를 가리키는 정적 탭(커서 default, transition 없음).
function Tab({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        // 2px 밑줄이 NAV_H 안에 들어오도록 border-box(전역 box-sizing 리셋이 없어 기본은 content-box).
        boxSizing: 'border-box',
        padding: '0 14px', height: '100%',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
        color: active ? 'var(--ink)' : 'var(--ink-faint)',
        background: 'none', cursor: onClick ? 'pointer' : 'default',
        // 단축 border를 먼저, borderBottom을 뒤에 — 순서가 뒤집히면 뒤의 단축 속성이 밑줄을 조용히
        // 되돌린다(9개 복붙본 중 5곳이 그 상태였고, 금색 활성 밑줄이 렌더되지 않던 원인).
        border: 'none',
        borderBottom: `2px solid ${active ? 'var(--gold)' : 'transparent'}`,
        transition: onClick ? 'color var(--dur-fast), border-color var(--dur-fast)' : undefined,
      }}
    >
      <Icon size={18} />
      <span style={{ fontSize: 10, lineHeight: 1 }}>{label}</span>
    </button>
  )
}

// 하위 탭이 없는 단일 페이지의 정적 타이틀. icon은 노드 슬롯(lucide·인장·이모지 무엇이든).
function Title({ icon, label, color = 'var(--ink-dim)', gap = 8 }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 14px', gap }}>
      {icon}
      <span style={{ color, fontSize: 13, fontFamily: 'var(--serif)', fontWeight: 600 }}>{label}</span>
    </div>
  )
}

StageNav.Tab = Tab
StageNav.Title = Title
