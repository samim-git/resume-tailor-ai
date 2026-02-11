import { apiFetch, apiJson } from './client'
import type {
  CreateResumeTemplateRequest,
  ResumeTemplateListResponse,
  ResumeTemplateResponse,
  UpdateResumeTemplateRequest,
} from '../../features/templates/types'

export async function listResumeTemplates(): Promise<ResumeTemplateListResponse> {
  const res = await apiFetch('/resume/templates', { method: 'GET', auth: true })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Failed to load templates')
  }
  return await apiJson<ResumeTemplateListResponse>(res)
}

export async function getResumeTemplate(templateId: string): Promise<ResumeTemplateResponse> {
  const res = await apiFetch(`/resume/templates/${encodeURIComponent(templateId)}`, { method: 'GET', auth: true })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Failed to load template')
  }
  return await apiJson<ResumeTemplateResponse>(res)
}

export async function createResumeTemplate(req: CreateResumeTemplateRequest): Promise<ResumeTemplateResponse> {
  const res = await apiFetch('/resume/templates', {
    method: 'POST',
    auth: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Failed to create template')
  }
  return await apiJson<ResumeTemplateResponse>(res)
}

export async function updateResumeTemplate(
  templateId: string,
  req: UpdateResumeTemplateRequest,
): Promise<ResumeTemplateResponse> {
  const res = await apiFetch(`/resume/templates/${encodeURIComponent(templateId)}`, {
    method: 'PUT',
    auth: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Failed to update template')
  }
  return await apiJson<ResumeTemplateResponse>(res)
}

export async function duplicateResumeTemplate(templateId: string): Promise<ResumeTemplateResponse> {
  const res = await apiFetch(`/resume/templates/${encodeURIComponent(templateId)}/duplicate`, {
    method: 'POST',
    auth: true,
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Failed to duplicate template')
  }
  return await apiJson<ResumeTemplateResponse>(res)
}

