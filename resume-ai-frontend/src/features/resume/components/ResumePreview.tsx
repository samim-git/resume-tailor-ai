import { Fragment, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { ResumeStructured } from '../types'
import './ResumePreview.css'

function nonEmpty(v?: string | null) {
  return Boolean(v && v.trim())
}

function joinDate(start?: string | null, end?: string | null) {
  if (!nonEmpty(start) && !nonEmpty(end)) return ''
  if (nonEmpty(start) && nonEmpty(end)) return `${start} – ${end}`
  return (start || end || '').trim()
}

function renderBoldMarkers(input: string) {
  // Normalize \\b and b\\ to \b and b\ so both single and double backslash work
  let s = (input || '').replace(/\\\\b/g, '\\b').replace(/b\\\\/g, 'b\\')
  const OPEN = '\\b'
  const CLOSE = 'b\\'
  const out: Array<string | { bold: true; text: string }> = []

  let i = 0
  while (i < s.length) {
    const openAt = s.indexOf(OPEN, i)
    if (openAt === -1) {
      out.push(s.slice(i))
      break
    }
    // plain chunk
    if (openAt > i) out.push(s.slice(i, openAt))
    const innerStart = openAt + OPEN.length
    const closeAt = s.indexOf(CLOSE, innerStart)
    if (closeAt === -1) {
      // no closing marker → treat rest as plain text (including marker)
      out.push(s.slice(openAt))
      break
    }
    const inner = s.slice(innerStart, closeAt)
    out.push({ bold: true, text: inner })
    i = closeAt + CLOSE.length
  }

  return out.map((part, idx) => {
    if (typeof part === 'string') return <span key={`t-${idx}`}>{part}</span>
    return (
      <strong key={`b-${idx}`} style={{ fontWeight: 900 }}>
        {part.text}
      </strong>
    )
  })
}

type ContactKind = 'email' | 'phone' | 'location' | 'linkedin' | 'github'

function normalizeHttpUrl(v: string) {
  const s = (v || '').trim()
  if (!s) return ''
  if (/^https?:\/\//i.test(s)) return s
  return `https://${s}`
}

type ContactItem = { kind: ContactKind; label: string; href?: string }

function ContactIcon({ kind }: { kind: ContactKind }) {
  switch (kind) {
    case 'email':
      return <i className="fa-solid fa-envelope" aria-hidden="true" />
    case 'phone':
      return <i className="fa-solid fa-phone" aria-hidden="true" />
    case 'location':
      return <i className="fa-solid fa-location-dot" aria-hidden="true" />
    case 'linkedin':
      return <i className="fa-brands fa-linkedin-in" aria-hidden="true" />
    case 'github':
      return <i className="fa-brands fa-github" aria-hidden="true" />
    default:
      return null
  }
}

type PagePlan = {
  exp: ExpSlice[]
  edu: number[]
  proj: number[]
  expHeader?: boolean
}

type ExpSlice = {
  idx: number
  from: number
  to: number
}

export function ResumePreview({ resume, primaryColor }: { resume: ResumeStructured; primaryColor?: string }) {
  // Theme hook: allow parent to control accent color via CSS variable.
  // (Used by resume builder template dropdown.)
  const c = resume.contact
  const contactItems = [
    nonEmpty(c.email) ? ({ kind: 'email', label: c.email! } as ContactItem) : null,
    nonEmpty(c.phone) ? ({ kind: 'phone', label: c.phone! } as ContactItem) : null,
    nonEmpty(c.location) ? ({ kind: 'location', label: c.location! } as ContactItem) : null,
    nonEmpty(c.linkedin)
      ? ({ kind: 'linkedin', label: 'LinkedIn', href: normalizeHttpUrl(c.linkedin!) } as ContactItem)
      : null,
    nonEmpty(c.github)
      ? ({ kind: 'github', label: 'GitHub', href: normalizeHttpUrl(c.github!) } as ContactItem)
      : null,
  ].filter(Boolean) as ContactItem[]

  const exp = resume.experience || []
  const edu = resume.education || []
  const proj = resume.projects || []

  const expClean = useMemo(() => {
    return exp.map((e) => ({
      ...e,
      responsibilities: (e.responsibilities || []).map((s) => (s || '').trim()).filter(Boolean),
    }))
  }, [exp])

  const pageRef = useRef<HTMLElement | null>(null)
  const headerRef = useRef<HTMLElement | null>(null)
  const summaryRef = useRef<HTMLElement | null>(null)
  const skillsRef = useRef<HTMLElement | null>(null)
  const expStartRef = useRef<HTMLElement | null>(null)
  const eduStartRef = useRef<HTMLElement | null>(null)
  const projStartRef = useRef<HTMLElement | null>(null)

  const expItemRefs = useRef<Array<HTMLDivElement | null>>([])
  const expCoreRefs = useRef<Array<HTMLDivElement | null>>([])
  const expListRefs = useRef<Array<HTMLUListElement | null>>([])
  const expRespRefs = useRef<Array<Array<HTMLLIElement | null>>>([])
  const eduItemRefs = useRef<Array<HTMLDivElement | null>>([])
  const projItemRefs = useRef<Array<HTMLDivElement | null>>([])

  const [pages, setPages] = useState<PagePlan[]>([
    { exp: expClean.map((_, i) => ({ idx: i, from: 0, to: 0 })), edu: edu.map((_, i) => i), proj: proj.map((_, i) => i) },
  ])

  const hasSummary = nonEmpty(resume.professional_summary)
  const hasSkills = Boolean(resume.skills?.length)

  const measureKey = useMemo(() => {
    // Any change that affects layout should recompute paging
    return JSON.stringify({
      name: resume.name,
      title: resume.title,
      contact: resume.contact,
      summary: resume.professional_summary,
      skills: resume.skills,
      exp,
      edu,
      proj,
    })
  }, [resume, exp, edu, proj])

  function renderHeader() {
    return (
      <header className="rp__header">
        <div className="rp__headerBlock">
          <div className="rp__headerMain">{resume.name || '—'}</div>
          {resume.title ? <div className="rp__headerSub">{resume.title}</div> : null}
          {contactItems.length ? (
            <div className="rp__contact" aria-label="Contact details">
              {contactItems.map((it, idx) => (
                <span className="rp__contactItem" key={`${it.kind}-${it.label}-${idx}`}>
                  <span className="rp__contactIcon">
                    <ContactIcon kind={it.kind} />
                  </span>
                  {it.href ? (
                    <a className="rp__contactLink" href={it.href} target="_blank" rel="noreferrer">
                      {it.label}
                    </a>
                  ) : (
                    <span className="rp__contactText">{it.label}</span>
                  )}
                  {idx !== contactItems.length - 1 ? (
                    <span className="rp__contactSep" aria-hidden="true">
                      |
                    </span>
                  ) : null}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </header>
    )
  }

  function renderSummarySection() {
    if (!hasSummary) return null
    return (
      <section className="rp__section">
        <div className="rp__sectionHead">
          <div className="rp__sectionTitle">Summary</div>
        </div>
        <div className="rp__text">{resume.professional_summary}</div>
      </section>
    )
  }

  function renderSkillsSection() {
    if (!hasSkills) return null
    return (
      <section className="rp__section">
        <div className="rp__sectionHead">
          <div className="rp__sectionTitle">Skills</div>
        </div>
        <div className="rp__skillsBlock">
          {resume.skills!.map((s, idx) => (
            <div className="rp__skillLine" key={`${s.category ?? 'skills'}-${idx}`}>
              {s.category ? <span className="rp__skillCat">{s.category}:</span> : null}{' '}
              <span className="rp__skillItems">{(s.skills || []).join(', ')}</span>
            </div>
          ))}
        </div>
      </section>
    )
  }

  function renderEducationItem(e: (typeof edu)[number], idx: number) {
    return (
      <div className="rp__item" key={`${e.institution ?? 'edu'}-${idx}`}>
        <div className="rp__row">
          <div className="rp__school">{e.institution || '—'}</div>
          {joinDate(e.start_date, e.end_date) ? <div className="rp__dates">{joinDate(e.start_date, e.end_date)}</div> : null}
        </div>
        <div className="rp__row rp__rowSub">
          <div className="rp__field">{[e.degree, e.field_of_study].filter(Boolean).join(' · ')}</div>
          {e.location ? <div className="rp__loc">{e.location}</div> : null}
        </div>
        {e.notes ? <div className="rp__text">{e.notes}</div> : null}
      </div>
    )
  }

  function renderProjectItem(p: (typeof proj)[number], idx: number) {
    const github = (p.github || '').trim()
    const demo = ((p.demo || p.link) || '').trim()
    const links = [
      github ? { label: 'GitHub', href: github } : null,
      demo ? { label: 'Demo', href: demo } : null,
    ].filter(Boolean) as Array<{ label: string; href: string }>

    return (
      <div className="rp__item" key={`${p.name ?? 'proj'}-${idx}`}>
        <div className="rp__company">{p.name || '—'}</div>
        {p.description ? <div className="rp__text">{p.description}</div> : null}
        {p.technologies?.length ? (
          <div className="rp__text">
            <span className="rp__muted">Tech:</span> {p.technologies.join(', ')}
          </div>
        ) : null}
        {links.length ? (
          <div className="rp__projLinks">
            {links.map((l, i) => (
              <span key={l.href}>
                <a className="rp__link" href={l.href} target="_blank" rel="noreferrer">
                  {l.label}
                </a>
                {i !== links.length - 1 ? <span className="rp__linkSep"> | </span> : null}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    )
  }

  useLayoutEffect(() => {
    // reset refs arrays to current lengths
    expItemRefs.current = expClean.map((_, i) => expItemRefs.current[i] ?? null)
    expCoreRefs.current = expClean.map((_, i) => expCoreRefs.current[i] ?? null)
    expListRefs.current = expClean.map((_, i) => expListRefs.current[i] ?? null)
    expRespRefs.current = expClean.map((e, i) => {
      const prev = expRespRefs.current[i] ?? []
      const n = e.responsibilities?.length ?? 0
      return Array.from({ length: n }, (_, j) => prev[j] ?? null)
    })
    eduItemRefs.current = edu.map((_, i) => eduItemRefs.current[i] ?? null)
    projItemRefs.current = proj.map((_, i) => projItemRefs.current[i] ?? null)

    const pageEl = pageRef.current
    const headerEl = headerRef.current
    if (!pageEl || !headerEl) return

    const st = getComputedStyle(pageEl)
    const pageHeight = pageEl.getBoundingClientRect().height
    const paddingTop = Number.parseFloat(st.paddingTop || '0') || 0
    const paddingBottom = Number.parseFloat(st.paddingBottom || '0') || 0
    const contentMax = Math.max(200, pageHeight - paddingTop - paddingBottom)

    const headerHeight = headerEl.offsetHeight
    const summaryHeight = hasSummary ? summaryRef.current?.offsetHeight || 0 : 0
    const skillsHeight = hasSkills ? skillsRef.current?.offsetHeight || 0 : 0
    const expStartHeight = exp.length ? expStartRef.current?.offsetHeight || 0 : 0
    const eduStartHeight = edu.length ? eduStartRef.current?.offsetHeight || 0 : 0
    const projStartHeight = proj.length ? projStartRef.current?.offsetHeight || 0 : 0

    const expHeights = expItemRefs.current.map((el) => el?.offsetHeight || 0)
    const eduHeights = eduItemRefs.current.map((el) => el?.offsetHeight || 0)
    const projHeights = projItemRefs.current.map((el) => el?.offsetHeight || 0)

    const nextPages: PagePlan[] = []
    let pageIdx = 0
    let used = headerHeight

    function startNewPage() {
      pageIdx += 1
      used = 0
    }

    function ensurePage(idx: number) {
      while (nextPages.length <= idx) nextPages.push({ exp: [], edu: [], proj: [], expHeader: false })
    }

    ensurePage(0)

    // Summary + Skills stay on page 1 (PDF-like first page header block)
    used += summaryHeight + skillsHeight

    // Experience (only show section header once: on first occurrence)
    if (expClean.length) {
      let headerAdded = false
      // estimate per-slice padding from measured .rp__item
      const sampleItem = expItemRefs.current.find(Boolean) as HTMLDivElement | null
      const expPad = (() => {
        if (!sampleItem) return 20
        const cs = getComputedStyle(sampleItem)
        const pt = Number.parseFloat(cs.paddingTop || '0') || 0
        const pb = Number.parseFloat(cs.paddingBottom || '0') || 0
        return pt + pb
      })()

      const coreHeights = expCoreRefs.current.map((el) => el?.offsetHeight || 0)
      const respHeights = expRespRefs.current.map((rows) => rows.map((el) => el?.offsetHeight || 0))
      const listBaseOver = expListRefs.current.map((ul, i) => {
        if (!ul) return 0
        const sum = (respHeights[i] || []).reduce((a, b) => a + (b || 0), 0)
        return Math.max(0, ul.offsetHeight - sum)
      })
      const listMarginTop = expListRefs.current.map((ul) => {
        if (!ul) return 0
        const cs = getComputedStyle(ul)
        return Number.parseFloat(cs.marginTop || '0') || 0
      })

      for (let i = 0; i < expClean.length; i += 1) {
        const respCount = expClean[i]?.responsibilities?.length ?? 0
        const coreH = coreHeights[i] || 0

        // No responsibilities → treat as atomic block (like before)
        if (respCount === 0) {
          const h = expPad + (expHeights[i] ? coreH : coreH) // coreH already measured, expHeights kept for fallback
          const overhead = headerAdded ? 0 : expStartHeight
          if (used + overhead + h > contentMax && (headerAdded || used > 0)) {
            startNewPage()
            ensurePage(pageIdx)
          }
          if (!headerAdded) {
            used += expStartHeight
            headerAdded = true
            ensurePage(pageIdx)
            nextPages[pageIdx].expHeader = true
          }
          ensurePage(pageIdx)
          nextPages[pageIdx].exp.push({ idx: i, from: 0, to: 0 })
          used += h
          continue
        }

        // Split responsibilities across pages if needed
        let from = 0
        while (from < respCount) {
          const sectionOver = headerAdded ? 0 : expStartHeight
          const includeCore = from === 0
          const coreOver = includeCore ? coreH : 0
          const listOver = listBaseOver[i] + (includeCore ? listMarginTop[i] : 0) // continuation slices don't include margin-top
          const firstLine = respHeights[i]?.[from] || 0
          const sliceMin = expPad + coreOver + listOver + firstLine

          if (used + sectionOver + sliceMin > contentMax && (headerAdded || used > 0)) {
            startNewPage()
            ensurePage(pageIdx)
            continue
          }

          if (!headerAdded) {
            used += expStartHeight
            headerAdded = true
            ensurePage(pageIdx)
            nextPages[pageIdx].expHeader = true
          }

          used += expPad + coreOver + listOver

          let to = from
          while (to < respCount) {
            const lh = respHeights[i]?.[to] || 0
            if (to === from) {
              used += lh
              to += 1
              continue
            }
            if (used + lh > contentMax) break
            used += lh
            to += 1
          }

          ensurePage(pageIdx)
          nextPages[pageIdx].exp.push({ idx: i, from, to })

          from = to
          if (from < respCount) {
            startNewPage()
            ensurePage(pageIdx)
          }
        }
      }
    }

    // Education (only show section header once)
    if (edu.length) {
      let headerAdded = false
      for (let i = 0; i < edu.length; i += 1) {
        const h = eduHeights[i] || 0
        const overhead = headerAdded ? 0 : eduStartHeight
        if (used + overhead + h > contentMax && (headerAdded || used > 0)) {
          startNewPage()
          ensurePage(pageIdx)
        }
        const overhead2 = headerAdded ? 0 : eduStartHeight
        if (!headerAdded) {
          used += overhead2
          headerAdded = true
        }
        ensurePage(pageIdx)
        nextPages[pageIdx].edu.push(i)
        used += h
      }
    }

    // Projects (only show section header once)
    if (proj.length) {
      let headerAdded = false
      for (let i = 0; i < proj.length; i += 1) {
        const h = projHeights[i] || 0
        const overhead = headerAdded ? 0 : projStartHeight
        if (used + overhead + h > contentMax && (headerAdded || used > 0)) {
          startNewPage()
          ensurePage(pageIdx)
        }
        const overhead2 = headerAdded ? 0 : projStartHeight
        if (!headerAdded) {
          used += overhead2
          headerAdded = true
        }
        ensurePage(pageIdx)
        nextPages[pageIdx].proj.push(i)
        used += h
      }
    }

    setPages(
      nextPages.length
        ? nextPages
        : [
            {
              exp: expClean.map((_, i) => ({ idx: i, from: 0, to: 0 })),
              edu: edu.map((_, i) => i),
              proj: proj.map((_, i) => i),
              expHeader: true,
            },
          ],
    )
  }, [measureKey, expClean.length, edu.length, proj.length, hasSummary, hasSkills])

  function renderExperienceSlice(s: ExpSlice) {
    const e = expClean[s.idx]
    if (!e) return null
    const resp = e.responsibilities || []
    const showCore = s.from === 0
    const showList = s.to > s.from

    return (
      <div className="rp__item" key={`${e.company ?? e.title ?? 'exp'}-${s.idx}-${s.from}-${s.to}`}>
        {showCore ? (
          <>
            <div className="rp__row">
              <div className="rp__company">{e.company || '—'}</div>
              {e.company_address ? <div className="rp__addr">{e.company_address}</div> : null}
            </div>
            <div className="rp__row rp__rowSub">
              <div className="rp__role">{e.title || ''}</div>
              {joinDate(e.start_date, e.end_date) ? (
                <div className="rp__dates">{joinDate(e.start_date, e.end_date)}</div>
              ) : null}
            </div>
            {e.summary ? <div className="rp__text">{e.summary}</div> : null}
          </>
        ) : null}
        {showList ? (
          <ul className={`rp__list ${showCore ? '' : 'rp__listCont'}`}>
            {resp.slice(s.from, s.to).map((r, i) => (
              <li key={`${s.idx}-${s.from}-${i}`}>{renderBoldMarkers(r)}</li>
            ))}
          </ul>
        ) : null}
      </div>
    )
  }

  function renderExperienceSection(slices: ExpSlice[], showHeader: boolean) {
    const safe = slices.filter((s) => s.idx >= 0 && s.idx < exp.length && s.from >= 0 && s.to >= s.from)
    if (!safe.length) return null
    return (
      <section className="rp__section">
        {showHeader ? (
          <div className="rp__sectionHead">
            <div className="rp__sectionTitle">Experience</div>
          </div>
        ) : null}
        <div className="rp__stack">{safe.map((s) => renderExperienceSlice(s))}</div>
      </section>
    )
  }

  function renderEducationSection(indices: number[]) {
    const safe = indices.filter((i) => i >= 0 && i < edu.length)
    if (!safe.length) return null
    const showHeader = safe[0] === 0
    return (
      <section className="rp__section">
        {showHeader ? (
          <div className="rp__sectionHead">
            <div className="rp__sectionTitle">Education</div>
          </div>
        ) : null}
        <div className="rp__stack">{safe.map((i) => renderEducationItem(edu[i], i))}</div>
      </section>
    )
  }

  function renderProjectsSection(indices: number[]) {
    const safe = indices.filter((i) => i >= 0 && i < proj.length)
    if (!safe.length) return null
    const showHeader = safe[0] === 0
    return (
      <section className="rp__section">
        {showHeader ? (
          <div className="rp__sectionHead">
            <div className="rp__sectionTitle">Projects</div>
          </div>
        ) : null}
        <div className="rp__stack">{safe.map((i) => renderProjectItem(proj[i], i))}</div>
      </section>
    )
  }

  const themeStyle: CSSProperties | undefined = primaryColor
    ? ({ ['--rp-primary' as any]: primaryColor } as CSSProperties)
    : undefined

  return (
    <div className="rpPages" style={themeStyle}>
      {pages.map((p, idx) => (
        <Fragment key={idx}>
          {idx !== 0 ? <div className="rpPageSeparator" aria-hidden="true" /> : null}
          <article className="rp rpPage">
            {idx === 0 ? renderHeader() : null}
            {idx === 0 ? renderSummarySection() : null}
            {idx === 0 ? renderSkillsSection() : null}
            {renderExperienceSection(p.exp, Boolean(p.expHeader))}
            {renderEducationSection(p.edu)}
            {renderProjectsSection(p.proj)}
          </article>
        </Fragment>
      ))}

      {/* Offscreen measurement surface to decide paging */}
      <div className="rpMeasure" aria-hidden="true">
        <article className="rp rpPage" ref={pageRef}>
          <header className="rp__header" ref={headerRef}>
            <div className="rp__headerBlock">
              <div className="rp__headerMain">{resume.name || '—'}</div>
              {resume.title ? <div className="rp__headerSub">{resume.title}</div> : null}
              {contactItems.length ? (
                <div className="rp__contact">
                  {contactItems.map((it, idx2) => (
                    <span className="rp__contactItem" key={`${it.kind}-${it.label}-${idx2}`}>
                      <span className="rp__contactIcon">
                        <ContactIcon kind={it.kind} />
                      </span>
                      {it.href ? (
                        <a className="rp__contactLink" href={it.href} target="_blank" rel="noreferrer">
                          {it.label}
                        </a>
                      ) : (
                        <span className="rp__contactText">{it.label}</span>
                      )}
                      {idx2 !== contactItems.length - 1 ? <span className="rp__contactSep">|</span> : null}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          </header>

          {hasSummary ? (
            <section className="rp__section" ref={summaryRef}>
              <div className="rp__sectionHead">
                <div className="rp__sectionTitle">Summary</div>
              </div>
              <div className="rp__text">{resume.professional_summary}</div>
            </section>
          ) : null}

          {hasSkills ? (
            <section className="rp__section" ref={skillsRef}>
              <div className="rp__sectionHead">
                <div className="rp__sectionTitle">Skills</div>
              </div>
              <div className="rp__skillsBlock">
                {resume.skills!.map((s, idx3) => (
                  <div className="rp__skillLine" key={`${s.category ?? 'skills'}-${idx3}`}>
                    {s.category ? <span className="rp__skillCat">{s.category}:</span> : null}{' '}
                    <span className="rp__skillItems">{(s.skills || []).join(', ')}</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {exp.length ? (
            <section className="rp__section" ref={expStartRef}>
              <div className="rp__sectionHead">
                <div className="rp__sectionTitle">Experience</div>
              </div>
            </section>
          ) : null}
          <div className="rp__stack">
            {expClean.map((e, idx4) => (
              <div
                className="rp__item"
                key={`${e.company ?? e.title ?? 'exp'}-${idx4}`}
                ref={(el) => {
                  expItemRefs.current[idx4] = el
                }}
              >
                <div
                  ref={(el) => {
                    expCoreRefs.current[idx4] = el
                  }}
                >
                  <div className="rp__row">
                    <div className="rp__company">{e.company || '—'}</div>
                    {e.company_address ? <div className="rp__addr">{e.company_address}</div> : null}
                  </div>
                  <div className="rp__row rp__rowSub">
                    <div className="rp__role">{e.title || ''}</div>
                    {joinDate(e.start_date, e.end_date) ? <div className="rp__dates">{joinDate(e.start_date, e.end_date)}</div> : null}
                  </div>
                  {e.summary ? <div className="rp__text">{e.summary}</div> : null}
                </div>
                {e.responsibilities?.length ? (
                  <ul
                    className="rp__list"
                    ref={(el) => {
                      expListRefs.current[idx4] = el
                    }}
                  >
                    {e.responsibilities.map((r, j) => (
                      <li
                        key={j}
                        ref={(el) => {
                          if (!expRespRefs.current[idx4]) expRespRefs.current[idx4] = []
                          expRespRefs.current[idx4][j] = el
                        }}
                      >
                        {r}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <ul
                    className="rp__list"
                    style={{ marginTop: 0 }}
                    ref={(el) => {
                      expListRefs.current[idx4] = el
                    }}
                  >
                    {/* keep ref stable even when empty */}
                  </ul>
                )}
              </div>
            ))}
          </div>

          {edu.length ? (
            <section className="rp__section" ref={eduStartRef}>
              <div className="rp__sectionHead">
                <div className="rp__sectionTitle">Education</div>
              </div>
            </section>
          ) : null}
          <div className="rp__stack">
            {edu.map((e, idx5) => (
              <div
                key={`${e.institution ?? 'edu'}-${idx5}`}
                ref={(el) => {
                  eduItemRefs.current[idx5] = el
                }}
              >
                {renderEducationItem(e, idx5)}
              </div>
            ))}
          </div>

          {proj.length ? (
            <section className="rp__section" ref={projStartRef}>
              <div className="rp__sectionHead">
                <div className="rp__sectionTitle">Projects</div>
              </div>
            </section>
          ) : null}
          <div className="rp__stack">
            {proj.map((p2, idx6) => (
              <div
                key={`${p2.name ?? 'proj'}-${idx6}`}
                ref={(el) => {
                  projItemRefs.current[idx6] = el
                }}
              >
                {renderProjectItem(p2, idx6)}
              </div>
            ))}
          </div>
        </article>
      </div>
    </div>
  )
}

