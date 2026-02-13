import { GeoJSON } from "react-leaflet"
import type { PathOptions } from "leaflet"

interface Props {
  data: GeoJSON.FeatureCollection
}

const roadStyle: PathOptions = {
  fillColor: "#9ca3af",
  fillOpacity: 0.3,
  color: "#6b7280",
  weight: 1,
  opacity: 0.6,
}

export default function RoadOverlay({ data }: Props) {
  if (!data.features?.length) return null
  return (
    <GeoJSON
      key={JSON.stringify(data).slice(0, 100)}
      data={data}
      style={() => roadStyle}
    />
  )
}
