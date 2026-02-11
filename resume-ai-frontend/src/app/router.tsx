import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { HomePage } from '../features/home/pages/HomePage'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { RegisterPage } from '../features/auth/pages/RegisterPage'
import { DocsPage } from '../features/docs/pages/DocsPage'
import { TailorResumePage } from '../features/tailor/pages/TailorResumePage'
import { NewTailorPage } from '../features/tailor/pages/NewTailorPage'
import { TailoredResumeDetailPage } from '../features/tailor/pages/TailoredResumeDetailPage'
import { CoverLetterListPage } from '../features/coverLetter/pages/CoverLetterListPage'
import { NewCoverLetterPage } from '../features/coverLetter/pages/NewCoverLetterPage'
import { CoverLetterDetailPage } from '../features/coverLetter/pages/CoverLetterDetailPage'
import { UploadResumePage } from '../features/resume/pages/UploadResumePage'
import { ManualResumePage } from '../features/resume/pages/ManualResumePage'
import { BuiltResumesPage } from '../features/builtResumes/pages/BuiltResumesPage'
import { ResumeBuilderEditorPage } from '../features/resume/pages/ResumeBuilderEditorPage'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/tailorresume" element={<TailorResumePage />} />
        <Route path="/tailorresume/new" element={<NewTailorPage />} />
        <Route path="/tailorresume/:tailoredResumeId" element={<TailoredResumeDetailPage />} />
        <Route path="/coverletters" element={<CoverLetterListPage />} />
        <Route path="/coverletters/new" element={<NewCoverLetterPage />} />
        <Route path="/coverletters/:coverLetterId" element={<CoverLetterDetailPage />} />
        <Route path="/resume/upload" element={<UploadResumePage />} />
        <Route path="/resume/manual" element={<ManualResumePage />} />
        <Route path="/resume/builder" element={<BuiltResumesPage />} />
        <Route path="/resume/builder/:builtResumeId" element={<ResumeBuilderEditorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

