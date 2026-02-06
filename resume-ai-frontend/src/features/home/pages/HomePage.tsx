import { useNavigate } from 'react-router-dom'
import { getAccessToken } from '../../../shared/auth/tokenStore'
import './HomePage.css'

export function HomePage() {
  const navigate = useNavigate()
  const hasToken = Boolean(getAccessToken())

  function onGetStarted() {
    navigate(hasToken ? '/docs' : '/login?next=/docs')
  }

  return (
    <main className="landing">
      <section className="landing__hero">
        <p className="landing__kicker">AI-powered resume tailoring</p>
        <h1 className="landing__title">Build once. Tailor for every job.</h1>
        <p className="landing__sub">Role-specific, ATS-ready, and always truthful.</p>

        <button className="landing__cta" onClick={onGetStarted}>
          Get Started
        </button>
      </section>
    </main>
  )
}

