import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { FeatureCollection, Feature } from "geojson"
import { OpenAPI } from "@/client/core/OpenAPI"
import { getAccessToken, clearAuthState } from "@/utils/token"

export interface VehicleCheck {
  name: string
  rating: "GREEN" | "AMBER" | "RED"
  detail: string
  value: number | null
  threshold: number | null
}

export interface VehicleAssessment {
  vehicle_name: string
  vehicle_class: string
  overall_rating: "GREEN" | "AMBER" | "RED"
  confidence: number
  checks: VehicleCheck[]
  recommendation: string
}

export interface WidthAnalysis {
  min_width_m: number
  max_width_m: number
  mean_width_m: number
  pinch_points: Array<{ location: number[]; width_m: number }>
}

export interface GradientAnalysis {
  max_gradient_pct: number
  mean_gradient_pct: number
  steep_segments: Array<{ start_m: number; end_m: number; gradient_pct: number }>
}

export interface DataSourceInfo {
  source: string
  status: "ok" | "degraded" | "unavailable"
  note?: string
  resolution?: string
}

export interface AssessmentResult {
  id?: string
  postcode: string
  latitude: number
  longitude: number
  easting: number
  northing: number
  overall_rating: "GREEN" | "AMBER" | "RED"
  notes?: string | null
  vehicle_assessments: VehicleAssessment[]
  width_analysis: WidthAnalysis | null
  gradient_analysis: GradientAnalysis | null
  data_sources?: Record<string, DataSourceInfo>
  geojson_overlays: {
    roads: FeatureCollection
    buildings: FeatureCollection
    road_lines?: FeatureCollection
    width_measurements: FeatureCollection
    gradient_profile: Feature | null
  }
}

async function runAssessment(postcode: string): Promise<AssessmentResult> {
  const token = getAccessToken()
  const encodedPostcode = encodeURIComponent(postcode)

  // Try authenticated endpoint first if we have a token
  if (token) {
    const res = await fetch(
      `${OpenAPI.BASE}/api/v1/assessments/?postcode=${encodedPostcode}`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    )

    if (res.ok) return res.json()

    // Stale/invalid token — clear it and fall back to unauthenticated endpoint
    if (res.status === 401 || res.status === 403 || res.status === 404) {
      clearAuthState()
    } else {
      let detail = "Assessment failed"
      try {
        const err = await res.json()
        detail = err.detail || detail
      } catch {
        detail = `Assessment failed (${res.status})`
      }
      throw new Error(detail)
    }
  }

  // Unauthenticated fallback (/quick endpoint)
  const res = await fetch(
    `${OpenAPI.BASE}/api/v1/assessments/quick?postcode=${encodedPostcode}`,
    { method: "POST" },
  )
  if (!res.ok) {
    let detail = "Assessment failed"
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch {
      detail = `Assessment failed (${res.status})`
    }
    throw new Error(detail)
  }
  return res.json()
}

async function updateNotes({ assessmentId, notes }: { assessmentId: string; notes: string }): Promise<void> {
  const token = getAccessToken()
  const res = await fetch(`${OpenAPI.BASE}/api/v1/assessments/${assessmentId}/notes`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ notes }),
  })
  if (!res.ok) {
    let detail = "Failed to update notes"
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch {
      detail = `Failed to update notes (${res.status})`
    }
    throw new Error(detail)
  }
}

export function useRunAssessment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: runAssessment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] })
    },
  })
}

export function useUpdateAssessmentNotes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: updateNotes,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] })
    },
  })
}

export interface AssessmentHistoryItem {
  id: string
  postcode: string
  overall_rating: "GREEN" | "AMBER" | "RED"
  latitude: number
  longitude: number
  notes: string | null
  created_at: string
}

interface AssessmentHistoryResponse {
  data: AssessmentHistoryItem[]
  count: number
}

export function useAssessmentHistory() {
  return useQuery<AssessmentHistoryItem[]>({
    queryKey: ["assessments"],
    queryFn: async () => {
      const token = getAccessToken()
      if (!token) return []
      const res = await fetch(`${OpenAPI.BASE}/api/v1/assessments/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        if (res.status === 401) return []
        throw new Error("Failed to fetch assessment history")
      }
      const json: AssessmentHistoryResponse = await res.json()
      return json.data ?? []
    },
  })
}
