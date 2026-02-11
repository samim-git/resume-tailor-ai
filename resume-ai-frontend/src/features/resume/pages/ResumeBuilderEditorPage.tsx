import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiFetch } from '../../../app/api/client'
import { getBuiltResume, updateBuiltResume } from '../../../app/api/builtResumes'
import { getResumeTemplate, listResumeTemplates } from '../../../app/api/templates'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import type { ResumeTemplateSummary } from '../../templates/types'
import { ResumePreview } from '../components/ResumePreview'
import type { ResumeStructured } from '../types'
import './ResumeBuilderEditorPage.css'

type SectionKey = 'header' | 'contact' | 'summary' | 'skills' | 'experience' | 'education' | 'projects'

function moveItem<T>(arr: T[], idx: number, dir: -1 | 1): T[] {
  const j = idx + dir
  if (j < 0 || j >= arr.length) return arr
  const next = [...arr]
  ;[next[idx], next[j]] = [next[j], next[idx]]
  return next
}

function filenameFromContentDisposition(v: string | null): string | null {
  if (!v) return null
  const m = v.match(/filename\*?=(?:UTF-8''|")?([^\";]+)"?/i)
  if (!m?.[1]) return null
  try {
    return decodeURIComponent(m[1])
  } catch {
    return m[1]
  }
}

export function ResumeBuilderEditorPage() {
  const navigate = useNavigate()
  const { builtResumeId } = useParams()
  const token = getAccessToken()
  const id = builtResumeId ?? ''

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [downloadingTex, setDownloadingTex] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [title, setTitle] = useState('Untitled')
  const [resume, setResume] = useState<ResumeStructured | null>(null)

  const [enabled, setEnabled] = useState<Record<SectionKey, boolean>>({
    header: true,
    contact: true,
    summary: true,
    skills: true,
    experience: true,
    education: true,
    projects: true,
  })

  const [templates, setTemplates] = useState<ResumeTemplateSummary[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(false)
  const [templatesError, setTemplatesError] = useState<string | null>(null)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('default')
  const [previewPrimaryColor, setPreviewPrimaryColor] = useState<string | null>(null)

  const [projectTechDraft, setProjectTechDraft] = useState<Record<number, string>>({})
  const [experienceBulletDraft, setExperienceBulletDraft] = useState<Record<number, string>>({})

  if (!token) {
    navigate('/login?next=/resume/builder')
    return null
  }
  if (!builtResumeId) {
    navigate('/resume/builder')
    return null
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const doc = await getBuiltResume(id)
        if (cancelled) return
        setTitle(doc.title || 'Untitled')
        setResume(doc.resume)
        setSelectedTemplateId((doc.template_id || '').trim() || 'default')
      } catch (e) {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load resume')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [id])

  useEffect(() => {
    let cancelled = false
    async function loadTemplates() {
      setTemplatesLoading(true)
      setTemplatesError(null)
      try {
        const data = await listResumeTemplates()
        if (cancelled) return
        setTemplates(data.templates ?? [])
      } catch (e) {
        if (cancelled) return
        setTemplatesError(e instanceof Error ? e.message : 'Failed to load templates')
      } finally {
        if (!cancelled) setTemplatesLoading(false)
      }
    }
    loadTemplates()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadTheme() {
      const effectiveId =
        selectedTemplateId === 'default' ? templates.find((t) => t.is_default)?.id ?? null : selectedTemplateId
      if (!effectiveId || effectiveId === 'default') {
        setPreviewPrimaryColor(null)
        return
      }
      try {
        const data = await getResumeTemplate(effectiveId)
        if (cancelled) return
        setPreviewPrimaryColor((data.template?.theme?.primary_color || '').trim() || null)
      } catch {
        if (cancelled) return
        setPreviewPrimaryColor(null)
      }
    }
    loadTheme()
    return () => {
      cancelled = true
    }
  }, [selectedTemplateId, templates])

  function parseCsv(raw: string) {
    const v = (raw || '').trim()
    return v
      ? v
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
      : []
  }

  function applyDrafts(r0: ResumeStructured): ResumeStructured {
    const r: ResumeStructured = { ...r0 }
    if (r.projects?.length) {
      const nextProjects = [...r.projects]
      for (const [k, v] of Object.entries(projectTechDraft)) {
        const idx = Number(k)
        if (!Number.isFinite(idx) || idx < 0 || idx >= nextProjects.length) continue
        nextProjects[idx] = { ...nextProjects[idx], technologies: parseCsv(v) }
      }
      r.projects = nextProjects
    }
    return r
  }

  const previewResume = useMemo<ResumeStructured | null>(() => {
    if (!resume) return null
    const r: ResumeStructured = applyDrafts({ ...resume, contact: { ...resume.contact } })
    if (!enabled.header) {
      r.name = ''
      r.title = ''
    }
    if (!enabled.contact) r.contact = { email: '', phone: '', location: '', linkedin: '', github: '' }
    if (!enabled.summary) r.professional_summary = ''
    if (!enabled.skills) r.skills = []
    if (!enabled.experience) r.experience = []
    if (!enabled.education) r.education = []
    if (!enabled.projects) r.projects = []
    return r
  }, [resume, enabled, projectTechDraft])

  function toggleSection(k: SectionKey) {
    setEnabled((prev) => ({ ...prev, [k]: !prev[k] }))
  }

  function sectionHead(k: SectionKey, label: string) {
    const on = enabled[k]
    return (
      <div className="rb__cardHead">
        <div className="rb__cardTitle">{label}</div>
        <button
          type="button"
          className="rb__eyeBtn"
          onClick={() => toggleSection(k)}
          aria-label={`${on ? 'Hide' : 'Show'} ${label}`}
          title={`${on ? 'Hide' : 'Show'} ${label}`}
        >
          <i className={`fa-solid ${on ? 'fa-eye' : 'fa-eye-slash'}`} aria-hidden="true" />
        </button>
      </div>
    )
  }

  async function onSave() {
    if (!resume) return
    setSaving(true)
    setError(null)
    try {
      const template_id = selectedTemplateId && selectedTemplateId !== 'default' ? selectedTemplateId : null
      const resumeToSave = applyDrafts(resume)
      const updated = await updateBuiltResume(id, { title: title.trim() || 'Untitled', resume: resumeToSave, template_id })
      setTitle(updated.title)
      setResume(updated.resume)
      setProjectTechDraft({})
      setExperienceBulletDraft({})
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save resume')
    } finally {
      setSaving(false)
    }
  }

  async function onDownloadPdf() {
    setDownloading(true)
    setError(null)
    try {
      const qs =
        selectedTemplateId && selectedTemplateId !== 'default'
          ? `?template_id=${encodeURIComponent(selectedTemplateId)}`
          : ''
      const res = await apiFetch(`/resume/built-resumes/${encodeURIComponent(id)}/export/pdf${qs}`, {
        method: 'GET',
        auth: true,
      })
      if (!res.ok) {
        let msg = `Failed to download (HTTP ${res.status})`
        try {
          const data = (await res.json()) as { detail?: string }
          if (data?.detail) msg = data.detail
        } catch {
          // ignore
        }
        throw new Error(msg)
      }

      const blob = await res.blob()
      const dispo = res.headers.get('content-disposition')
      const filename = filenameFromContentDisposition(dispo) ?? 'resume.pdf'

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to download PDF')
    } finally {
      setDownloading(false)
    }
  }

  async function onDownloadLatex() {
    setDownloadingTex(true)
    setError(null)
    try {
      const qs =
        selectedTemplateId && selectedTemplateId !== 'default'
          ? `?template_id=${encodeURIComponent(selectedTemplateId)}`
          : ''
      const res = await apiFetch(`/resume/built-resumes/${encodeURIComponent(id)}/export/tex${qs}`, {
        method: 'GET',
        auth: true,
      })
      if (!res.ok) {
        let msg = `Failed to download (HTTP ${res.status})`
        try {
          const data = (await res.json()) as { detail?: string }
          if (data?.detail) msg = data.detail
        } catch {
          // ignore
        }
        throw new Error(msg)
      }

      const blob = await res.blob()
      const dispo = res.headers.get('content-disposition')
      const filename = filenameFromContentDisposition(dispo) ?? 'resume.tex.txt'

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to download LaTeX')
    } finally {
      setDownloadingTex(false)
    }
  }

  function addExperienceBullet(expIdx: number, text: string) {
    if (!resume) return
    const t = (text || '').trim()
    if (!t) return
    const next = [...resume.experience]
    if (!next[expIdx]) return
    const cur = next[expIdx].responsibilities || []
    next[expIdx] = { ...next[expIdx], responsibilities: [...cur, t] }
    setResume({ ...resume, experience: next })
  }

  function insertExperienceBullet(expIdx: number, afterIndex: number) {
    if (!resume) return
    const next = [...resume.experience]
    if (!next[expIdx]) return
    const cur = [...(next[expIdx].responsibilities || [])]
    cur.splice(afterIndex + 1, 0, '')
    next[expIdx] = { ...next[expIdx], responsibilities: cur }
    setResume({ ...resume, experience: next })
  }

  function updateExperienceBullet(expIdx: number, bulletIdx: number, value: string) {
    if (!resume) return
    const next = [...resume.experience]
    if (!next[expIdx]) return
    const cur = [...(next[expIdx].responsibilities || [])]
    if (bulletIdx < 0 || bulletIdx >= cur.length) return
    cur[bulletIdx] = value
    next[expIdx] = { ...next[expIdx], responsibilities: cur }
    setResume({ ...resume, experience: next })
  }

  function removeExperienceBullet(expIdx: number, bulletIdx: number) {
    if (!resume) return
    const next = [...resume.experience]
    if (!next[expIdx]) return
    const cur = [...(next[expIdx].responsibilities || [])]
    next[expIdx] = { ...next[expIdx], responsibilities: cur.filter((_, i) => i !== bulletIdx) }
    setResume({ ...resume, experience: next })
  }

  function cleanupEmptyExperienceBullets(expIdx: number) {
    if (!resume) return
    const next = [...resume.experience]
    if (!next[expIdx]) return
    const cur = [...(next[expIdx].responsibilities || [])]
    const cleaned = cur.map((s) => (s || '').trim()).filter(Boolean)
    if (cleaned.length === cur.length) return
    next[expIdx] = { ...next[expIdx], responsibilities: cleaned }
    setResume({ ...resume, experience: next })
  }

  if (loading) {
    return (
      <main className="rb">
        <div className="rb__msg">Loading…</div>
      </main>
    )
  }

  if (!resume) {
    return (
      <main className="rb">
        <div className="rb__msg">No resume found.</div>
        <button className="rb__secondary" onClick={() => navigate('/resume/builder')}>
          Back
        </button>
      </main>
    )
  }

  return (
    <main className="rb">
      <div className="rb__top">
        <div>
          <div className="rb__title">Resume Builder</div>
          <div className="rb__sub">Edit and save your built resume.</div>
        </div>
        <div className="rb__actions">
          <button className="rb__secondary" onClick={() => navigate('/resume/builder')}>
            Back to Built Resumes
          </button>
          <button className="rb__secondary" onClick={() => navigate('/docs')}>
            Back to Docs
          </button>
          <select
            className="rb__select"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
            disabled={templatesLoading}
            aria-label="Resume theme"
            title={templatesError ? templatesError : 'Select a theme'}
          >
            <option value="default">Default theme</option>
            {templates.map((t) => (
              <option value={t.id} key={t.id}>
                {t.name}
                {t.is_default ? ' (default)' : ''}
              </option>
            ))}
          </select>
          <button className="rb__secondary" onClick={onDownloadPdf} disabled={downloading}>
            {downloading ? 'Downloading…' : 'Download PDF'}
          </button>
          <button className="rb__secondary" onClick={onDownloadLatex} disabled={downloadingTex}>
            {downloadingTex ? 'Downloading…' : 'Download LaTeX'}
          </button>
          <button className="rb__secondary" onClick={onSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {error ? <div className="rb__msg">{error}</div> : null}

      <div className="rb__grid">
        <section className="rb__panel">
          <label className="rb__field rb__fieldFull">
            <div className="rb__label">Resume title</div>
            <input className="rb__input" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>

          <div className="rb__card">
            {sectionHead('header', 'Header')}
            {enabled.header ? (
              <div className="rb__formGrid">
                <label className="rb__field">
                  <div className="rb__label">Full name</div>
                  <input className="rb__input" value={resume.name ?? ''} onChange={(e) => setResume({ ...resume, name: e.target.value })} />
                </label>
                <label className="rb__field">
                  <div className="rb__label">Title</div>
                  <input className="rb__input" value={resume.title ?? ''} onChange={(e) => setResume({ ...resume, title: e.target.value })} />
                </label>
              </div>
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>

          <div className="rb__card">
            {sectionHead('contact', 'Contact')}
            {enabled.contact ? (
              <div className="rb__formGrid">
                {(
                  [
                    ['email', 'Email'],
                    ['phone', 'Phone'],
                    ['location', 'Location'],
                    ['linkedin', 'LinkedIn (URL)'],
                    ['github', 'GitHub (URL)'],
                  ] as const
                ).map(([key, label]) => (
                  <label className="rb__field" key={key}>
                    <div className="rb__label">{label}</div>
                    <input
                      className="rb__input"
                      value={(resume.contact?.[key] as string) ?? ''}
                      onChange={(e) => setResume({ ...resume, contact: { ...resume.contact, [key]: e.target.value } })}
                    />
                  </label>
                ))}
              </div>
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>

          <div className="rb__card">
            {sectionHead('summary', 'Summary')}
            {enabled.summary ? (
              <textarea
                className="rb__textarea"
                value={resume.professional_summary ?? ''}
                onChange={(e) => setResume({ ...resume, professional_summary: e.target.value })}
                rows={5}
              />
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>

          <div className="rb__card">
            {sectionHead('skills', 'Skills')}
            {enabled.skills ? (
              <>
                <div className="rb__row">
                  <button
                    className="rb__secondary"
                    onClick={() =>
                      setResume({
                        ...resume,
                        skills: [...resume.skills, { category: 'Category', skills: ['Skill 1', 'Skill 2'] }],
                      })
                    }
                  >
                    + Add skill category
                  </button>
                </div>

                {resume.skills.map((cat, idx) => (
                  <div className="rb__miniCard" key={idx}>
                    <div className="rb__miniTop">
                      <div className="rb__miniTitle">Category {idx + 1}</div>
                      <div className="rb__miniActions">
                        <button
                          type="button"
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, skills: resume.skills.filter((_, i) => i !== idx) })}
                          aria-label="Remove skill category"
                          title="Remove"
                        >
                          <i className="fa-solid fa-trash" aria-hidden="true" />
                        </button>
                      </div>
                    </div>
                    <div className="rb__formGrid">
                      <label className="rb__field">
                        <div className="rb__label">Category</div>
                        <input
                          className="rb__input"
                          value={cat.category ?? ''}
                          onChange={(e) => {
                            const next = [...resume.skills]
                            next[idx] = { ...next[idx], category: e.target.value }
                            setResume({ ...resume, skills: next })
                          }}
                        />
                      </label>
                      <label className="rb__field">
                        <div className="rb__label">Skills (comma separated)</div>
                        <input
                          className="rb__input"
                          value={(cat.skills || []).join(', ')}
                          onChange={(e) => {
                            const next = [...resume.skills]
                            next[idx] = {
                              ...next[idx],
                              skills: e.target.value
                                .split(',')
                                .map((s) => s.trim())
                                .filter(Boolean),
                            }
                            setResume({ ...resume, skills: next })
                          }}
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>

          <div className="rb__card">
            {sectionHead('experience', 'Experience')}
            {enabled.experience ? (
              <>
                <div className="rb__row">
                  <button
                    className="rb__secondary"
                    onClick={() =>
                      setResume({
                        ...resume,
                        experience: [
                          ...resume.experience,
                          {
                            company: 'Company',
                            company_address: 'City, Country',
                            title: 'Role',
                            start_date: '2023',
                            end_date: 'Present',
                            summary: '',
                            responsibilities: ['Achievement / responsibility'],
                          },
                        ],
                      })
                    }
                  >
                    + Add experience
                  </button>
                </div>

                {resume.experience.map((ex, idx) => (
                  <div className="rb__miniCard" key={idx}>
                    <div className="rb__miniTop">
                      <div className="rb__miniTitle">Experience {idx + 1}</div>
                      <div className="rb__miniActions">
                        <button className="rb__miniBtn" onClick={() => setResume({ ...resume, experience: moveItem(resume.experience, idx, -1) })} disabled={idx === 0}>
                          ↑
                        </button>
                        <button
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, experience: moveItem(resume.experience, idx, 1) })}
                          disabled={idx === resume.experience.length - 1}
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, experience: resume.experience.filter((_, i) => i !== idx) })}
                          aria-label="Remove experience"
                          title="Remove"
                        >
                          <i className="fa-solid fa-trash" aria-hidden="true" />
                        </button>
                      </div>
                    </div>

                    <div className="rb__formGrid">
                      {(
                        [
                          ['company', 'Company'],
                          ['company_address', 'Company address'],
                          ['title', 'Role title'],
                          ['start_date', 'Start date'],
                          ['end_date', 'End date'],
                        ] as const
                      ).map(([key, label]) => (
                        <label className="rb__field" key={key}>
                          <div className="rb__label">{label}</div>
                          <input
                            className="rb__input"
                            value={(ex[key] as string) ?? ''}
                            onChange={(e) => {
                              const next = [...resume.experience]
                              next[idx] = { ...next[idx], [key]: e.target.value }
                              setResume({ ...resume, experience: next })
                            }}
                          />
                        </label>
                      ))}

                      <label className="rb__field rb__fieldFull">
                        <div className="rb__label">Summary (optional)</div>
                        <textarea
                          className="rb__textarea"
                          rows={3}
                          value={ex.summary ?? ''}
                          onChange={(e) => {
                            const next = [...resume.experience]
                            next[idx] = { ...next[idx], summary: e.target.value }
                            setResume({ ...resume, experience: next })
                          }}
                        />
                      </label>

                      <label className="rb__field rb__fieldFull">
                        <div className="rb__label">Responsibilities</div>
                        <div className="rb__bullets">
                          {(ex.responsibilities || []).map((r, j) => (
                            <div className="rb__bulletRow" key={`${idx}-${j}`}>
                              <div className="rb__bulletDot">•</div>
                              <input
                                className="rb__input rb__bulletInput"
                                value={r}
                                onChange={(e) => updateExperienceBullet(idx, j, e.target.value)}
                                onBlur={() => cleanupEmptyExperienceBullets(idx)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') {
                                    e.preventDefault()
                                    insertExperienceBullet(idx, j)
                                  }
                                  if (e.key === 'Backspace' && !r) {
                                    removeExperienceBullet(idx, j)
                                  }
                                }}
                              />
                              <button
                                type="button"
                                className="rb__bulletRemove"
                                onClick={() => removeExperienceBullet(idx, j)}
                                aria-label="Remove bullet"
                                title="Remove"
                              >
                                <i className="fa-solid fa-xmark" aria-hidden="true" />
                              </button>
                            </div>
                          ))}

                          <div className="rb__bulletRow rb__bulletRowNew">
                            <div className="rb__bulletDot">•</div>
                            <input
                              className="rb__input rb__bulletInput"
                              placeholder="Type a bullet and press Enter"
                              value={experienceBulletDraft[idx] ?? ''}
                              onChange={(e) => setExperienceBulletDraft({ ...experienceBulletDraft, [idx]: e.target.value })}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault()
                                  const raw = experienceBulletDraft[idx] ?? ''
                                  const t = raw.trim()
                                  if (!t) return
                                  addExperienceBullet(idx, t)
                                  setExperienceBulletDraft({ ...experienceBulletDraft, [idx]: '' })
                                }
                              }}
                              onBlur={() => {
                                const raw = experienceBulletDraft[idx] ?? ''
                                const t = raw.trim()
                                if (!t) return
                                addExperienceBullet(idx, t)
                                setExperienceBulletDraft({ ...experienceBulletDraft, [idx]: '' })
                              }}
                            />
                            <button
                              type="button"
                              className="rb__bulletAdd"
                              onClick={() => {
                                const raw = experienceBulletDraft[idx] ?? ''
                                const t = raw.trim()
                                if (!t) return
                                addExperienceBullet(idx, t)
                                setExperienceBulletDraft({ ...experienceBulletDraft, [idx]: '' })
                              }}
                              aria-label="Add bullet"
                              title="Add"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>

          <div className="rb__card">
            {sectionHead('education', 'Education')}
            {enabled.education ? (
              <>
                <div className="rb__row">
                  <button
                    className="rb__secondary"
                    onClick={() =>
                      setResume({
                        ...resume,
                        education: [
                          ...resume.education,
                          {
                            institution: 'University',
                            degree: 'BSc',
                            field_of_study: 'Field',
                            location: 'City',
                            start_date: '2019',
                            end_date: '2023',
                            notes: '',
                          },
                        ],
                      })
                    }
                  >
                    + Add education
                  </button>
                </div>

                {resume.education.map((ed, idx) => (
                  <div className="rb__miniCard" key={idx}>
                    <div className="rb__miniTop">
                      <div className="rb__miniTitle">Education {idx + 1}</div>
                      <div className="rb__miniActions">
                        <button className="rb__miniBtn" onClick={() => setResume({ ...resume, education: moveItem(resume.education, idx, -1) })} disabled={idx === 0}>
                          ↑
                        </button>
                        <button
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, education: moveItem(resume.education, idx, 1) })}
                          disabled={idx === resume.education.length - 1}
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, education: resume.education.filter((_, i) => i !== idx) })}
                          aria-label="Remove education"
                          title="Remove"
                        >
                          <i className="fa-solid fa-trash" aria-hidden="true" />
                        </button>
                      </div>
                    </div>

                    <div className="rb__formGrid">
                      {(
                        [
                          ['institution', 'Institution'],
                          ['degree', 'Degree'],
                          ['field_of_study', 'Field of study'],
                          ['location', 'Location'],
                          ['start_date', 'Start date'],
                          ['end_date', 'End date'],
                        ] as const
                      ).map(([key, label]) => (
                        <label className="rb__field" key={key}>
                          <div className="rb__label">{label}</div>
                          <input
                            className="rb__input"
                            value={(ed[key] as string) ?? ''}
                            onChange={(e) => {
                              const next = [...resume.education]
                              next[idx] = { ...next[idx], [key]: e.target.value }
                              setResume({ ...resume, education: next })
                            }}
                          />
                        </label>
                      ))}

                      <label className="rb__field rb__fieldFull">
                        <div className="rb__label">Notes (optional)</div>
                        <textarea
                          className="rb__textarea"
                          rows={3}
                          value={ed.notes ?? ''}
                          onChange={(e) => {
                            const next = [...resume.education]
                            next[idx] = { ...next[idx], notes: e.target.value }
                            setResume({ ...resume, education: next })
                          }}
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>

          <div className="rb__card">
            {sectionHead('projects', 'Projects')}
            {enabled.projects ? (
              <>
                <div className="rb__row">
                  <button
                    className="rb__secondary"
                    onClick={() =>
                      setResume({
                        ...resume,
                        projects: [
                          ...resume.projects,
                          {
                            name: 'Project',
                            description: 'What you built…',
                            github: '',
                            demo: '',
                            link: '',
                            technologies: ['React', 'FastAPI'],
                          },
                        ],
                      })
                    }
                  >
                    + Add project
                  </button>
                </div>

                {resume.projects.map((p, idx) => (
                  <div className="rb__miniCard" key={idx}>
                    <div className="rb__miniTop">
                      <div className="rb__miniTitle">Project {idx + 1}</div>
                      <div className="rb__miniActions">
                        <button className="rb__miniBtn" onClick={() => setResume({ ...resume, projects: moveItem(resume.projects, idx, -1) })} disabled={idx === 0}>
                          ↑
                        </button>
                        <button
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, projects: moveItem(resume.projects, idx, 1) })}
                          disabled={idx === resume.projects.length - 1}
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          className="rb__miniBtn"
                          onClick={() => setResume({ ...resume, projects: resume.projects.filter((_, i) => i !== idx) })}
                          aria-label="Remove project"
                          title="Remove"
                        >
                          <i className="fa-solid fa-trash" aria-hidden="true" />
                        </button>
                      </div>
                    </div>

                    <div className="rb__formGrid">
                      <label className="rb__field">
                        <div className="rb__label">Title</div>
                        <input
                          className="rb__input"
                          value={p.name ?? ''}
                          onChange={(e) => {
                            const next = [...resume.projects]
                            next[idx] = { ...next[idx], name: e.target.value }
                            setResume({ ...resume, projects: next })
                          }}
                        />
                      </label>
                      <label className="rb__field">
                        <div className="rb__label">GitHub link</div>
                        <input
                          className="rb__input"
                          value={p.github ?? ''}
                          onChange={(e) => {
                            const next = [...resume.projects]
                            next[idx] = { ...next[idx], github: e.target.value }
                            setResume({ ...resume, projects: next })
                          }}
                        />
                      </label>
                      <label className="rb__field">
                        <div className="rb__label">Demo link</div>
                        <input
                          className="rb__input"
                          value={(p.demo ?? p.link) ?? ''}
                          onChange={(e) => {
                            const next = [...resume.projects]
                            next[idx] = { ...next[idx], demo: e.target.value, link: e.target.value }
                            setResume({ ...resume, projects: next })
                          }}
                        />
                      </label>
                      <label className="rb__field rb__fieldFull">
                        <div className="rb__label">Description</div>
                        <textarea
                          className="rb__textarea"
                          rows={3}
                          value={p.description ?? ''}
                          onChange={(e) => {
                            const next = [...resume.projects]
                            next[idx] = { ...next[idx], description: e.target.value }
                            setResume({ ...resume, projects: next })
                          }}
                        />
                      </label>
                      <label className="rb__field rb__fieldFull">
                        <div className="rb__label">Technologies (comma separated)</div>
                        <input
                          className="rb__input"
                          value={projectTechDraft[idx] ?? (p.technologies || []).join(', ')}
                          onChange={(e) => setProjectTechDraft({ ...projectTechDraft, [idx]: e.target.value })}
                          onBlur={() => {
                            const raw = (projectTechDraft[idx] ?? (p.technologies || []).join(', ')).trim()
                            const nextTech = parseCsv(raw)
                            const next = [...resume.projects]
                            next[idx] = { ...next[idx], technologies: nextTech }
                            setResume({ ...resume, projects: next })
                            const draft = { ...projectTechDraft }
                            delete draft[idx]
                            setProjectTechDraft(draft)
                          }}
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="rb__cardHidden">Hidden</div>
            )}
          </div>
        </section>

        <section className="rb__preview">
          {previewResume ? <ResumePreview resume={previewResume} primaryColor={previewPrimaryColor ?? undefined} /> : null}
        </section>
      </div>
    </main>
  )
}

