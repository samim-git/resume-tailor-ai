export type BlockType = 'header' | 'summary' | 'skills' | 'experience' | 'education' | 'projects'

export type TemplateTheme = {
  primary_color: string
  page_margin_top_mm: number
  page_margin_right_mm: number
  page_margin_bottom_mm: number
  page_margin_left_mm: number
  pdf_scale?: number
}

export type TemplateBlock = {
  type: BlockType
  props: Record<string, unknown>
  style: Record<string, unknown>
}

export type ResumeTemplateSchema = {
  name: string
  version: number
  is_default: boolean
  theme: TemplateTheme
  blocks: TemplateBlock[]
}

export type ResumeTemplateSummary = {
  id: string
  name: string
  version: number
  is_default: boolean
  created_at: string
  updated_at: string
}

export type ResumeTemplateListResponse = {
  templates: ResumeTemplateSummary[]
}

export type CreateResumeTemplateRequest = ResumeTemplateSchema
export type UpdateResumeTemplateRequest = ResumeTemplateSchema

export type ResumeTemplateResponse = {
  id: string
  template: ResumeTemplateSchema
}

