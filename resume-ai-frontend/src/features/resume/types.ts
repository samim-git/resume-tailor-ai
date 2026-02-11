export type Contact = {
  phone?: string | null
  email?: string | null
  linkedin?: string | null
  github?: string | null
  location?: string | null
}

export type EducationItem = {
  institution?: string | null
  degree?: string | null
  field_of_study?: string | null
  location?: string | null
  start_date?: string | null
  end_date?: string | null
  notes?: string | null
}

export type ExperienceItem = {
  title?: string | null
  company?: string | null
  company_address?: string | null
  start_date?: string | null
  end_date?: string | null
  summary?: string | null
  responsibilities: string[]
}

export type ProjectItem = {
  name?: string | null
  description?: string | null
  technologies: string[]
  link?: string | null
  github?: string | null
  demo?: string | null
}

export type SkillCategory = {
  category?: string | null
  skills: string[]
}

export type ResumeStructured = {
  name?: string | null
  title?: string | null
  contact: Contact
  professional_summary?: string | null
  education: EducationItem[]
  experience: ExperienceItem[]
  projects: ProjectItem[]
  skills: SkillCategory[]
}

export type CurrentResumeResponse = {
  resume: ResumeStructured | null
}

