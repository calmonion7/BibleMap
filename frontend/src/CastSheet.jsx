// 설정화 개발 시트 — #/cast (ADR 260823-190821, task#307 S1).
// 저작 에이전트는 자기 그림을 못 본다(ADR 260822-072153와 같은 문제의식) — 이 화면이 그 눈이다.
// 사용자 화면 어디서도 이 라우트로의 링크가 없다(§4: 설정화는 사용자 화면에 노출하지 않는다).
//
// 두 층을 분리해 렌더한다:
//   인물 정본(cast/*.jsx)       — 강제 컴포넌트. 호출 규약(숫자 리터럴 cx·cy·scale·delay,
//                                  transform·조건 분기 금지)은 lib.jsx 저작 규약 참조.
//   지물 참고 도상(cast/props/*.jsx) — 비강제. 자체 완결 컴포넌트(props 없음), 장면이 import하지 않는다.
// import.meta.glob로 열거하므로 파일을 추가하면 이 화면에 자동으로 실린다 — 명단을 여기 박지 않는다.
// props/ 서브디렉터리는 별도 glob으로 분리해야 한다 — 합치면 지물이 "안 쓴 인물 정본"으로 잡혀
// B12(정본 사용 강제) 게이트가 거짓 빨강이 된다(공통 맥락 "디렉터리 규약" 참조).
const castModules = import.meta.glob('./sketches/cast/*.jsx', { eager: true })
const propModules = import.meta.glob('./sketches/cast/props/*.jsx', { eager: true })

// 세 배율 — 주역/보조/원경. S2가 이 화면으로 "세 배율에서 실루엣이 무너지지 않는가"를 판정한다
// (plan.md S1). 잠정값이다 — 실제 장면 배선(S4)에서 쓰이는 실측 scale이 나오면 재개정 대상.
const SCALES = [
  { label: '주역', scale: 1.0 },
  { label: '보조', scale: 0.7 },
  { label: '원경', scale: 0.45 },
]

function nameFromPath(path) {
  return path.match(/\/([^/]+)\.jsx$/)?.[1] ?? path
}

// 기본 내보내기 없는 모듈은 조용히 걸러내고 경고만 남긴다(§1.2 로깅 규약 — 비치명적 실패는 console.warn).
function loadEntries(modules, tag) {
  const out = []
  for (const [path, mod] of Object.entries(modules)) {
    if (!mod?.default) { console.warn(`[CastSheet] ${tag} 기본 내보내기 없음 — 건너뜀: ${path}`); continue }
    out.push({ name: nameFromPath(path), aliases: Array.isArray(mod.aliases) ? mod.aliases : null, Comp: mod.default })
  }
  return out.sort((a, b) => a.name.localeCompare(b.name))
}

const CARD = {
  border: '1px solid var(--line)', borderRadius: 'var(--r-m)', background: 'var(--bg-1)',
  padding: 14, display: 'flex', flexDirection: 'column', gap: 8, boxSizing: 'border-box',
}
const GRID = { display: 'flex', flexWrap: 'wrap', gap: 14 }
const EMPTY = { color: 'var(--ink-faint)', fontSize: 13, padding: '4px 0 12px' }
const SECTION_TITLE = { fontFamily: 'var(--serif)', fontSize: 16, color: 'var(--ink)', margin: '0 0 4px' }
const SECTION_DESC = { fontSize: 12, color: 'var(--ink-faint)', margin: '0 0 10px', maxWidth: '65ch' }

// 인물 정본 카드 — 같은 컴포넌트를 세 배율로 나란히(3배율 실루엣 회귀 판정용).
function CastCard({ name, aliases, Comp }) {
  return (
    <div style={CARD}>
      <div style={{ fontFamily: 'var(--serif)', fontSize: 14, color: 'var(--ink)' }}>
        {name}
        {aliases && <span style={{ color: 'var(--ink-faint)', fontSize: 12 }}> ({aliases.join(' / ')})</span>}
      </div>
      <div style={{ display: 'flex', gap: 10, overflowX: 'auto' }}>
        {SCALES.map(({ label, scale }) => (
          <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, flexShrink: 0, width: 'clamp(70px, 26vw, 150px)' }}>
            <svg viewBox="0 0 120 64" style={{ width: '100%', height: 'auto', aspectRatio: '120 / 64', display: 'block', background: 'var(--bg-2)', borderRadius: 6 }}
              fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <Comp cx={60} cy={34} scale={scale} delay={0} />
            </svg>
            <div style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{label} × {scale}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// 지물 참고 도상 카드 — 자체 완결 컴포넌트를 그대로 렌더(props 없음, 배율 비교 대상 아님).
function PropCard({ name, Comp }) {
  return (
    <div style={CARD}>
      <div style={{ fontFamily: 'var(--serif)', fontSize: 14, color: 'var(--ink)' }}>{name}</div>
      <div style={{ overflowX: 'auto' }}><Comp /></div>
    </div>
  )
}

export default function CastSheet() {
  const cast = loadEntries(castModules, '인물 정본')
  const propItems = loadEntries(propModules, '지물 참고 도상')
  return (
    <div data-cast-sheet style={{ padding: 16, maxWidth: 960, margin: '0 auto', boxSizing: 'border-box' }}>
      <div style={{
        border: '1px solid var(--gold-dim)', borderRadius: 'var(--r-s)', background: 'var(--bg-2)',
        color: 'var(--ink-dim)', fontSize: 12, padding: '8px 12px', marginBottom: 16,
      }}>
        개발 전용 화면입니다 — 사용자 화면 어디에도 이 페이지로 오는 링크가 없습니다. 주소창에 직접
        <code style={{ margin: '0 4px' }}>#/cast</code>를 입력해야만 열립니다(ADR 260823-190821).
      </div>

      <h2 style={SECTION_TITLE}>인물 정본</h2>
      <p style={SECTION_DESC}>
        머리 윤곽·머리카락·수염·머리쓰개만 강제 컴포넌트로 정본화한다. 이목구비는 슬롯으로 비워
        장면별로 저작하므로 <strong>얼굴 없이 렌더되는 것이 정상</strong>이다.
      </p>
      {cast.length === 0
        ? <div style={EMPTY}>아직 정본이 없다 — frontend/src/sketches/cast/*.jsx를 추가하면 자동으로 실린다.</div>
        : <div style={GRID}>{cast.map(c => <CastCard key={c.name} {...c} />)}</div>}

      <h2 style={{ ...SECTION_TITLE, marginTop: 24 }}>지물 참고 도상</h2>
      <p style={SECTION_DESC}>
        반복 배경·지물의 비강제 참고 도상 — 컴포넌트가 아니고 장면이 import하지 않는다. 저작자가 보고 그린다.
      </p>
      {propItems.length === 0
        ? <div style={EMPTY}>아직 참고 도상이 없다 — frontend/src/sketches/cast/props/*.jsx를 추가하면 자동으로 실린다.</div>
        : <div style={GRID}>{propItems.map(p => <PropCard key={p.name} {...p} />)}</div>}
    </div>
  )
}
