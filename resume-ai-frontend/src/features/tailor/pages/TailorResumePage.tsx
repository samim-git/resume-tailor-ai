import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { listTailoredResumes } from '../../../app/api/tailoredResumes'
import type { TailoredResumeSummary } from '../types'
import './TailorResumePage.css'

export function TailorResumePage() {
  const navigate = useNavigate()
  const token = getAccessToken()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resumes, setResumes] = useState<TailoredResumeSummary[]>([])

  if (!token) {
    navigate('/login?next=/tailorresume')
    return null
  }

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await listTailoredResumes()
      setResumes(data.resumes ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load tailored resumes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <main className="tr">
      <div className="tr__top">
        <div>
          <div className="tr__title">Tailored Resumes</div>
          <div className="tr__sub">Your tailoring history.</div>
        </div>
        <div className="tr__actions">
          <button className="tr__secondary" onClick={() => navigate('/docs')}>
            Back to Docs
          </button>
          <button className="tr__primary" onClick={() => navigate('/tailorresume/new')}>
            + Add new
          </button>
        </div>
      </div>

      {error ? <div className="tr__error">{error}</div> : null}

      {loading ? (
        <div className="tr__card">Loading…</div>
      ) : resumes.length === 0 ? (
        <div className="tr__card">
          <div className="tr__emptyTitle">No tailored history</div>
          <div className="tr__emptyText">Click “+ Add new” to tailor your resume for a job.</div>
        </div>
      ) : (
        <div className="tr__list">
          {resumes.map((r) => (
            <button key={r.id} className="tr__item" onClick={() => navigate(`/tailorresume/${r.id}`)}>
              <div className="tr__itemTitle">{r.title || r.job_title || 'Untitled'}</div>
              <div className="tr__itemMeta">
                Job: {r.job_title || '—'} · Updated: {new Date(r.updated_at).toLocaleString()}
              </div>
            </button>
          ))}
        </div>
      )}
    </main>
  )
}

