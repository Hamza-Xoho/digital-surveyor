import { useMemo } from "react"
import { Rectangle, Circle } from "react-leaflet"
import L from "leaflet"
import type { AssessmentResult } from "../../hooks/useAssessment"
import { useVehicleProfiles } from "../../hooks/useVehicles"

interface Props {
  assessment: AssessmentResult
  vehicleClass: string
}

export default function VehicleOverlay({ assessment, vehicleClass }: Props) {
  const { data: vehicles } = useVehicleProfiles()
  const vehicle = vehicles?.find((v) => v.vehicle_class === vehicleClass)

  const bounds = useMemo(() => {
    if (!vehicle) return null
    const lat = assessment.latitude
    const lon = assessment.longitude
    const halfWidthDeg = (vehicle.width_m / 2) / 69000
    const halfLengthDeg = (vehicle.length_m / 2) / 111320
    return L.latLngBounds(
      [lat - halfLengthDeg, lon - halfWidthDeg],
      [lat + halfLengthDeg, lon + halfWidthDeg]
    )
  }, [vehicle, assessment.latitude, assessment.longitude])

  if (!vehicle || !bounds) return null

  return (
    <>
      <Rectangle
        bounds={bounds}
        pathOptions={{
          color: "#3b82f6",
          fillColor: "#3b82f6",
          fillOpacity: 0.25,
          weight: 2,
          dashArray: "6, 4",
        }}
      />
      <Circle
        center={[assessment.latitude, assessment.longitude]}
        radius={vehicle.turning_radius_m}
        pathOptions={{
          color: "#3b82f6",
          fillColor: "#3b82f6",
          fillOpacity: 0.08,
          weight: 1,
          dashArray: "4, 8",
        }}
      />
    </>
  )
}
