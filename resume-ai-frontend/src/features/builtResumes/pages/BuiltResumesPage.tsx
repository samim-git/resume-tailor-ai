import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { createBuiltResume, listBuiltResumes } from '../../../app/api/builtResumes'
import type { BuiltResumeSummary } from '../types'
import './BuiltResumesPage.css'

export function BuiltResumesPage() {
  const navigate = useNavigate()
  const token = getAccessToken()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resumes, setResumes] = useState<BuiltResumeSummary[]>([])

  const [createOpen, setCreateOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('Untitled')

  if (!token) {
    navigate('/login?next=/resume/builder')
    return null
  }

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await listBuiltResumes()
      setResumes(data.resumes ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load built resumes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function start(source: 'blank' | 'current') {
    setCreating(true)
    setError(null)
    try {
      const doc = await createBuiltResume({ source, title: newTitle })
      setCreateOpen(false)
      navigate(`/resume/builder/${doc.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create resume')
    } finally {
      setCreating(false)
    }
  }

  return (
    <main className="br">
      <div className="br__top">
        <div>
          <div className="br__title">Built Resumes</div>
          <div className="br__sub">Create and manage your built resumes.</div>
        </div>
        <div className="br__actions">
          <button className="br__secondary" onClick={() => navigate('/docs')}>
            Back to Docs
          </button>
          <button className="br__primary" onClick={() => setCreateOpen(true)}>
            + New
          </button>
        </div>
      </div>

      {error ? <div className="br__error">{error}</div> : null}

      {loading ? (
        <div className="br__card">Loading…</div>
      ) : resumes.length === 0 ? (
        <div className="br__card">
          <div className="br__emptyTitle">No resume yet</div>
          <div className="br__emptyText">Click “+ New” to create your first built resume.</div>
        </div>
      ) : (
        <div className="br__list">
          {resumes.map((r) => (
            <button key={r.id} className="br__item" onClick={() => navigate(`/resume/builder/${r.id}`)}>
              <div className="br__itemTitle">{r.title || 'Untitled'}</div>
              <div className="br__itemMeta">Updated: {new Date(r.updated_at).toLocaleString()}</div>
            </button>
          ))}
        </div>
      )}

      {createOpen ? (
        <div className="brModalOverlay" role="dialog" aria-modal="true" aria-label="Create resume">
          <div className="brModalCard">
            <div className="brModalHeader">
              <div className="brModalTitle">Create a resume</div>
              <button className="brModalClose" onClick={() => setCreateOpen(false)} aria-label="Close">
                ×
              </button>
            </div>

            <label className="brModalField">
              <div className="brModalLabel">Title</div>
              <input className="brModalInput" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
            </label>

            <div className="brModalBtns">
              <button className="br__secondary" onClick={() => start('blank')} disabled={creating}>
                {creating ? 'Creating…' : 'Start blank'}
              </button>
              <button className="br__primary" onClick={() => start('current')} disabled={creating}>
                {creating ? 'Creating…' : 'Load content from database'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  )
}

