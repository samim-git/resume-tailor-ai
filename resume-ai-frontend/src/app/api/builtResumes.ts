import { apiFetch, apiJson } from './client'
import type {
  BuiltResumeListResponse,
  BuiltResumeResponse,
  CreateBuiltResumeRequest,
  UpdateBuiltResumeRequest,
} from '../../features/builtResumes/types'

export async function listBuiltResumes(): Promise<BuiltResumeListResponse> {
  const res = await apiFetch('/resume/built-resumes', { method: 'GET', auth: true })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to load built resumes')
  return await apiJson<BuiltResumeListResponse>(res)
}

export async function createBuiltResume(req: CreateBuiltResumeRequest): Promise<BuiltResumeResponse> {
  const res = await apiFetch('/resume/built-resumes', {
    method: 'POST',
    auth: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to create built resume')
  return await apiJson<BuiltResumeResponse>(res)
}

export async function getBuiltResume(id: string): Promise<BuiltResumeResponse> {
  const res = await apiFetch(`/resume/built-resumes/${encodeURIComponent(id)}`, { method: 'GET', auth: true })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to load built resume')
  return await apiJson<BuiltResumeResponse>(res)
}

export async function updateBuiltResume(id: string, req: UpdateBuiltResumeRequest): Promise<BuiltResumeResponse> {
  const res = await apiFetch(`/resume/built-resumes/${encodeURIComponent(id)}`, {
    method: 'PUT',
    auth: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error((await res.text()) || 'Failed to save built resume')
  return await apiJson<BuiltResumeResponse>(res)
}

