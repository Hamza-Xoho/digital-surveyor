import { GeoJSON } from "react-leaflet"
import type { PathOptions } from "leaflet"

interface Props {
  data: GeoJSON.Feature
}

function getGradientColor(gradientPct: number): string {
  if (gradientPct <= 5) return "#22c55e"
  if (gradientPct <= 8) return "#f59e0b"
  return "#ef4444"
}

export default function GradientOverlay({ data }: Props) {
  if (!data) return null
  const maxGrad = data.properties?.max_gradient_pct || 0
  const style: PathOptions = {
    color: getGradientColor(maxGrad),
    weight: 5,
    opacity: 0.8,
  }
  return (
    <GeoJSON
      key={`gradient-${maxGrad}`}
      data={{ type: "FeatureCollection", features: [data] }}
      style={() => style}
    />
  )
}
