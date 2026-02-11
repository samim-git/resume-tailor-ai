import type { ResumeStructured } from '../resume/types'

export type TailoredResumeSummary = {
  id: string
  title: string
  job_title: string
  created_at: string
  updated_at: string
}

export type TailoredResumeListResponse = {
  resumes: TailoredResumeSummary[]
}

export type TailoredResumeDetailResponse = {
  id: string
  title: string
  job_title: string
  tailored_prof: ResumeStructured
  created_at: string
  updated_at: string
}

export type TailorResumeRequest = {
  job_title: string
  title: string
  job_description: string
  ai_template_message?: string | null
}

export type TailorResumeResponse = {
  id: string
  title: string
  job_title: string
  tailored_prof: ResumeStructured
}

