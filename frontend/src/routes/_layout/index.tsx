import { Link } from "@tanstack/react-router"
import { createFileRoute } from "@tanstack/react-router"
import { MapPin, Settings, Key, CheckCircle2, AlertTriangle } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import useAuth from "@/hooks/useAuth"
import { useApiKeyStatus } from "@/hooks/useApiKeys"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - Digital Surveyor",
      },
    ],
  }),
})

function ApiKeyStatusCard() {
  const { data: status, isLoading, isError } = useApiKeyStatus()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Key className="size-4" />
            API Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    )
  }

  if (isError || !status) {
    return null
  }

  const configuredCount = [
    status.os_configured,
    status.here_configured,
    status.mapillary_configured,
  ].filter(Boolean).length

  const hasWarning = !status.os_configured

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Key className="size-4" />
          API Configuration
        </CardTitle>
        <CardDescription>
          {configuredCount}/3 API keys configured
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            {status.os_configured ? (
              <CheckCircle2 className="size-4 text-green-600" />
            ) : (
              <AlertTriangle className="size-4 text-amber-500" />
            )}
            <span>Ordnance Survey</span>
            <span className={`ml-auto text-xs ${status.os_configured ? "text-green-600" : "text-amber-500"}`}>
              {status.os_configured ? "Active" : "Not configured"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {status.here_configured ? (
              <CheckCircle2 className="size-4 text-green-600" />
            ) : (
              <span className="size-4 rounded-full border border-muted-foreground/30" />
            )}
            <span>HERE Routing</span>
            <span className={`ml-auto text-xs ${status.here_configured ? "text-green-600" : "text-muted-foreground"}`}>
              {status.here_configured ? "Active" : "Optional"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {status.mapillary_configured ? (
              <CheckCircle2 className="size-4 text-green-600" />
            ) : (
              <span className="size-4 rounded-full border border-muted-foreground/30" />
            )}
            <span>Mapillary</span>
            <span className={`ml-auto text-xs ${status.mapillary_configured ? "text-green-600" : "text-muted-foreground"}`}>
              {status.mapillary_configured ? "Active" : "Optional"}
            </span>
          </div>
        </div>
        {hasWarning && (
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

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight truncate max-w-lg">
          Hi, {currentUser?.full_name || currentUser?.email}
        </h1>
        <p className="text-muted-foreground">
          Welcome back, nice to see you again!
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Quick action: Run Assessment */}
        <Card className="cursor-pointer transition-shadow hover:shadow-md">
          <Link to="/assessments" className="block">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <MapPin className="size-4 text-blue-600" />
                Run Assessment
              </CardTitle>
              <CardDescription>
                Check vehicle access for a UK postcode
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Enter a postcode to analyse road width, gradient, and turning space for different vehicle types.
              </p>
            </CardContent>
          </Link>
        </Card>

        {/* API Key Status (superuser only) */}
        {currentUser?.is_superuser && <ApiKeyStatusCard />}

        {/* Account Settings */}
        <Card className="cursor-pointer transition-shadow hover:shadow-md">
          <Link to="/settings" className="block">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Settings className="size-4" />
                Account Settings
              </CardTitle>
              <CardDescription>
                Manage your profile and preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Update your name, email, password, and theme preferences.
              </p>
            </CardContent>
          </Link>
        </Card>
      </div>
    </div>
  )
}
