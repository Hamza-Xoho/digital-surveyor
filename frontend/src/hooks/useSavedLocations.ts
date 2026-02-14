import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { getAccessToken } from "@/utils/token"

export interface SavedLocation {
  id: string
  label: string
  postcode: string
  latitude: number
  longitude: number
  notes: string | null
  created_at: string
}

async function fetchLocations(): Promise<SavedLocation[]> {
  const token = getAccessToken()
  const res = await fetch(`${OpenAPI.BASE}/api/v1/locations/`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error("Failed to fetch locations")
  return res.json()
}

async function createLocation(data: { label: string; postcode: string; notes?: string }): Promise<SavedLocation> {
  const token = getAccessToken()
  const res = await fetch(`${OpenAPI.BASE}/api/v1/locations/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Failed to create location")
  }
  return res.json()
}

async function deleteLocation(id: string): Promise<void> {
  const token = getAccessToken()
  const res = await fetch(`${OpenAPI.BASE}/api/v1/locations/${id}`, {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error("Failed to delete location")
}

export function useSavedLocations() {
  return useQuery({
    queryKey: ["saved-locations"],
    queryFn: fetchLocations,
  })
}

export function useCreateLocation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-locations"] })
    },
  })
}

export function useDeleteLocation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-locations"] })
    },
  })
}
