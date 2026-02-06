import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { loginAndStoreToken } from '../services/authService'
import './AuthPages.css'

export function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/docs'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await loginAndStoreToken(username, password)
      navigate(next)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="authPage">
      <div className="authCard">
        <h1 className="authTitle">Welcome back</h1>
        <p className="authSubtitle">Sign in to access your documents.</p>

        <form className="authForm" onSubmit={onSubmit}>
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
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="authFooter">
          <span>Don’t have an account?</span>{' '}
          <Link className="authLink" to={`/register?next=${encodeURIComponent(next)}`}>
            Create one
          </Link>
        </div>
      </div>
    </main>
  )
}

