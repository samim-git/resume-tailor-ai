import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { listCoverLetters } from '../../../app/api/coverLetters'
import type { TailoredCoverLetterSummary } from '../types'
import './CoverLetterListPage.css'

export function CoverLetterListPage() {
  const navigate = useNavigate()
  const token = getAccessToken()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [coverLetters, setCoverLetters] = useState<TailoredCoverLetterSummary[]>([])

  if (!token) {
    navigate('/login?next=/coverletters')
    return null
  }

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await listCoverLetters()
      setCoverLetters(data.cover_letters ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load cover letters')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <main className="cl">
      <div className="cl__top">
        <div>
          <div className="cl__title">Cover Letters</div>
          <div className="cl__sub">Your cover letter history.</div>
        </div>
        <div className="cl__actions">
          <button className="cl__secondary" onClick={() => navigate('/docs')}>
            Back to Docs
          </button>
          <button className="cl__primary" onClick={() => navigate('/coverletters/new')}>
            + Add new
          </button>
        </div>
      </div>

      {error ? <div className="cl__error">{error}</div> : null}

      {loading ? (
        <div className="cl__card">Loading…</div>
      ) : coverLetters.length === 0 ? (
        <div className="cl__card">
          <div className="cl__emptyTitle">No cover letters yet</div>
          <div className="cl__emptyText">Click “+ Add new” to create a tailored cover letter for a job.</div>
        </div>
      ) : (
        <div className="cl__list">
          {coverLetters.map((c) => (
            <button key={c.id} className="cl__item" onClick={() => navigate(`/coverletters/${c.id}`)}>
              <div className="cl__itemTitle">{c.title || c.job_title || 'Untitled'}</div>
              <div className="cl__itemMeta">
                Job: {c.job_title || '—'} · Updated: {new Date(c.updated_at).toLocaleString()}
              </div>
            </button>
          ))}
        </div>
      )}
    </main>
  )
}
