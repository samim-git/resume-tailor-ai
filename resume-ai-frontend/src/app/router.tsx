import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { HomePage } from '../features/home/pages/HomePage.tsx'
import { LoginPage } from '../features/auth/pages/LoginPage.tsx'
import { RegisterPage } from '../features/auth/pages/RegisterPage.tsx'
import { DocsPage } from '../features/docs/pages/DocsPage.tsx'
import { TailorResumePage } from '../features/tailor/pages/TailorResumePage.tsx'
import { UploadResumePage } from '../features/resume/pages/UploadResumePage.tsx'
import { ManualResumePage } from '../features/resume/pages/ManualResumePage.tsx'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/tailorresume" element={<TailorResumePage />} />
        <Route path="/resume/upload" element={<UploadResumePage />} />
        <Route path="/resume/manual" element={<ManualResumePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

