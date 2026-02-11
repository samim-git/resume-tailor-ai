import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { clearAccessToken, getAccessToken } from '../../../shared/auth/tokenStore'
import { apiFetch } from '../../../app/api/client'
import { getCurrentResume } from '../../../app/api/resume'
import { createResumeTemplate, listResumeTemplates } from '../../../app/api/templates'
import type { ResumeStructured } from '../../resume/types'
import { ResumePreview } from '../../resume/components/ResumePreview'
import type { BlockType, ResumeTemplateSummary } from '../../templates/types'
import './DocsPage.css'

function filenameFromContentDisposition(v: string | null): string | null {
  if (!v) return null
  // examples:
  // attachment; filename="My Resume.pdf"
  // attachment; filename=resume.pdf
  const m = v.match(/filename\*?=(?:UTF-8''|")?([^\";]+)"?/i)
  if (!m?.[1]) return null
  try {
    return decodeURIComponent(m[1])
  } catch {
    return m[1]
  }
}

export function DocsPage() {
  const navigate = useNavigate()
  const token = getAccessToken()
  const [active, setActive] = useState<'resume' | 'cover'>('resume')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resume, setResume] = useState<ResumeStructured | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [templates, setTemplates] = useState<ResumeTemplateSummary[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(false)
  const [templatesError, setTemplatesError] = useState<string | null>(null)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('default')

  const [templateModalOpen, setTemplateModalOpen] = useState(false)
  const [tplName, setTplName] = useState('My Template')
  const [tplPrimary, setTplPrimary] = useState('#00BBF9')
  const [tplDefault, setTplDefault] = useState(false)
  const [tplMargins, setTplMargins] = useState({ top: 6, right: 6, bottom: 8, left: 6 })
  const [tplBlocks, setTplBlocks] = useState<BlockType[]>([
    'header',
    'summary',
    'skills',
    'experience',
    'education',
    'projects',
  ])
  const [tplSaving, setTplSaving] = useState(false)

  function onLogout() {
    clearAccessToken()
    navigate('/')
  }

  async function onDownloadResume() {
    setDownloading(true)
    setError(null)
    try {
      const qs =
        selectedTemplateId && selectedTemplateId !== 'default'
          ? `?template_id=${encodeURIComponent(selectedTemplateId)}`
          : ''
      const res = await apiFetch(`/resume/export/current/pdf${qs}`, {
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
      setError(e instanceof Error ? e.message : 'Failed to download resume')
    } finally {
      setDownloading(false)
    }
  }

  async function loadTemplates() {
    setTemplatesLoading(true)
    setTemplatesError(null)
    try {
      const data = await listResumeTemplates()
      setTemplates(data.templates ?? [])
    } catch (e) {
      setTemplatesError(e instanceof Error ? e.message : 'Failed to load templates')
    } finally {
      setTemplatesLoading(false)
    }
  }

  async function onCreateTemplate() {
    setTplSaving(true)
    setTemplatesError(null)
    try {
      const req = {
        name: tplName.trim() || 'Untitled Template',
        version: 1,
        is_default: tplDefault,
        theme: {
          primary_color: tplPrimary,
          page_margin_top_mm: tplMargins.top,
          page_margin_right_mm: tplMargins.right,
          page_margin_bottom_mm: tplMargins.bottom,
          page_margin_left_mm: tplMargins.left,
        },
        blocks: tplBlocks.map((t) => ({ type: t, props: {}, style: {} })),
      }
      await createResumeTemplate(req)
      setTemplateModalOpen(false)
      await loadTemplates()
      if (tplDefault) setSelectedTemplateId('default')
    } catch (e) {
      setTemplatesError(e instanceof Error ? e.message : 'Failed to create template')
    } finally {
      setTplSaving(false)
    }
  }

  function moveBlock(idx: number, dir: -1 | 1) {
    const next = [...tplBlocks]
    const j = idx + dir
    if (j < 0 || j >= next.length) return
    ;[next[idx], next[j]] = [next[j], next[idx]]
    setTplBlocks(next)
  }

  if (!token) {
    return (
      <main className="docs">
        <div className="docs__card">
          <h1 className="docs__title">You’re not signed in</h1>
          <p className="docs__subtitle">Login to access your documents.</p>
          <button className="docs__button" onClick={() => navigate('/login?next=/docs')}>
            Go to Login
          </button>
        </div>
      </main>
    )
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      if (active !== 'resume') return
      setLoading(true)
      setError(null)
      try {
        const data = await getCurrentResume()
        if (cancelled) return
        setResume(data.resume ?? null)
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
  }, [active])

  useEffect(() => {
    if (!token) return
    if (active !== 'resume') return
    loadTemplates()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, token])

  return (
    <main className="docs">
      <div className="dash">
        <aside className="dash__sidebar">
          <div className="dash__sidebarTitle">Documents</div>
          <button
            className={`dash__navItem ${active === 'resume' ? 'isActive' : ''}`}
            onClick={() => setActive('resume')}
          >
            Resume
          </button>
          <button
            className={`dash__navItem ${active === 'cover' ? 'isActive' : ''}`}
            onClick={() => navigate('/coverletters')}
          >
            Cover Letter
          </button>
        </aside>

        <section className="dash__content">
          <div className="dash__topbar">
            <div className="dash__title">{active === 'resume' ? 'Resume' : 'Cover Letter'}</div>
            <div className="dash__topActions">
              <button className="dash__secondary" onClick={onLogout}>
                Logout
              </button>
              {active === 'resume' ? (
                <>
                  <select
                    className="dash__select"
                    value={selectedTemplateId}
                    onChange={(e) => setSelectedTemplateId(e.target.value)}
                    disabled={templatesLoading}
                    aria-label="Resume template"
                    title={templatesError ? templatesError : 'Select a template'}
                  >
                    <option value="default">Default template</option>
                    {templates.map((t) => (
                      <option value={t.id} key={t.id}>
                        {t.name}
                        {t.is_default ? ' (default)' : ''}
                      </option>
                    ))}
                  </select>
                  <button className="dash__secondary" onClick={() => setTemplateModalOpen(true)}>
                    Add Template
                  </button>
                  <button className="dash__secondary" onClick={() => navigate('/resume/builder')}>
                    Resume Builder
                  </button>
                  <button className="dash__secondary" onClick={onDownloadResume} disabled={downloading}>
                    {downloading ? 'Downloading…' : 'Download Resume'}
                  </button>
                </>
              ) : null}
              <button className="dash__primary" onClick={() => navigate('/tailorresume')}>
                Tailored Resumes
              </button>
            </div>
          </div>

          {templateModalOpen ? (
            <div className="modalOverlay" role="dialog" aria-modal="true" aria-label="Add template">
              <div className="modalCard">
                <div className="modalHeader">
                  <div className="modalTitle">Add Template</div>
                  <button className="modalClose" onClick={() => setTemplateModalOpen(false)} aria-label="Close">
                    ×
                  </button>
                </div>

                <div className="modalGrid">
                  <label className="modalField">
                    <div className="modalLabel">Template name</div>
                    <input className="modalInput" value={tplName} onChange={(e) => setTplName(e.target.value)} />
                  </label>

                  <label className="modalField">
                    <div className="modalLabel">Primary color</div>
                    <input
                      className="modalInput"
                      type="color"
                      value={tplPrimary}
                      onChange={(e) => setTplPrimary(e.target.value)}
                    />
                  </label>

                  <label className="modalField modalFieldFull">
                    <div className="modalLabel">Page margins (mm)</div>
                    <div className="modalRow">
                      <input
                        className="modalInput"
                        type="number"
                        min={0}
                        step={1}
                        value={tplMargins.top}
                        onChange={(e) => setTplMargins({ ...tplMargins, top: Number(e.target.value) })}
                        placeholder="Top"
                      />
                      <input
                        className="modalInput"
                        type="number"
                        min={0}
                        step={1}
                        value={tplMargins.right}
                        onChange={(e) => setTplMargins({ ...tplMargins, right: Number(e.target.value) })}
                        placeholder="Right"
                      />
                      <input
                        className="modalInput"
                        type="number"
                        min={0}
                        step={1}
                        value={tplMargins.bottom}
                        onChange={(e) => setTplMargins({ ...tplMargins, bottom: Number(e.target.value) })}
                        placeholder="Bottom"
                      />
                      <input
                        className="modalInput"
                        type="number"
                        min={0}
                        step={1}
                        value={tplMargins.left}
                        onChange={(e) => setTplMargins({ ...tplMargins, left: Number(e.target.value) })}
                        placeholder="Left"
                      />
                    </div>
                  </label>

                  <label className="modalCheck modalFieldFull">
                    <input type="checkbox" checked={tplDefault} onChange={(e) => setTplDefault(e.target.checked)} />
                    Set as default template
                  </label>

                  <div className="modalField modalFieldFull">
                    <div className="modalLabel">Section order</div>
                    <div className="blockList">
                      {tplBlocks.map((b, idx) => (
                        <div className="blockRow" key={`${b}-${idx}`}>
                          <div className="blockName">{b}</div>
                          <div className="blockActions">
                            <button className="blockBtn" onClick={() => moveBlock(idx, -1)} disabled={idx === 0}>
                              ↑
                            </button>
                            <button
                              className="blockBtn"
                              onClick={() => moveBlock(idx, 1)}
                              disabled={idx === tplBlocks.length - 1}
                            >
                              ↓
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {templatesError ? <div className="modalError">{templatesError}</div> : null}

                <div className="modalFooter">
                  <button className="dash__secondary" onClick={() => setTemplateModalOpen(false)}>
                    Cancel
                  </button>
                  <button className="dash__primary" onClick={onCreateTemplate} disabled={tplSaving}>
                    {tplSaving ? 'Saving…' : 'Save template'}
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          {active === 'cover' ? null : loading ? (
            <div className="dash__empty">
              <p className="dash__emptyText">Loading your resume…</p>
            </div>
          ) : error ? (
            <div className="dash__empty">
              <h2 className="dash__emptyTitle">Couldn’t load resume</h2>
              <p className="dash__emptyText">{error}</p>
            </div>
          ) : !resume ? (
            <div className="dash__empty">
              <h2 className="dash__emptyTitle">Resume not added yet</h2>
              <p className="dash__emptyText">Upload your resume PDF or enter your details manually to get started.</p>
              <div className="dash__actions">
                <button className="dash__primary" onClick={() => navigate('/resume/upload')}>
                  Upload resume
                </button>
                <button className="dash__secondary" onClick={() => navigate('/resume/manual')}>
                  Enter manually
                </button>
              </div>
            </div>
          ) : (
            <ResumePreview resume={resume} />
          )}
        </section>
      </div>
    </main>
  )
}

