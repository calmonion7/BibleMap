import { describe, it, expect } from 'vitest'
import {
  coreBounds, ringLabels, ringPositions, easeOutCubic, placesToGeoJSON,
  buildEventGeoJSON, buildJourneyLineGeoJSON, journeyStopGroups,
  buildJourneyStopsGeoJSON, buildParablesMiraclesGeoJSON, buildSpiderGeoJSON,
} from './mapGeo'

const place = (id, lng, lat, extra = {}) => ({ id, lng, lat, nameKo: id, isPrimary: false, ...extra })

describe('coreBounds — outlier 제외 프레이밍', () => {
  it('4개 미만이면 null (전체 bounds 폴백)', () => {
    expect(coreBounds([])).toBeNull()
    expect(coreBounds([place('a', 35, 32), place('b', 36, 33), place('c', 37, 34)])).toBeNull()
  })

  it('거의 한 점에 모이면 null — 프레이밍 문제 없음', () => {
    const dense = [0, 1, 2, 3].map((i) => place(`p${i}`, 35 + i * 0.001, 32 + i * 0.001))
    expect(coreBounds(dense)).toBeNull()
  })

  it('제외되는 outlier가 없으면 null', () => {
    const square = [place('a', 0, 0), place('b', 1, 0), place('c', 0, 1), place('d', 1, 1)]
    expect(coreBounds(square)).toBeNull()
  })

  it('원거리 outlier는 bounds에서 빠진다', () => {
    const b = coreBounds([
      place('a', 35, 32), place('b', 35.1, 32), place('c', 35, 32.1), place('d', 35.1, 32.1),
      place('outlier', 45, 32),
    ])
    expect(b).not.toBeNull()
    expect(b.getEast()).toBeCloseTo(35.1, 6)   // outlier(45)가 빠졌다
    expect(b.getWest()).toBeCloseTo(35, 6)
    expect(b.getSouth()).toBeCloseTo(32, 6)
    expect(b.getNorth()).toBeCloseTo(32.1, 6)
  })
})

describe('easeOutCubic — 경계값', () => {
  it('0에서 0, 1에서 1', () => {
    expect(easeOutCubic(0)).toBe(0)
    expect(easeOutCubic(1)).toBe(1)
  })

  it('중간값은 단조증가하며 선형보다 앞선다 (ease-out)', () => {
    expect(easeOutCubic(0.5)).toBeCloseTo(0.875, 6)
    expect(easeOutCubic(0.25)).toBeGreaterThan(0.25)
    expect(easeOutCubic(0.75)).toBeGreaterThan(easeOutCubic(0.5))
  })
})

describe('ringPositions — 링 좌표 배치', () => {
  it('n개를 반환하고 첫 점은 lat−R (angle=−π/2 → 화면상 6시 방향)', () => {
    const pos = ringPositions(10, 20, 4, 2)
    expect(pos).toHaveLength(4)
    expect(pos[0][0]).toBeCloseTo(10, 6)      // lng 변화 없음
    expect(pos[0][1]).toBeCloseTo(18, 6)      // lat - R
  })

  it('모든 점이 중심에서 반경 R만큼 떨어져 있다', () => {
    for (const [lng, lat] of ringPositions(0, 0, 6, 3)) {
      expect(Math.hypot(lng, lat)).toBeCloseTo(3, 6)
    }
  })

  it('n=0이면 빈 배열', () => {
    expect(ringPositions(0, 0, 0, 1)).toEqual([])
  })
})

describe('ringLabels — 방사 라벨 앵커', () => {
  it('n개를 반환하고 각 항목이 anchor·offset을 갖는다', () => {
    const labels = ringLabels(32, 8)
    expect(labels).toHaveLength(8)
    for (const l of labels) {
      expect(typeof l.anchor).toBe('string')
      expect(l.offset).toHaveLength(2)
    }
  })

  it('첫 라벨은 바깥(아래) 방향 — top 앵커 + 양수 y offset이라 텍스트가 점 아래', () => {
    const [first] = ringLabels(0, 4)
    expect(first.anchor).toBe('top')
    expect(first.offset).toEqual([0, 1.2])
  })

  it('앵커가 전부 같지 않다 — 분산 배치', () => {
    expect(new Set(ringLabels(32, 8).map((l) => l.anchor)).size).toBeGreaterThan(1)
  })
})

describe('placesToGeoJSON', () => {
  it('빈 입력 → 유효한 빈 FeatureCollection', () => {
    expect(placesToGeoJSON([])).toEqual({ type: 'FeatureCollection', features: [] })
  })

  it('단독 좌표는 기본 우측 앵커', () => {
    const fc = placesToGeoJSON([place('solo', 35, 32)])
    expect(fc.features).toHaveLength(1)
    expect(fc.features[0].geometry).toEqual({ type: 'Point', coordinates: [35, 32] })
    expect(fc.features[0].properties.anchor).toBe('left')
    expect(fc.features[0].properties.offset).toEqual([1.2, 0])
  })

  it('이웃이 있으면 이웃 반대쪽으로 민다', () => {
    const fc = placesToGeoJSON([place('west', 35, 32), place('east', 36, 32)])
    // west는 east(오른쪽)의 반대인 왼쪽으로 → 'right' 앵커(텍스트가 점 왼쪽)
    expect(fc.features[0].properties.anchor).toBe('right')
    expect(fc.features[1].properties.anchor).toBe('left')
  })

  it('동일 좌표 그룹은 라벨을 방사 배치한다 (앵커 충돌 방지)', () => {
    const fc = placesToGeoJSON([place('horeb', 33.9, 28.5), place('sinai', 33.9, 28.5)])
    expect(fc.features).toHaveLength(2)
    expect(fc.features[0].properties.anchor).not.toBe(fc.features[1].properties.anchor)
  })

  it('id·label·isPrimary를 그대로 싣는다', () => {
    const fc = placesToGeoJSON([place('p1', 35, 32, { nameKo: '예루살렘', isPrimary: true })])
    expect(fc.features[0].properties).toMatchObject({ id: 'p1', label: '예루살렘', isPrimary: true })
  })
})

describe('buildEventGeoJSON', () => {
  it('빈 입력 → 빈 FeatureCollection', () => {
    expect(buildEventGeoJSON([], [], [])).toEqual({ type: 'FeatureCollection', features: [] })
  })

  it('positions·anchors를 인덱스로 짝지어 싣는다', () => {
    const fc = buildEventGeoJSON(
      [{ id: 'e1', nameKo: '출애굽' }, { id: 'e2', name: 'Exodus' }],
      [[1, 2], [3, 4]],
      [{ anchor: 'left', offset: [1.2, 0] }, { anchor: 'top', offset: [0, 1.2] }],
    )
    expect(fc.features).toHaveLength(2)
    expect(fc.features[0].geometry.coordinates).toEqual([1, 2])
    expect(fc.features[0].properties).toMatchObject({ id: 'e1', label: '출애굽', anchor: 'left' })
    expect(fc.features[1].properties.label).toBe('Exodus')   // nameKo 없으면 name 폴백
  })
})

describe('buildJourneyLineGeoJSON', () => {
  const stop = (lng, lat) => ({ lng, lat })

  it('빈 입력 → 빈 FeatureCollection', () => {
    expect(buildJourneyLineGeoJSON([])).toEqual({ type: 'FeatureCollection', features: [] })
  })

  it('좌표 있는 정차지가 2개 미만이면 선을 그리지 않는다', () => {
    expect(buildJourneyLineGeoJSON([stop(35, 32)]).features).toEqual([])
    expect(buildJourneyLineGeoJSON([stop(35, 32), { lng: null, lat: null }]).features).toEqual([])
  })

  it('연속 중복 좌표는 1점으로 합쳐 0길이 세그먼트를 막는다', () => {
    const fc = buildJourneyLineGeoJSON([stop(35, 32), stop(35, 32), stop(36, 32)])
    expect(fc.features[0].geometry.coordinates).toEqual([[35, 32], [36, 32]])
  })

  it('coordProgress는 0에서 1까지 단조증가한다', () => {
    const fc = buildJourneyLineGeoJSON([stop(0, 0), stop(1, 0), stop(3, 0)])
    const prog = fc.features[0].properties.coordProgress
    expect(prog[0]).toBe(0)
    expect(prog[prog.length - 1]).toBeCloseTo(1, 6)
    expect(prog[1]).toBeCloseTo(1 / 3, 6)
  })
})

describe('journeyStopGroups — 좌표 단위 그룹핑', () => {
  const stop = (lng, lat, seq, title) => ({ lng, lat, seq, title })

  it('빈 입력·null 입력 → 빈 배열', () => {
    expect(journeyStopGroups([])).toEqual([])
    expect(journeyStopGroups(null)).toEqual([])
    expect(journeyStopGroups(undefined)).toEqual([])
  })

  it('좌표 없는 정차지는 제외한다', () => {
    expect(journeyStopGroups([{ lng: null, lat: null, seq: 1 }])).toEqual([])
  })

  it('같은 좌표의 여러 사건을 한 정차지로 묶고 첫 등장 순서를 지킨다', () => {
    const groups = journeyStopGroups([
      stop(35, 32, 1, 'a'), stop(36, 33, 2, 'b'), stop(35, 32, 3, 'c'),
    ])
    expect(groups).toHaveLength(2)
    expect(groups[0]).toMatchObject({ lng: 35, lat: 32, isStart: true, isEnd: false })
    expect(groups[0].stops).toHaveLength(2)
    expect(groups[1]).toMatchObject({ lng: 36, lat: 33, isEnd: true })
  })

  it('seqLabel은 연속 구간을 압축한다 — [6,7,8,10] → "6-8, 10"', () => {
    const groups = journeyStopGroups([6, 7, 8, 10].map((n) => stop(35, 32, n, 't')))
    expect(groups[0].seqLabel).toBe('6-8, 10')
  })

  it('비연속·단일 순번도 올바로 표기한다', () => {
    expect(journeyStopGroups([9, 11].map((n) => stop(1, 1, n, 't')))[0].seqLabel).toBe('9, 11')
    expect(journeyStopGroups([stop(1, 1, 12, 't')])[0].seqLabel).toBe('12')
  })

  it('seq가 없으면 그룹 순번으로 폴백한다', () => {
    expect(journeyStopGroups([{ lng: 1, lat: 1, title: 't' }])[0].seqLabel).toBe('1')
  })

  it('title은 그룹의 마지막 정차지 것을 쓴다', () => {
    expect(journeyStopGroups([stop(1, 1, 1, '처음'), stop(1, 1, 2, '나중')])[0].title).toBe('나중')
  })
})

describe('buildJourneyStopsGeoJSON', () => {
  it('빈 입력 → 빈 FeatureCollection', () => {
    expect(buildJourneyStopsGeoJSON([])).toEqual({ type: 'FeatureCollection', features: [] })
  })

  it('그룹 인덱스를 idx로 싣는다 (activeStopIdx·JourneyList와 동일 기준)', () => {
    const fc = buildJourneyStopsGeoJSON([
      { lng: 35, lat: 32, seq: 1, title: 'a' },
      { lng: 36, lat: 33, seq: 2, title: 'b' },
      { lng: 35, lat: 32, seq: 3, title: 'c' },
    ])
    expect(fc.features).toHaveLength(2)
    expect(fc.features.map((f) => f.properties.idx)).toEqual([0, 1])
    expect(fc.features[0].properties).toMatchObject({ seqLabel: '1, 3', isStart: true })
    expect(fc.features[1].properties.isEnd).toBe(true)
  })
})

describe('buildParablesMiraclesGeoJSON', () => {
  it('빈 입력 → 빈 FeatureCollection', () => {
    expect(buildParablesMiraclesGeoJSON([])).toEqual({ type: 'FeatureCollection', features: [] })
  })

  it('좌표 없는 항목은 제외한다 (지도에 못 얹는 "가르침" 비유)', () => {
    const fc = buildParablesMiraclesGeoJSON([
      { id: 'a', type: 'miracle', name: '가나 혼인', lng: 35.3, lat: 32.7 },
      { id: 'b', type: 'parable', name: '선한 사마리아인' },
    ])
    expect(fc.features).toHaveLength(1)
    expect(fc.features[0].properties.id).toBe('a')
  })

  it('verses를 평면 문자열 하나로 합친다 (geojson-vt는 배열을 못 싣는다)', () => {
    const fc = buildParablesMiraclesGeoJSON([{
      id: 'a', type: 'parable', name: 'n', lng: 1, lat: 1,
      verses: [{ textKo: '첫 절' }, { textKo: null }, { textKo: '둘째 절' }],
    }])
    expect(fc.features[0].properties.verseText).toBe('첫 절 둘째 절')
  })

  it('없는 선택 필드는 빈 문자열로 채운다', () => {
    const fc = buildParablesMiraclesGeoJSON([{ id: 'a', type: 'parable', name: 'n', lng: 1, lat: 1 }])
    expect(fc.features[0].properties).toMatchObject({ placeName: '', note: '', verseText: '' })
  })
})

describe('buildSpiderGeoJSON', () => {
  it('빈 입력 → 빈 FeatureCollection', () => {
    expect(buildSpiderGeoJSON([], [], [])).toEqual({ type: 'FeatureCollection', features: [] })
  })

  it('원 좌표를 originalLng/Lat로 보존하면서 위치만 옮긴다', () => {
    const fc = buildSpiderGeoJSON(
      [{ properties: { id: 'p1' }, geometry: { coordinates: [35, 32] } }],
      [[35.5, 32.5]],
      [{ anchor: 'left', offset: [1.2, 0] }],
    )
    expect(fc.features[0].geometry.coordinates).toEqual([35.5, 32.5])
    expect(fc.features[0].properties).toMatchObject({
      id: 'p1', originalLng: 35, originalLat: 32, anchor: 'left',
    })
  })
})
