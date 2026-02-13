import { useEffect } from "react"
import { MapContainer as LeafletMap, TileLayer, useMap } from "react-leaflet"
import type { LatLngTuple } from "leaflet"
import type { AssessmentResult } from "../../hooks/useAssessment"
import RoadOverlay from "./RoadOverlay"
import BuildingOverlay from "./BuildingOverlay"
import WidthMarkers from "./WidthMarkers"
import GradientOverlay from "./GradientOverlay"
import VehicleOverlay from "./VehicleOverlay"

const DEFAULT_CENTRE: LatLngTuple = [50.92, -0.13]
const DEFAULT_ZOOM = 10
const ASSESSMENT_ZOOM = 17

const OSM_TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

interface Props {
  assessment: AssessmentResult | null
  selectedVehicle: string | null
}

function FlyToAssessment({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo([lat, lon], ASSESSMENT_ZOOM, { duration: 1.5 })
  }, [lat, lon, map])
  return null
}

export default function MapContainer({ assessment, selectedVehicle }: Props) {
  const tileUrl = import.meta.env.VITE_OS_API_KEY
    ? `https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=${import.meta.env.VITE_OS_API_KEY}`
    : OSM_TILE_URL
  const attribution = import.meta.env.VITE_OS_API_KEY
    ? "© Crown copyright and database rights Ordnance Survey"
    : "© OpenStreetMap contributors"

  return (
    <LeafletMap
      center={DEFAULT_CENTRE}
      zoom={DEFAULT_ZOOM}
      className="h-full w-full"
      zoomControl={true}
    >
      <TileLayer url={tileUrl} attribution={attribution} maxZoom={20} />

      {assessment && (
        <>
          <FlyToAssessment lat={assessment.latitude} lon={assessment.longitude} />

          {assessment.geojson_overlays.roads && (
            <RoadOverlay data={assessment.geojson_overlays.roads} />
          )}

          {assessment.geojson_overlays.buildings && (
            <BuildingOverlay data={assessment.geojson_overlays.buildings} />
          )}

          {assessment.geojson_overlays.width_measurements && (
            <WidthMarkers data={assessment.geojson_overlays.width_measurements} />
          )}

          {assessment.geojson_overlays.gradient_profile && (
            <GradientOverlay data={assessment.geojson_overlays.gradient_profile} />
          )}

          {selectedVehicle && (
            <VehicleOverlay
              assessment={assessment}
              vehicleClass={selectedVehicle}
            />
          )}
        </>
      )}
    </LeafletMap>
  )
}
