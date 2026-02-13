import { useMutation, useQuery } from "@tanstack/react-query"

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

export interface AssessmentResult {
  postcode: string
  latitude: number
  longitude: number
  easting: number
  northing: number
  overall_rating: "GREEN" | "AMBER" | "RED"
  vehicle_assessments: VehicleAssessment[]
  width_analysis: WidthAnalysis | null
  gradient_analysis: GradientAnalysis | null
  geojson_overlays: {
    roads: GeoJSON.FeatureCollection
    buildings: GeoJSON.FeatureCollection
    width_measurements: GeoJSON.FeatureCollection
    gradient_profile: GeoJSON.Feature | null
  }
}

async function runQuickAssessment(postcode: string): Promise<AssessmentResult> {
  const res = await fetch(
    `/api/v1/assessments/quick?postcode=${encodeURIComponent(postcode)}`,
    { method: "POST" }
  )
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Assessment failed")
  }
  return res.json()
}

export function useRunAssessment() {
  return useMutation({
    mutationFn: runQuickAssessment,
  })
}

export function useAssessmentHistory() {
  return useQuery({
    queryKey: ["assessments"],
    queryFn: async () => {
      const res = await fetch("/api/v1/assessments/")
      return res.json()
    },
  })
}
