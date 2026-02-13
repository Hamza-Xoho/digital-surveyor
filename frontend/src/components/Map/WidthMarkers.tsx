import { GeoJSON } from "react-leaflet"
import type { PathOptions } from "leaflet"

interface Props {
  data: GeoJSON.FeatureCollection
}

function getWidthColor(width: number): string {
  if (width >= 4.0) return "#22c55e"
  if (width >= 3.0) return "#f59e0b"
  return "#ef4444"
}

export default function WidthMarkers({ data }: Props) {
  if (!data.features?.length) return null
  return (
    <GeoJSON
      key={`widths-${data.features.length}`}
      data={data}
      style={(feature) => {
        const width = feature?.properties?.width_m || 0
        return {
          color: getWidthColor(width),
          weight: 3,
          opacity: 0.9,
          dashArray: "8, 6",
        } as PathOptions
      }}
      onEachFeature={(feature, layer) => {
        const width = feature.properties?.width_m
        if (width) {
          layer.bindTooltip(`${width}m`, {
            permanent: true,
            direction: "center",
            className: "width-label",
          })
        }
      }}
    />
  )
}
