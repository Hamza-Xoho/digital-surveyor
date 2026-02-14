import { Link } from "@tanstack/react-router"
import { Key, CheckCircle2, AlertTriangle, Settings } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useApiKeyStatus } from "@/hooks/useApiKeys"

export default function DataSourceStatus() {
  const { data: status, isLoading, isError } = useApiKeyStatus()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Key className="size-4" />
            Data Sources
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-6 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (isError || !status) return null

  const sources = [
    {
      name: "Ordnance Survey",
      configured: status.os_configured,
      required: true,
      description: "Road geometry & building footprints",
    },
    {
      name: "HERE Routing",
      configured: status.here_configured,
      required: false,
      description: "Route restrictions & turn analysis",
    },
    {
      name: "Mapillary",
      configured: status.mapillary_configured,
      required: false,
      description: "Street-level imagery",
    },
  ]

  const configuredCount = sources.filter((s) => s.configured).length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Key className="size-4" />
          Data Sources
        </CardTitle>
        <CardDescription>
          {configuredCount}/{sources.length} APIs configured
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2 text-sm">
          {sources.map((source) => (
            <div key={source.name} className="flex items-center gap-2">
              {source.configured ? (
                <CheckCircle2 className="size-4 shrink-0 text-green-600" />
              ) : source.required ? (
                <AlertTriangle className="size-4 shrink-0 text-amber-500" />
              ) : (
                <span className="size-4 shrink-0 rounded-full border border-muted-foreground/30" />
              )}
              <span className="flex-1">{source.name}</span>
              <span
                className={`text-xs ${source.configured ? "text-green-600" : source.required ? "text-amber-500" : "text-muted-foreground"}`}
              >
                {source.configured ? "Active" : source.required ? "Recommended" : "Optional"}
              </span>
            </div>
          ))}
        </div>
        {!status.os_configured && (
          <Button asChild variant="outline" size="sm" className="w-full">
            <Link to="/settings">
              <Settings className="mr-2 size-4" />
              Configure API Keys
            </Link>
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
