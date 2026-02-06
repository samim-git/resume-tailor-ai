import { apiFetch, apiJson } from './client'

export type LoginRequest = {
  username: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: 'bearer' | string
  expires_in_days: number
}

export type RegisterRequest = {
  fullname: string
  username: string
  password: string
}

export type RegisterResponse = {
  id: string
}

export async function login(req: LoginRequest): Promise<LoginResponse> {
  const res = await apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Login failed')
  }
  return await apiJson<LoginResponse>(res)
}

export async function register(req: RegisterRequest): Promise<RegisterResponse> {
  const res = await apiFetch('/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Registration failed')
  }
  return await apiJson<RegisterResponse>(res)
}

