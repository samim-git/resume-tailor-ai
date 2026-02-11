import type { ResumeStructured } from '../resume/types'

export type BuiltResumeSummary = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type BuiltResumeListResponse = {
  resumes: BuiltResumeSummary[]
}

export type CreateBuiltResumeRequest = {
  title?: string | null
  source: 'blank' | 'current'
  template_id?: string | null
}

export type BuiltResumeResponse = {
  id: string
  title: string
  resume: ResumeStructured
  template_id?: string | null
  created_at: string
  updated_at: string
}

export type UpdateBuiltResumeRequest = {
  title: string
  resume: ResumeStructured
  template_id?: string | null
}

