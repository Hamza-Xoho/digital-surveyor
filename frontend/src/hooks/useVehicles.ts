import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { getAccessToken } from "@/utils/token"

export interface VehicleProfile {
  id?: string
  name: string
  vehicle_class: string
  width_m: number
  length_m: number
  height_m: number
  weight_kg: number
  turning_radius_m: number
  mirror_width_m: number
  created_at?: string
}

export interface VehicleCreateInput {
  name: string
  vehicle_class: string
  width_m: number
  length_m: number
  height_m: number
  weight_kg: number
  turning_radius_m: number
  mirror_width_m?: number
}

export function useVehicleProfiles() {
  return useQuery<VehicleProfile[]>({
    queryKey: ["vehicles"],
    queryFn: async () => {
      const res = await fetch(`${OpenAPI.BASE}/api/v1/vehicles/`)
      if (!res.ok) throw new Error("Failed to fetch vehicles")
      return res.json()
    },
  })
}

export function useCustomVehicles() {
  return useQuery<VehicleProfile[]>({
    queryKey: ["custom-vehicles"],
    queryFn: async () => {
      const token = getAccessToken()
      const res = await fetch(`${OpenAPI.BASE}/api/v1/vehicles/custom/list`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error("Failed to fetch custom vehicles")
      return res.json()
    },
  })
}

export function useCreateVehicle() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: VehicleCreateInput) => {
      const token = getAccessToken()
      const res = await fetch(`${OpenAPI.BASE}/api/v1/vehicles/custom`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Failed to create vehicle")
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-vehicles"] })
    },
  })
}

export function useDeleteVehicle() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const token = getAccessToken()
      const res = await fetch(`${OpenAPI.BASE}/api/v1/vehicles/custom/${id}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error("Failed to delete vehicle")
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-vehicles"] })
    },
  })
}
