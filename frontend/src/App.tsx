import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import MailAccountPage from './pages/MailAccountPage'
import RecipientsPage from './pages/RecipientsPage'
import ModelConfigsPage from './pages/ModelConfigsPage'
import SourcesPage from './pages/SourcesPage'
import EmailTemplatePage from './pages/EmailTemplatePage'
import SchedulePage from './pages/SchedulePage'
import JobsPage from './pages/JobsPage'
import StoragePage from './pages/StoragePage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/mail-account" element={<MailAccountPage />} />
        <Route path="/recipients" element={<RecipientsPage />} />
        <Route path="/models" element={<ModelConfigsPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/email-template" element={<EmailTemplatePage />} />
        <Route path="/schedule" element={<SchedulePage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/storage" element={<StoragePage />} />
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
