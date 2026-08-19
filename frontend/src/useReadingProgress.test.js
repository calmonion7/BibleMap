import { describe, it, expect } from 'vitest'
import { computeResume } from './useReadingProgress'

// 이어읽기 경계(task#276) — 완독한 책이 "존재하지 않는 장"을 가리키던 결함의 회귀망.
// 이 테스트는 수정 전 소스(HEAD 0bd58a7)에서 ①·⑥이 실제로 실패함을 확인한 뒤 추가했다
// (회고 260820-003946: 기준선에서 통과하는 테스트는 아무것도 증명하지 않는다).
const GEN = 'recIFusdNl6d8dj3L'
const last = (chapter, label = '창세기') => ({ bookId: GEN, chapter, label })
const upTo = n => Array.from({ length: n }, (_, i) => i + 1)

describe('computeResume — 이어읽기 경계', () => {
  it('① 완독(1~50/전 50장)이면 이어읽기가 없다', () => {
    expect(computeResume(upTo(50), last(50), 50)).toBeNull()
  })

  it('② 1~30만 읽었으면 다음 미독 장 31장을 가리킨다', () => {
    expect(computeResume(upTo(30), last(30), 50)).toEqual({ bookId: GEN, chapter: 31, label: '창세기' })
  })

  it('③ 1,2,4장을 읽었으면 중간 공백인 3장을 가리킨다', () => {
    expect(computeResume([1, 2, 4], last(4), 50)).toMatchObject({ chapter: 3 })
  })

  it('④ 마지막 위치(last)가 없으면 이어읽기가 없다', () => {
    expect(computeResume(upTo(10), null, 50)).toBeNull()
    expect(computeResume(upTo(10), { chapter: 3 }, 50)).toBeNull()
  })

  it('⑤ 총 장 수를 모르면 이어읽기가 없다 — 없는 장을 잠깐 보여주지 않으려고 지연시킨다', () => {
    expect(computeResume(upTo(30), last(30), null)).toBeNull()
    expect(computeResume(upTo(30), last(30), undefined)).toBeNull()
    expect(computeResume(upTo(30), last(30), 0)).toBeNull()
  })

  it('⑥ 이미 오염된 저장값(총 장 수를 넘는 51장 포함)도 없는 장을 가리키지 않는다', () => {
    expect(computeResume(upTo(51), last(51), 50)).toBeNull()
  })

  it('⑦ 1장뿐인 책을 읽었으면 이어읽기가 없다', () => {
    expect(computeResume([1], last(1, '유다서'), 1)).toBeNull()
  })

  it('⑧ 읽은 장이 없으면 1장을 가리킨다', () => {
    expect(computeResume([], last(1), 50)).toMatchObject({ chapter: 1 })
  })

  it('⑨ 깨진 장 번호(0·음수·소수)는 무시하고 계산한다', () => {
    expect(computeResume([1, 2, 0, -3, 2.5], last(2), 50)).toMatchObject({ chapter: 3 })
  })
})
