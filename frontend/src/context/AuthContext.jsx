import React, { createContext, useContext, useState } from 'react'
import client from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('ecg_user')
    return raw ? JSON.parse(raw) : null
  })

  async function login(username, password, role) {
    const { data } = await client.post('/auth/login', { username, password, role })
    localStorage.setItem('ecg_token', data.access_token)
    const u = { username: data.username, role: data.role, full_name: data.full_name }
    localStorage.setItem('ecg_user', JSON.stringify(u))
    setUser(u)
    return u
  }

  function logout() {
    localStorage.removeItem('ecg_token')
    localStorage.removeItem('ecg_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
