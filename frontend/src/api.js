const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

let accessToken = null
let refreshToken = null

export async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/token/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.detail || data.non_field_errors?.[0] || 'Invalid username or password.'
    )
  }

  accessToken = data.access
  refreshToken = data.refresh

  return true
}

export function logout() {
  accessToken = null
  refreshToken = null
}

export function isAuthenticated() {
  return Boolean(accessToken)
}

async function refreshAccessToken() {
  if (!refreshToken) {
    logout()
    return false
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh: refreshToken })
    })

    if (!response.ok) {
      logout()
      return false
    }

    const data = await response.json()
    accessToken = data.access

    if (data.refresh) {
      refreshToken = data.refresh
    }

    return Boolean(accessToken)
  } catch {
    logout()
    return false
  }
}

export async function authenticatedFetch(path, options = {}) {
  if (!accessToken) {
    throw new Error('Please log in to continue.')
  }

  const makeRequest = () => fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${accessToken}`
    }
  })

  let response = await makeRequest()

  if (response.status === 401) {
    const refreshed = await refreshAccessToken()

    if (!refreshed) {
      throw new Error('Your session has expired. Please log in again.')
    }

    response = await makeRequest()
  }

  return response
}
