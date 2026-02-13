import { GeoJSON } from "react-leaflet"
import type { PathOptions } from "leaflet"
import type { FeatureCollection } from "geojson"

interface Props {
  data: FeatureCollection
}

const buildingStyle: PathOptions = {
  fillColor: "#f9a8d4",
  fillOpacity: 0.4,
  color: "#be185d",
  weight: 1,
  opacity: 0.7,
}

export default function BuildingOverlay({ data }: Props) {
  if (!data.features?.length) return null
  return (
    <GeoJSON
      key={JSON.stringify(data).slice(0, 100)}
      data={data}
      style={() => buildingStyle}
    />
  )
}
