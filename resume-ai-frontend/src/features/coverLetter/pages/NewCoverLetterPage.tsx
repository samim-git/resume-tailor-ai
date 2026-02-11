import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { createCoverLetter } from '../../../app/api/coverLetters'
import './NewCoverLetterPage.css'

const DEFAULT_TEMPLATE = `You are writing my cover letter for this job.

- Keep it truthful (do not invent anything).
- Be professional and enthusiastic.
- Highlight the most relevant experience and skills for the job.
- Use keywords from the job description where appropriate.
`

export function NewCoverLetterPage() {
  const navigate = useNavigate()
  const token = getAccessToken()

  const [jobTitle, setJobTitle] = useState('')
  const [aiTemplate, setAiTemplate] = useState(DEFAULT_TEMPLATE)
  const [jobDesc, setJobDesc] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!token) {
    navigate('/login?next=/coverletters/new')
    return null
  }

  async function onTailor() {
    setLoading(true)
    setError(null)
    try {
      const title = (jobTitle || '').trim() || 'Cover Letter'
      await createCoverLetter({
        title,
        job_title: title,
        job_description: jobDesc,
        ai_template_message: aiTemplate,
      })
      navigate('/coverletters')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create cover letter')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="cn">
      <div className="cn__top">
        <div>
          <div className="cn__title">Add new cover letter</div>
          <div className="cn__sub">Enter job details and tailor your cover letter.</div>
        </div>
        <div className="cn__actions">
          <button className="cn__secondary" onClick={() => navigate('/coverletters')}>
            Back
          </button>
        </div>
      </div>

      {error ? <div className="cn__error">{error}</div> : null}

      <div className="cn__card">
        <label className="cn__field">
          <div className="cn__label">Job title (cover letter title)</div>
          <input
            className="cn__input"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Senior Backend Engineer"
          />
        </label>

        <label className="cn__field">
          <div className="cn__label">Job description</div>
          <textarea
            className="cn__textarea"
            rows={10}
            value={jobDesc}
            onChange={(e) => setJobDesc(e.target.value)}
            placeholder="Paste the full job description here…"
          />
        </label>

        <label className="cn__field">
          <div className="cn__label">AI prompt</div>
          <textarea
            className="cn__textarea"
            rows={8}
            value={aiTemplate}
            onChange={(e) => setAiTemplate(e.target.value)}
          />
        </label>

        <button className="cn__primary" onClick={onTailor} disabled={loading || !jobDesc.trim()}>
          {loading ? 'Generating…' : 'Tailor now'}
        </button>
      </div>
    </main>
  )
}
