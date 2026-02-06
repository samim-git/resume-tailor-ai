import { Link } from 'react-router-dom'
import './TopNav.css'

export function TopNav() {
  return (
    <header className="topnav">
      <div className="topnav__inner">
        <Link to="/" className="topnav__brand">
          ResumeTailor AI
        </Link>
      </div>
    </header>
  )
}

