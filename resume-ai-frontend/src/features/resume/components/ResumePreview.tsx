import type { ResumeStructured } from '../types'
import './ResumePreview.css'

function nonEmpty(v?: string | null) {
  return Boolean(v && v.trim())
}

export function ResumePreview({ resume }: { resume: ResumeStructured }) {
  const c = resume.contact
  const contactBits = [
    nonEmpty(c.email) ? c.email : null,
    nonEmpty(c.phone) ? c.phone : null,
    nonEmpty(c.location) ? c.location : null,
    nonEmpty(c.linkedin) ? `LinkedIn: ${c.linkedin}` : null,
    nonEmpty(c.github) ? `GitHub: ${c.github}` : null,
  ].filter(Boolean) as string[]

  return (
    <article className="rp">
      <header className="rp__header">
        <div>
          <h1 className="rp__name">{resume.name || '—'}</h1>
          {resume.title ? <div className="rp__title">{resume.title}</div> : null}
        </div>
        {contactBits.length ? <div className="rp__contact">{contactBits.join(' • ')}</div> : null}
      </header>

      {resume.professional_summary ? (
        <section className="rp__section">
          <h2 className="rp__h2">Professional Summary</h2>
          <p className="rp__p">{resume.professional_summary}</p>
        </section>
      ) : null}

      {resume.experience?.length ? (
        <section className="rp__section">
          <h2 className="rp__h2">Experience</h2>
          <div className="rp__stack">
            {resume.experience.map((e, idx) => (
              <div className="rp__item" key={`${e.title ?? 'exp'}-${idx}`}>
                <div className="rp__itemTop">
                  <div className="rp__itemTitle">
                    {e.title || '—'}
                    {e.company ? <span className="rp__muted"> · {e.company}</span> : null}
                  </div>
                  {(e.start_date || e.end_date) ? (
                    <div className="rp__dates">
                      {(e.start_date || '—') + ' — ' + (e.end_date || '—')}
                    </div>
                  ) : null}
                </div>
                {e.summary ? <div className="rp__p">{e.summary}</div> : null}
                {e.responsibilities?.length ? (
                  <ul className="rp__list">
                    {e.responsibilities.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {resume.education?.length ? (
        <section className="rp__section">
          <h2 className="rp__h2">Education</h2>
          <div className="rp__stack">
            {resume.education.map((e, idx) => (
              <div className="rp__item" key={`${e.institution ?? 'edu'}-${idx}`}>
                <div className="rp__itemTop">
                  <div className="rp__itemTitle">
                    {e.degree || '—'}
                    {e.field_of_study ? <span className="rp__muted"> · {e.field_of_study}</span> : null}
                    {e.institution ? <span className="rp__muted"> · {e.institution}</span> : null}
                  </div>
                  {(e.start_date || e.end_date) ? (
                    <div className="rp__dates">
                      {(e.start_date || '—') + ' — ' + (e.end_date || '—')}
                    </div>
                  ) : null}
                </div>
                {e.notes ? <div className="rp__p">{e.notes}</div> : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {resume.skills?.length ? (
        <section className="rp__section">
          <h2 className="rp__h2">Skills</h2>
          <div className="rp__skills">
            {resume.skills.map((s, idx) => (
              <div className="rp__skillRow" key={`${s.category ?? 'skills'}-${idx}`}>
                {s.category ? <div className="rp__skillCat">{s.category}</div> : null}
                <div className="rp__skillList">{(s.skills || []).join(', ')}</div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {resume.projects?.length ? (
        <section className="rp__section">
          <h2 className="rp__h2">Projects</h2>
          <div className="rp__stack">
            {resume.projects.map((p, idx) => (
              <div className="rp__item" key={`${p.name ?? 'proj'}-${idx}`}>
                <div className="rp__itemTitle">{p.name || '—'}</div>
                {p.description ? <div className="rp__p">{p.description}</div> : null}
                {p.technologies?.length ? (
                  <div className="rp__p">
                    <span className="rp__muted">Tech:</span> {p.technologies.join(', ')}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </article>
  )
}

