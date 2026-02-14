import { Info, CheckCircle2, AlertTriangle, XCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { DataSourceInfo } from "@/hooks/useAssessment"

interface Props {
  dataSources: Record<string, DataSourceInfo>
}

const sourceLabels: Record<string, string> = {
  geocoding: "Geocoding",
  road_geometry: "Road Geometry",
  elevation: "Elevation",
  width_analysis: "Width Analysis",
  route_restrictions: "Route Restrictions",
}

const sourceDisplayNames: Record<string, string> = {
  "postcodes.io": "Postcodes.io",
  os_mastermap: "OS MasterMap",
  openstreetmap: "OpenStreetMap",
  lidar_dtm: "LiDAR DTM",
  elevation_api: "Elevation API",
  osm_estimates: "OSM Estimates",
  here_api: "HERE Routing",
  none: "Not Available",
}

function StatusIcon({ status }: { status: string }) {
  if (status === "ok") return <CheckCircle2 className="size-3.5 shrink-0 text-green-600" />
  if (status === "degraded") return <AlertTriangle className="size-3.5 shrink-0 text-amber-500" />
  return <XCircle className="size-3.5 shrink-0 text-muted-foreground" />
}

export default function DataSourceBanner({ dataSources }: Props) {
  const entries = Object.entries(dataSources)
  if (entries.length === 0) return null

  const allOk = entries.every(([, info]) => info.status === "ok")

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Info className="size-4" />
          Data Sources
          {allOk ? (
            <span className="text-xs font-normal text-green-600">All active</span>
          ) : (
            <span className="text-xs font-normal text-amber-500">Some limited</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5 text-xs">
          {entries.map(([key, info]) => (
            <div key={key} className="flex items-center gap-2">
              <StatusIcon status={info.status} />
              <span className="w-28 shrink-0 text-muted-foreground">
                {sourceLabels[key] || key}
              </span>
              <span className="flex-1 truncate">
                {sourceDisplayNames[info.source] || info.source}
              </span>
              {info.note && (
                <span className="hidden text-muted-foreground sm:inline" title={info.note}>
                  *
                </span>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
