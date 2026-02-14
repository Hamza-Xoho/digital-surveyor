import { useAssessmentHistory, type AssessmentHistoryItem } from "../../hooks/useAssessment"

const ratingDot: Record<string, string> = {
  GREEN: "bg-green-500",
  AMBER: "bg-amber-500",
  RED: "bg-red-500",
}

export default function AssessmentHistory() {
  const { data, isLoading } = useAssessmentHistory()
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading history...</p>
  if (!data?.length) return <p className="text-sm text-muted-foreground">No past assessments</p>

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-foreground text-sm">Recent Assessments</h3>
      {data.map((a: AssessmentHistoryItem) => (
        <div key={a.id} className="flex items-center gap-2 p-2 border rounded text-sm hover:bg-muted/50 cursor-pointer">
          <div className={`w-3 h-3 rounded-full ${ratingDot[a.overall_rating] ?? ""}`} />
          <span className="font-medium">{a.postcode}</span>
          <span className="text-muted-foreground text-xs ml-auto">{new Date(a.created_at).toLocaleDateString()}</span>
        </div>
      ))}
    </div>
  )
}
