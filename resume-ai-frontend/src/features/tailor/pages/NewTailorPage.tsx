import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { createTailoredResume } from '../../../app/api/tailoredResumes'
import './NewTailorPage.css'

const DEFAULT_TEMPLATE = `You are tailoring my resume for this job.

- Keep it truthful (do not invent anything).
- Prefer concise, impact-driven bullet points.
- Emphasize the most relevant experience and skills for the job.
- Use keywords from the job description where appropriate.
`

export function NewTailorPage() {
  const navigate = useNavigate()
  const token = getAccessToken()

  const [jobTitle, setJobTitle] = useState('')
  const [jobDesc, setJobDesc] = useState('')
  const [aiTemplate, setAiTemplate] = useState(DEFAULT_TEMPLATE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!token) {
    navigate('/login?next=/tailorresume/new')
    return null
  }

  async function onTailor() {
    setLoading(true)
    setError(null)
    try {
      const title = (jobTitle || '').trim() || 'Tailored Resume'
      const job_title = title
      await createTailoredResume({
        title,
        job_title,
        job_description: jobDesc,
        ai_template_message: aiTemplate,
      })
      navigate('/tailorresume')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to tailor resume')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="tn">
      <div className="tn__top">
        <div>
          <div className="tn__title">Add new tailored resume</div>
          <div className="tn__sub">Paste the job description and tailor your resume.</div>
        </div>
        <div className="tn__actions">
          <button className="tn__secondary" onClick={() => navigate('/tailorresume')}>
            Back
          </button>
        </div>
      </div>

      {error ? <div className="tn__error">{error}</div> : null}

      <div className="tn__card">
        <label className="tn__field">
          <div className="tn__label">Job title</div>
          <input className="tn__input" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="e.g. Senior Backend Engineer" />
        </label>

        <label className="tn__field">
          <div className="tn__label">Job description</div>
          <textarea className="tn__textarea" rows={10} value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} placeholder="Paste the full job description here…" />
        </label>

        <label className="tn__field">
          <div className="tn__label">AI template message</div>
          <textarea className="tn__textarea" rows={8} value={aiTemplate} onChange={(e) => setAiTemplate(e.target.value)} />
        </label>

        <button className="tn__primary" onClick={onTailor} disabled={loading || !jobDesc.trim()}>
          {loading ? 'Tailoring…' : 'Tailor now'}
        </button>
      </div>
    </main>
  )
}

