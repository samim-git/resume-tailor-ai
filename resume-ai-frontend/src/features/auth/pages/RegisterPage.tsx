import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { registerThenLogin } from '../services/authService'
import './AuthPages.css'

export function RegisterPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/docs'

  const [fullname, setFullname] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await registerThenLogin(fullname, username, password)
      navigate(next)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="authPage">
      <div className="authCard">
        <h1 className="authTitle">Create your account</h1>
        <p className="authSubtitle">Start tailoring your resume with AI.</p>

        <form className="authForm" onSubmit={onSubmit}>
          <label className="authLabel">
            Full name
            <input className="authInput" value={fullname} onChange={(e) => setFullname(e.target.value)} />
          </label>

          <label className="authLabel">
            Username
            <input className="authInput" value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>

          <label className="authLabel">
            Password
            <input
              className="authInput"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          {error ? <div className="authError">{error}</div> : null}

          <button className="authButton" disabled={loading}>
            {loading ? 'Creating…' : 'Create account'}
          </button>
        </form>

        <div className="authFooter">
          <span>Already have an account?</span>{' '}
          <Link className="authLink" to={`/login?next=${encodeURIComponent(next)}`}>
            Sign in
          </Link>
        </div>
      </div>
    </main>
  )
}

