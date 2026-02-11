import { apiFetch, apiJson } from './client'
import type {
  TailorResumeRequest,
  TailorResumeResponse,
  TailoredResumeDetailResponse,
  TailoredResumeListResponse,
} from '../../features/tailor/types'

export async function listTailoredResumes(): Promise<TailoredResumeListResponse> {
  const res = await apiFetch('/resume/tailored-resumes', { method: 'GET', auth: true })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to load tailored resumes')
  return await apiJson<TailoredResumeListResponse>(res)
}

export async function createTailoredResume(req: TailorResumeRequest): Promise<TailorResumeResponse> {
  const res = await apiFetch('/resume/tailor', {
    method: 'POST',
    auth: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to tailor resume')
  return await apiJson<TailorResumeResponse>(res)
}

export async function getTailoredResume(id: string): Promise<TailoredResumeDetailResponse> {
  const res = await apiFetch(`/resume/tailored-resumes/${encodeURIComponent(id)}`, { method: 'GET', auth: true })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to load tailored resume')
  return await apiJson<TailoredResumeDetailResponse>(res)
}

