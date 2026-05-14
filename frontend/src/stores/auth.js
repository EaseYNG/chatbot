import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setAuthTokenGetter, setOnUnauthorized } from '../api/client.js'

const STORAGE_KEY = 'chatbot_auth'

function loadTokens() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return { accessToken: null, refreshToken: null }
}

export const useAuthStore = defineStore('auth', () => {
  const tokens = ref(loadTokens())
  const user = ref(null)

  // Register token getter and 401 handler so api/client.js can inject auth headers
  setAuthTokenGetter(() => tokens.value.accessToken)
  setOnUnauthorized(() => {
    tokens.value = { accessToken: null, refreshToken: null }
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
  })

  const isAuthenticated = computed(() => !!tokens.value.accessToken)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens.value))
  }

  function setTokens(accessToken, refreshToken) {
    tokens.value = { accessToken, refreshToken }
    persist()
  }

  function setUser(userData) {
    user.value = userData
  }

  function clear() {
    tokens.value = { accessToken: null, refreshToken: null }
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  async function login(username, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail)
    }
    const data = await res.json()
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
    return data
  }

  async function register(username, password) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(err.detail)
    }
    const data = await res.json()
    setTokens(data.access_token, data.refresh_token)
    return data
  }

  async function fetchUser() {
    if (!tokens.value.accessToken) return null
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${tokens.value.accessToken}` },
      })
      if (res.ok) {
        user.value = await res.json()
        return user.value
      }
      if (res.status === 401) {
        clear()
      }
    } catch { /* ignore */ }
    return null
  }

  function getAuthHeaders() {
    if (!tokens.value.accessToken) return {}
    return { Authorization: `Bearer ${tokens.value.accessToken}` }
  }

  return {
    tokens,
    user,
    isAuthenticated,
    setTokens,
    clear,
    login,
    register,
    fetchUser,
    getAuthHeaders,
  }
})
