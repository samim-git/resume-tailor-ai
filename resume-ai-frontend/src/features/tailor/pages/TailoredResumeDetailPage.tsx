import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiFetch } from '../../../app/api/client'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import { getTailoredResume } from '../../../app/api/tailoredResumes'
import { ResumePreview } from '../../resume/components/ResumePreview'
import type { TailoredResumeDetailResponse } from '../types'
import './TailoredResumeDetailPage.css'

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

export function TailoredResumeDetailPage() {
  const navigate = useNavigate()
  const token = getAccessToken()
  const { tailoredResumeId } = useParams()
  const id = tailoredResumeId ?? ''

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [doc, setDoc] = useState<TailoredResumeDetailResponse | null>(null)

  if (!token) {
    navigate(`/login?next=/tailorresume/${encodeURIComponent(id)}`)
    return null
  }
  if (!tailoredResumeId) {
    navigate('/tailorresume')
    return null
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const d = await getTailoredResume(id)
        if (cancelled) return
        setDoc(d)
      } catch (e) {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load tailored resume')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [id])

  async function onDownloadPdf() {
    setDownloading(true)
    setError(null)
    try {
      const res = await apiFetch(`/resume/export/pdf?tailored_resume_id=${encodeURIComponent(id)}`, {
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
      const filename = filenameFromContentDisposition(dispo) ?? 'tailored_resume.pdf'

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

  return (
    <main className="td">
      <div className="td__top">
        <div>
          <div className="td__title">{doc?.title || 'Tailored resume'}</div>
          <div className="td__sub">{doc?.job_title ? `Job: ${doc.job_title}` : 'Preview'}</div>
        </div>
        <div className="td__actions">
          <button className="td__secondary" onClick={() => navigate('/tailorresume')}>
            Back
          </button>
          <button className="td__primary" onClick={onDownloadPdf} disabled={downloading || loading || !doc}>
            {downloading ? 'Downloading…' : 'Download PDF'}
          </button>
        </div>
      </div>

      {error ? <div className="td__error">{error}</div> : null}

      {loading ? (
        <div className="td__card">Loading…</div>
      ) : !doc ? (
        <div className="td__card">No resume found.</div>
      ) : (
        <ResumePreview resume={doc.tailored_prof} />
      )}
    </main>
  )
}

