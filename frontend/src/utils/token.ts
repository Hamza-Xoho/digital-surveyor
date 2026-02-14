const TOKEN_KEY = "access_token"

interface JwtPayload {
  exp?: number
  sub?: string
  [key: string]: unknown
}

function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split(".")
    if (parts.length !== 3) return null
    const payload = atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"))
    return JSON.parse(payload)
  } catch {
    return null
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return true
  // Add 30-second buffer to avoid edge-case requests right at expiry
  return Date.now() >= (payload.exp - 30) * 1000
}

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function isLoggedIn(): boolean {
  const token = getAccessToken()
  if (!token) return false
  return !isTokenExpired(token)
}

export function clearAuthState(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}
