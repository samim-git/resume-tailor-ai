import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { clearAccessToken, getAccessToken } from '../../../shared/auth/tokenStore'
import { getCurrentResume } from '../../../app/api/resume'
import type { ResumeStructured } from '../../resume/types'
import { ResumePreview } from '../../resume/components/ResumePreview'
import './DocsPage.css'

export function DocsPage() {
  const navigate = useNavigate()
  const token = getAccessToken()
  const [active, setActive] = useState<'resume' | 'cover'>('resume')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resume, setResume] = useState<ResumeStructured | null>(null)

  function onLogout() {
    clearAccessToken()
    navigate('/')
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
            onClick={() => setActive('cover')}
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
              <button className="dash__primary" onClick={() => navigate('/tailorresume')}>
                New Tailor
              </button>
            </div>
          </div>

          {active === 'cover' ? (
            <div className="dash__empty">
              <h2 className="dash__emptyTitle">Cover letters coming next</h2>
              <p className="dash__emptyText">This section will show your cover letter drafts and versions.</p>
            </div>
          ) : loading ? (
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

