import { Navigate, useLocation } from 'react-router-dom'
import { ReactNode } from 'react'
import { getToken } from '../api/client'

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = getToken()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
