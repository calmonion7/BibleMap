import { useState, useEffect, useRef, Fragment } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLangTabs from './VerseLangTabs'
import BookmarkToggle from './BookmarkToggle'
import { paperTextStyle } from './VerseLayer'

// 본문 리더(task#205) — 장 단위 통독 화면. chapter가 null이면 장 그리드(목차), 지정되면 그 장 본문.
// 본문 데이터는 프리베이크 정본 절 사전(/book/{id}/chapter/{n}, ADR-0003·0015) — 신규 저작 0.
// 장 목차(nameKo·chapterCount·장별 개요)는 /book/{id}/chapters — 개요 오버레이 없으면 숫자 그리드 폴백(task#206).
function ChapterReader({ bookId, chapter, onSelectChapter, highlightVerseId, verseLang, setVerseLang,
  bookmarkEntry, isBookmarked, onToggleBookmark, onRecordRecent,
  isChapterRead, onToggleRead, bookReadCount }) {
  const [bookMeta, setBookMeta] = useState(null)   // { nameKo, chapterCount, chapters } — 그리드·로딩 헤더용
  const [data, setData] = useState(null)           // /book/{id}/chapter/{n} 응답
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const ctrl = new AbortController()
    let alive = true
    Promise.resolve().then(() => { if (alive) setBookMeta(null) })
    apiGet(`/book/${encodeURIComponent(bookId)}/chapters`, { signal: ctrl.signal })
      .then(d => { if (alive) setBookMeta(d) })
      .catch(e => { if (e?.name !== 'AbortError') console.warn('[ChapterReader] 장 목차 로드 실패 — 그리드 헤더 미노출', e) })
    return () => { alive = false; ctrl.abort() }
  }, [bookId])

  useEffect(() => {
    if (chapter == null) return
    const ctrl = new AbortController()
    let alive = true
    // 장 전환 리셋 — effect 동기 setState 금지 규칙 회피(WordDistributionView 선례).
    Promise.resolve().then(() => { if (alive) { setData(null); setFailed(false) } })
    apiGet(`/book/${encodeURIComponent(bookId)}/chapter/${chapter}`, { signal: ctrl.signal })
      .then(d => { if (alive) setData(d) })
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[ChapterReader] 장 본문 로드 실패', e); setFailed(true) } })
    return () => { alive = false; ctrl.abort() }
  }, [bookId, chapter])

  // 검색 결과로 들어온 절(task#267) — 본문이 그려진 뒤 그 절을 뷰포트 안으로 스크롤한다.
  const highlightRef = useRef(null)
  useEffect(() => {
    if (!highlightVerseId || !data) return
    highlightRef.current?.scrollIntoView({ block: 'center' })
  }, [highlightVerseId, data])

  const nameKo = data?.nameKo || bookMeta?.nameKo || ''
  const chapterCount = data?.chapterCount ?? bookMeta?.chapterCount ?? null

  // 저장·이어보기 라벨(task#268) — "창세기 22장" / 목차는 "창세기".
  const readerLabel = nameKo ? (chapter != null ? `${nameKo} ${chapter}장` : nameKo) : null
  // 읽기 진도(task#269)
  const readCount = bookReadCount?.(bookId) ?? 0
  const chapterRead = chapter != null && !!isChapterRead?.(chapter)

  useEffect(() => {
    if (!bookmarkEntry?.hash || !readerLabel) return
    onRecordRecent?.({ ...bookmarkEntry, label: readerLabel })
  }, [bookmarkEntry, readerLabel, onRecordRecent])

  const chapterBtnStyle = (disabled) => ({
    padding: '8px 16px', borderRadius: 999, cursor: disabled ? 'default' : 'pointer',
    border: '1px solid var(--line)', background: 'var(--bg-1)',
    color: disabled ? 'var(--ink-faint)' : 'var(--ink)', fontSize: 13, fontFamily: 'var(--serif)',
    opacity: disabled ? 0.5 : 1,
  })

  // 장 그리드(목차) — 장 개요가 있으면 "읽히는 목차"(번호+요약 행, task#206), 없으면 숫자 그리드 폴백.
  if (chapter == null) {
    const summaries = bookMeta?.chapters?.length ? bookMeta.chapters : null
    // 장 묶음(task#212) — 있으면 요약 목록에 묶음 헤더를 끼워 구조화된 개요로. 단장권·미저작권은 헤더 없이 평면.
    const sectionAt = bookMeta?.sections?.length ? new Map(bookMeta.sections.map(s => [s.startChapter, s])) : null
    return (
      <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '20px 16px 48px' }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 700, color: 'var(--ink)' }}>
              {nameKo || ' '}
            </div>
            {chapterCount != null && (
              <div style={{ fontSize: 12, color: 'var(--ink-dim)', marginTop: 4 }}>전 {chapterCount}장 — 장을 골라 읽기 시작</div>
            )}
            {/* 읽기 진도(task#269) — 진도 0이면 막대 자체를 렌더하지 않는다 */}
            {chapterCount != null && readCount > 0 && (
              <div data-reading-progress={`${readCount}/${chapterCount}`} style={{ marginTop: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--ink-faint)', marginBottom: 4 }}>
                  <span>읽은 장</span>
                  <span>{readCount}/{chapterCount}</span>
                </div>
                <div style={{ height: 4, borderRadius: 2, background: 'var(--line)', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.round((readCount / chapterCount) * 100)}%`, height: '100%', background: 'var(--gold)' }} />
                </div>
              </div>
            )}
          </div>
          {chapterCount == null ? (
            <Spinner />
          ) : summaries ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {summaries.map(e => {
                const sec = sectionAt?.get(e.chapter)
                return (
                  <Fragment key={e.chapter}>
                    {sec && (
                      <div style={{
                        display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10,
                        padding: '14px 10px 6px', marginTop: e.chapter === 1 ? 0 : 10,
                        borderBottom: '1px solid var(--line)',
                      }}>
                        <span style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: 'var(--gold)' }}>{sec.title}</span>
                        <span style={{ fontSize: 11, color: 'var(--ink-faint)', flexShrink: 0 }}>
                          {sec.startChapter === sec.endChapter ? `${sec.startChapter}장` : `${sec.startChapter}–${sec.endChapter}장`}
                        </span>
                      </div>
                    )}
                    <button
                      onClick={() => onSelectChapter(e.chapter)}
                      style={{
                        display: 'flex', alignItems: 'baseline', gap: 10, width: '100%', textAlign: 'left',
                        padding: '9px 10px', borderRadius: 8, cursor: 'pointer',
                        border: 'none', background: 'none', font: 'inherit',
                        borderLeft: '3px solid var(--gold-dim)',
                        transition: 'background var(--dur-fast)',
                      }}
                      onMouseEnter={ev => { ev.currentTarget.style.background = 'var(--bg-1)' }}
                      onMouseLeave={ev => { ev.currentTarget.style.background = 'none' }}
                    >
                      <span style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: 'var(--gold)', flexShrink: 0, minWidth: 22, textAlign: 'right' }}>{e.chapter}</span>
                      <span style={{ fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{e.summary}</span>
                      {isChapterRead?.(e.chapter) && (
                        <span data-chapter-read={e.chapter} title="읽음" style={{ marginLeft: 'auto', flexShrink: 0, color: 'var(--gold)', fontSize: 12 }}>✓</span>
                      )}
                    </button>
                  </Fragment>
                )
              })}
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(52px, 1fr))', gap: 8 }}>
              {Array.from({ length: chapterCount }, (_, i) => i + 1).map(n => (
                <button
                  key={n}
                  onClick={() => onSelectChapter(n)}
                  {...(isChapterRead?.(n) ? { 'data-chapter-read': n } : null)}
                  style={{
                    padding: '12px 0', borderRadius: 8, cursor: 'pointer',
                    border: `1px solid ${isChapterRead?.(n) ? 'var(--gold)' : 'var(--line)'}`,
                    background: 'var(--bg-1)',
                    color: isChapterRead?.(n) ? 'var(--gold)' : 'var(--ink)', fontSize: 14, fontFamily: 'var(--serif)',
                    transition: 'border-color var(--dur-fast), color var(--dur-fast)',
                  }}
                >{n}</button>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // 장 본문 — 양피지 카드(--paper*, 테마 불변) + 한/영 탭 + 이전/다음 장.
  // key={chapter}로 장 전환 시 스크롤 컨테이너 리마운트(항상 맨 위에서 시작).
  return (
    <div key={`${bookId}-${chapter}`} style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)' }}>
      <div style={{ maxWidth: 640, margin: '0 auto', padding: '16px 16px 48px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 12 }}>
          <button
            onClick={() => onSelectChapter(null)}
            style={{
              border: 'none', background: 'none', cursor: 'pointer', padding: 0,
              fontSize: 12, color: 'var(--ink-dim)', display: 'inline-flex', alignItems: 'center', gap: 4,
            }}
          >☰ 목차</button>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 700, color: 'var(--ink)' }}>
            {nameKo} {chapter}장
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} />
            {bookmarkEntry && (
              <BookmarkToggle
                saved={isBookmarked}
                onToggle={() => onToggleBookmark({ ...bookmarkEntry, label: readerLabel || bookmarkEntry.label })}
              />
            )}
          </div>
        </div>

        {/* 장 개요(task#206) — 리더 헤더 아래 한 줄, 오버레이 없으면 조용히 생략 */}
        {data?.summary && (
          <div style={{ fontSize: 12, color: 'var(--ink-dim)', textAlign: 'center', margin: '-6px 0 12px', lineHeight: 1.5 }}>
            {data.summary}
          </div>
        )}

        <div style={{
          background: 'var(--paper)', color: 'var(--paper-ink)', boxShadow: 'var(--shadow-2)',
          borderRadius: 10, padding: '20px 22px',
        }}>
          {failed ? (
            <div style={{ ...paperTextStyle, textAlign: 'center', padding: '24px 0' }}>본문을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.</div>
          ) : !data ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '32px 0' }}><Spinner /></div>
          ) : data.verses.length === 0 ? (
            <div style={{ ...paperTextStyle, textAlign: 'center', padding: '24px 0' }}>이 장에는 본문이 없어요.</div>
          ) : (
            data.verses.map(v => {
              const hit = v.verseId === highlightVerseId
              return (
                <div
                  key={v.verseId}
                  ref={hit ? highlightRef : undefined}
                  data-verse-id={v.verseId}
                  data-verse-highlight={hit ? 'true' : undefined}
                  style={{
                    ...paperTextStyle, marginBottom: 6,
                    ...(hit ? {
                      background: 'color-mix(in srgb, var(--paper-accent) 22%, transparent)',
                      borderRadius: 4, padding: '2px 6px', margin: '0 -6px 6px',
                    } : null),
                  }}
                >
                  <sup style={{ fontSize: 11, color: 'var(--paper-accent)', marginRight: 4, fontWeight: 600 }}>{v.v}</sup>
                  {verseLang === 'ko' ? v.textKo : v.textEn}
                </div>
              )
            })
          )}
        </div>

        {/* 읽음 토글(task#269) — 본문 끝에서 이 장을 읽음으로 표시 */}
        {onToggleRead && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 16 }}>
            <button
              onClick={() => onToggleRead(bookId, chapter, nameKo || null)}
              data-read-toggle={chapterRead ? 'on' : 'off'}
              aria-pressed={chapterRead}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '8px 18px', borderRadius: 999, cursor: 'pointer',
                border: `1px solid ${chapterRead ? 'var(--gold)' : 'var(--line)'}`,
                background: chapterRead ? 'color-mix(in srgb, var(--gold) 12%, var(--bg-1))' : 'var(--bg-1)',
                color: chapterRead ? 'var(--gold)' : 'var(--ink-dim)',
                fontSize: 13, fontFamily: 'var(--serif)',
              }}
            >{chapterRead ? '✓ 읽음' : '읽음으로 표시'}</button>
          </div>
        )}

        {chapterCount != null && (
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 16 }}>
            <button onClick={() => onSelectChapter(chapter - 1)} disabled={chapter <= 1} style={chapterBtnStyle(chapter <= 1)}>← 이전 장</button>
            <button onClick={() => onSelectChapter(chapter + 1)} disabled={chapter >= chapterCount} style={chapterBtnStyle(chapter >= chapterCount)}>다음 장 →</button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChapterReader
