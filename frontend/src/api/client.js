import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const client = axios.create({ baseURL: API_BASE })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('ecg_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ecg_token')
      localStorage.removeItem('ecg_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
