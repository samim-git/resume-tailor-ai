import { apiFetch, apiJson } from './client'
import type { CurrentResumeResponse } from '../../features/resume/types'

export async function getCurrentResume(): Promise<CurrentResumeResponse> {
  const res = await apiFetch('/resume/current', { method: 'GET', auth: true })
  if (res.status === 404) return { resume: null }
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Failed to load resume')
  }
  return await apiJson<CurrentResumeResponse>(res)
}

