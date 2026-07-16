import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function AdminRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'admin') return <Navigate to="/" replace />
  return children
}
