import { Link } from "@tanstack/react-router"
import { Clock, MapPin, ArrowRight } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAssessmentHistory, type AssessmentHistoryItem } from "@/hooks/useAssessment"

type Rating = "GREEN" | "AMBER" | "RED"

const ratingColors: Record<Rating, string> = {
  GREEN: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  AMBER: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  RED: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
}

export default function RecentAssessments() {
  const { data, isLoading } = useAssessmentHistory()

  const assessments = data?.slice(0, 5) ?? []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="size-4" />
            Recent Assessments
          </CardTitle>
          <CardDescription>Your latest postcode assessments</CardDescription>
        </div>
        {assessments.length > 0 && (
          <Button variant="ghost" size="sm" asChild>
            <Link to="/assessments" search={{ postcode: undefined }}>
              View all
              <ArrowRight className="ml-1 size-3" />
            </Link>
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : assessments.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <MapPin className="mx-auto mb-2 size-8 opacity-50" />
            <p>No assessments yet</p>
            <p className="mt-1">Run your first assessment above</p>
          </div>
        ) : (
          <div className="space-y-2">
            {assessments.map((a: AssessmentHistoryItem) => (
              <div
                key={a.id}
                className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-center gap-3">
                  <MapPin className="size-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{a.postcode}</p>
                    {a.created_at && (
                      <p className="text-xs text-muted-foreground">
                        {new Date(a.created_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
                <Badge
                  variant="secondary"
                  className={ratingColors[a.overall_rating] || ""}
                >
                  {a.overall_rating}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
