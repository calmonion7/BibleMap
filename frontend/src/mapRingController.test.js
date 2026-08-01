import { describe, it, expect } from 'vitest'
import { createRingController } from './mapRingController'

// 이 모듈의 유일한 export는 맵 인스턴스·requestAnimationFrame·performance.now·apiGet에 묶인
// 클로저 팩토리라 순수 함수가 없다. 따라서 **목킹 인프라를 새로 만들지 않고** 확인 가능한 것만 덮는다:
// 생성 계약(반환 API·ref 초기화)과 아무것도 펼쳐지지 않은 상태의 조기 반환.
// 제외: 애니메이션 진행(rAF 프레임 구동)·expandPlace(네트워크 + map.project/unproject)·
//       collapse* 의 실제 setData 경로 — 전부 가짜 맵과 타이머 하네스가 필요하고, 그건 이 계획의 비목표다.
//       그 경로들은 Playwright 화면 검증이 덮는다.

// getSource를 부르면 터지는 맵 — "조기 반환이라 맵을 건드리지 않는다"를 단언으로 만든다.
const explodingMap = {
  getSource() { throw new Error('맵을 건드리면 안 되는 경로에서 getSource가 호출됨') },
  project() { throw new Error('project 호출됨') },
  unproject() { throw new Error('unproject 호출됨') },
}

const make = () => {
  const ref = { current: { stale: true } }
  const errors = []
  const ctl = createRingController(explodingMap, { expandedPlaceRef: ref, setError: (v) => errors.push(v) })
  return { ctl, ref, errors }
}

describe('createRingController — 생성 계약', () => {
  it('4개 조작 함수 + destroy를 반환한다', () => {
    const { ctl } = make()
    expect(Object.keys(ctl).sort()).toEqual(
      ['collapseRing', 'collapseSpider', 'destroy', 'expandPlace', 'spiderifyPlaces'],
    )
    for (const fn of Object.values(ctl)) expect(typeof fn).toBe('function')
  })

  it('맵 재초기화 시 공유 ref의 펼침 상태를 비운다', () => {
    const { ref } = make()
    expect(ref.current).toBeNull()
  })

  it('생성만으로는 맵을 건드리지 않는다', () => {
    expect(() => make()).not.toThrow()
  })
})

describe('펼쳐진 것이 없을 때의 조기 반환', () => {
  it('collapseRing은 아무 일도 하지 않는다 (맵 미접근)', () => {
    const { ctl } = make()
    expect(() => ctl.collapseRing()).not.toThrow()
  })

  it('collapseSpider도 아무 일도 하지 않는다', () => {
    const { ctl } = make()
    expect(() => ctl.collapseSpider()).not.toThrow()
  })

  it('여러 번 불러도 안전하다', () => {
    const { ctl } = make()
    expect(() => { ctl.collapseRing(); ctl.collapseRing(); ctl.collapseSpider() }).not.toThrow()
  })
})

describe('destroy', () => {
  it('진행 중인 애니메이션이 없어도 안전하고 멱등이다', () => {
    const { ctl } = make()
    expect(() => { ctl.destroy(); ctl.destroy() }).not.toThrow()
  })

  it('destroy 후 collapse를 불러도 터지지 않는다', () => {
    const { ctl } = make()
    ctl.destroy()
    expect(() => { ctl.collapseRing(); ctl.collapseSpider() }).not.toThrow()
  })
})
