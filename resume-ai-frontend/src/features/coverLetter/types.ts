export type TailoredCoverLetterSummary = {
  id: string
  title: string
  job_title: string
  created_at: string
  updated_at: string
}

export type TailoredCoverLetterListResponse = {
  cover_letters: TailoredCoverLetterSummary[]
}

export type TailoredCoverLetterDetailResponse = {
  id: string
  title: string
  job_title: string
  tailored_content: string
  created_at: string
  updated_at: string
}

export type TailorCoverLetterRequest = {
  title: string
  job_title: string
  job_description: string
  ai_template_message?: string | null
}

export type TailorCoverLetterResponse = {
  id: string
  title: string
  job_title: string
  tailored_content: string
}
