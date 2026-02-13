import { useQuery } from "@tanstack/react-query"

export interface VehicleProfile {
  name: string
  vehicle_class: string
  width_m: number
  length_m: number
  height_m: number
  weight_kg: number
  turning_radius_m: number
  mirror_width_m: number
}

export function useVehicleProfiles() {
  return useQuery<VehicleProfile[]>({
    queryKey: ["vehicles"],
    queryFn: async () => {
      const res = await fetch("/api/v1/vehicles/")
      return res.json()
    },
  })
}
