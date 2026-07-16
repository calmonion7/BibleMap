// 공유 API 클라이언트 — 모든 프론트 fetch의 단일 베이스 URL + GET 헬퍼.
// 프로덕션은 VITE_API_URL=/api(빌드타임 주입)로 nginx 프록시(/api → api:8000)를 탄다.
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// 빌드 식별자(vite.config define) — 배포마다 바뀐다. 모든 API 요청에 ?v=로 실어, 데이터가
// 바뀐 배포 직후에도 브라우저가 옛 응답(max-age=3600 캐시)을 재사용하지 않게 한다. 같은
// 배포 안에서는 값이 고정이라 1시간 캐시 이점은 유지된다.
const BUILD_ID = __BUILD_ID__

// GET → JSON. 비-OK 응답이면 status로 reject(기존 각 파일의 Promise.reject(r.status)와 동일 시맨틱).
// 요청 취소(AbortError)는 fetch에서 그대로 전파 — 호출부가 e.name === 'AbortError'로 구분한다.
export async function apiGet(path, { signal } = {}) {
  const url = API_BASE + path + (path.includes('?') ? '&' : '?') + 'v=' + BUILD_ID
  const res = await fetch(url, { signal })
  if (!res.ok) { const err = new Error(String(res.status)); err.status = res.status; throw err }
  return res.json()
}
