import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { FeatureCollection, Feature } from "geojson"
import { OpenAPI } from "@/client/core/OpenAPI"
import { getAccessToken } from "@/utils/token"

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
  steep_segments: Array<{ start_m: number; end_m: number; max_gradient_pct: number }>
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
  // Use persisted endpoint when authenticated (returns id for notes)
  const endpoint = token
    ? `${OpenAPI.BASE}/api/v1/assessments/?postcode=${encodeURIComponent(postcode)}`
    : `${OpenAPI.BASE}/api/v1/assessments/quick?postcode=${encodeURIComponent(postcode)}`
  const res = await fetch(endpoint, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Assessment failed")
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
  if (!res.ok) throw new Error("Failed to update notes")
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

export function useAssessmentHistory() {
  return useQuery({
    queryKey: ["assessments"],
    queryFn: async () => {
      const token = getAccessToken()
      const res = await fetch(`${OpenAPI.BASE}/api/v1/assessments/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error("Failed to fetch assessment history")
      return res.json()
    },
  })
}
