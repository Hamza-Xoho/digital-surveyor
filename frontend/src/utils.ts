import type { ApiError } from "./client"

/**
 * Extract initials from a full name string.
 * E.g. "Jane Doe" → "JD", "Alice" → "A"
 */
export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("")
    .slice(0, 2)
}

/**
 * Generic error handler for TanStack Query mutations.
 *
 * Usage: `onError: handleError.bind(showErrorToast)`
 *
 * When bound to a toast function, extracts a user-friendly message
 * from the API error response and displays it.
 */
export function handleError(
  this: (message: string) => void,
  error: ApiError | Error,
): void {
  const detail =
    "body" in error
      ? ((error.body as { detail?: string })?.detail ?? error.message ?? "Unknown error")
      : (error.message ?? "Unknown error")
  this(detail)
}
