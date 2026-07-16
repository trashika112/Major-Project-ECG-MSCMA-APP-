import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Patients from './pages/Patients.jsx'
import PatientDetail from './pages/PatientDetail.jsx'
import Admin from './pages/Admin.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import AdminRoute from './components/AdminRoute.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/patients" element={<ProtectedRoute><Patients /></ProtectedRoute>} />
      <Route path="/patients/:code" element={<ProtectedRoute><PatientDetail /></ProtectedRoute>} />
      <Route path="/admin" element={<AdminRoute><Admin /></AdminRoute>} />
    </Routes>
  )
}
