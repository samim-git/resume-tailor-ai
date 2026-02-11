import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { getCoverLetter } from '../../../app/api/coverLetters'
import type { TailoredCoverLetterDetailResponse } from '../types'
import './CoverLetterDetailPage.css'

export function CoverLetterDetailPage() {
  const { coverLetterId } = useParams<{ coverLetterId: string }>()
  const navigate = useNavigate()
  const token = getAccessToken()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [letter, setLetter] = useState<TailoredCoverLetterDetailResponse | null>(null)

  if (!token) {
    navigate('/login?next=/coverletters')
    return null
  }

  useEffect(() => {
    if (!coverLetterId) return
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await getCoverLetter(coverLetterId)
        if (!cancelled) setLetter(data)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load cover letter')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [coverLetterId])

  if (loading) return <main className="cd"><div className="cd__card">Loading…</div></main>
  if (error) return <main className="cd"><div className="cd__error">{error}</div></main>
  if (!letter) return null

  return (
    <main className="cd">
      <div className="cd__top">
        <div>
          <div className="cd__title">{letter.title || letter.job_title || 'Cover Letter'}</div>
          <div className="cd__sub">Job: {letter.job_title || '—'}</div>
        </div>
        <div className="cd__actions">
          <button className="cd__secondary" onClick={() => navigate('/coverletters')}>
            Back to list
          </button>
        </div>
      </div>

      <div className="cd__card">
        <pre className="cd__content">{letter.tailored_content}</pre>
      </div>
    </main>
  )
}
