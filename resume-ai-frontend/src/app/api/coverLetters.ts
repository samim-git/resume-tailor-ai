import { apiFetch, apiJson } from './client'
import type {
  TailorCoverLetterRequest,
  TailorCoverLetterResponse,
  TailoredCoverLetterDetailResponse,
  TailoredCoverLetterListResponse,
} from '../../features/coverLetter/types'

export async function listCoverLetters(): Promise<TailoredCoverLetterListResponse> {
  const res = await apiFetch('/cover-letter/tailored-letters', { method: 'GET', auth: true })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to load cover letters')
  return await apiJson<TailoredCoverLetterListResponse>(res)
}

export async function createCoverLetter(req: TailorCoverLetterRequest): Promise<TailorCoverLetterResponse> {
  const res = await apiFetch('/cover-letter/tailor', {
    method: 'POST',
    auth: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to create cover letter')
  return await apiJson<TailorCoverLetterResponse>(res)
}

export async function getCoverLetter(id: string): Promise<TailoredCoverLetterDetailResponse> {
  const res = await apiFetch(`/cover-letter/tailored-letters/${encodeURIComponent(id)}`, { method: 'GET', auth: true })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to load cover letter')
  return await apiJson<TailoredCoverLetterDetailResponse>(res)
}
