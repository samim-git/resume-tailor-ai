import { getAccessToken } from '../../shared/auth/tokenStore'

export function getApiBaseUrl() {
  const raw = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000') as string
  return raw.replace(/\/+$/, '')
}

type ApiFetchOptions = Omit<RequestInit, 'headers'> & {
  headers?: Record<string, string>
  auth?: boolean
}

export async function apiFetch(path: string, options: ApiFetchOptions = {}) {
  const baseUrl = getApiBaseUrl()
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`

  const headers: Record<string, string> = {
    ...(options.headers ?? {}),
  }

  if (options.auth) {
    const token = getAccessToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(url, { ...options, headers })
  return res
}

export async function apiJson<T>(res: Response): Promise<T> {
  return (await res.json()) as T
}

