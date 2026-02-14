import { createFileRoute } from "@tanstack/react-router"
import { ClipboardCheck, Truck, TrendingUp } from "lucide-react"

import useAuth from "@/hooks/useAuth"
import { useAssessmentHistory } from "@/hooks/useAssessment"
import { useVehicleProfiles } from "@/hooks/useVehicles"
import StatsCard from "@/components/Dashboard/StatsCard"
import QuickAssessment from "@/components/Dashboard/QuickAssessment"
import RecentAssessments from "@/components/Dashboard/RecentAssessments"
import DataSourceStatus from "@/components/Dashboard/DataSourceStatus"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [{ title: "Dashboard - Digital Surveyor" }],
  }),
})

function Dashboard() {
  const { user: currentUser, isLoading: authLoading } = useAuth()
  const { data: assessments } = useAssessmentHistory()
  const { data: vehicles } = useVehicleProfiles()

  const assessmentCount = Array.isArray(assessments) ? assessments.length : 0
  const vehicleCount = vehicles?.length ?? 0

  const greenCount = Array.isArray(assessments)
    ? assessments.filter((a: any) => a.overall_rating === "GREEN").length
    : 0
  const passRate =
    assessmentCount > 0 ? Math.round((greenCount / assessmentCount) * 100) : 0

  if (authLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Welcome back{currentUser?.full_name ? `, ${currentUser.full_name}` : ""}
        </h1>
        <p className="text-muted-foreground">
          Assess vehicle access for UK properties
        </p>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatsCard
          title="Total Assessments"
          value={assessmentCount}
          description={assessmentCount === 1 ? "assessment completed" : "assessments completed"}
          icon={ClipboardCheck}
          iconColor="text-blue-600"
        />
        <StatsCard
          title="Vehicle Profiles"
          value={vehicleCount}
          description="configured vehicles"
          icon={Truck}
          iconColor="text-violet-600"
        />
        <StatsCard
          title="Pass Rate"
          value={assessmentCount > 0 ? `${passRate}%` : "--"}
          description={assessmentCount > 0 ? `${greenCount} green of ${assessmentCount}` : "No data yet"}
          icon={TrendingUp}
          iconColor="text-green-600"
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <QuickAssessment />
          <RecentAssessments />
        </div>
        <div className="space-y-6">
          {currentUser?.is_superuser && <DataSourceStatus />}
        </div>
      </div>
    </div>
  )
}
