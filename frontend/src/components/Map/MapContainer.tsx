import { useEffect, useRef } from "react"
import {
  MapContainer as LeafletMap,
  TileLayer,
  useMap,
} from "react-leaflet"
import L from "leaflet"
import type { LatLngTuple, Map as LMap } from "leaflet"
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

// ---------------------------------------------------------------------------
// Patch Leaflet to tolerate React 19 StrictMode double-mount.
//
// react-leaflet v4 creates the Leaflet map inside a ref callback that
// captures `context === null` via a `useCallback([], ...)` closure.  On
// StrictMode remount the closure fires again with stale `context === null`
// and calls `new L.Map(node)`.  Because React reuses the same DOM node, it
// still carries `_leaflet_id` and Leaflet throws
// "Map container is already initialized".
//
// We patch `_initContainer` to strip the stale `_leaflet_id` **and** remove
// leftover child nodes (tiles, controls) from the previous mount so only a
// single live map is visible.
// ---------------------------------------------------------------------------
const origInitContainer = (L.Map.prototype as any)._initContainer
;(L.Map.prototype as any)._initContainer = function (id: any) {
  const container =
    typeof id === "string" ? document.getElementById(id) : id
  if (container && (container as any)._leaflet_id) {
    // Stale Leaflet stamp — strip it and wipe leftover DOM children so
    // the new map instance starts with a clean container.
    delete (container as any)._leaflet_id
    while (container.firstChild) {
      container.removeChild(container.firstChild)
    }
  }
  origInitContainer.call(this, id)
}

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
  const mapRef = useRef<LMap | null>(null)

  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [])

  const tileUrl = import.meta.env.VITE_OS_API_KEY
    ? `https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=${import.meta.env.VITE_OS_API_KEY}`
    : OSM_TILE_URL
  const attribution = import.meta.env.VITE_OS_API_KEY
    ? "© Crown copyright and database rights Ordnance Survey"
    : "© OpenStreetMap contributors"

  return (
    <LeafletMap
      ref={mapRef}
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
