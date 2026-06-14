// 공유 API 클라이언트 — 모든 프론트 fetch의 단일 베이스 URL + GET 헬퍼.
// 프로덕션은 VITE_API_URL=/api(빌드타임 주입)로 nginx 프록시(/api → api:8000)를 탄다.
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// GET → JSON. 비-OK 응답이면 status로 reject(기존 각 파일의 Promise.reject(r.status)와 동일 시맨틱).
// 요청 취소(AbortError)는 fetch에서 그대로 전파 — 호출부가 e.name === 'AbortError'로 구분한다.
export async function apiGet(path, { signal } = {}) {
  const res = await fetch(API_BASE + path, { signal })
  if (!res.ok) throw res.status
  return res.json()
}
