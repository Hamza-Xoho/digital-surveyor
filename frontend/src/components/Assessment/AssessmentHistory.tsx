import { useAssessmentHistory } from "../../hooks/useAssessment"

const ratingDot = {
  GREEN: "bg-green-500",
  AMBER: "bg-amber-500",
  RED: "bg-red-500",
}

export default function AssessmentHistory() {
  const { data, isLoading } = useAssessmentHistory()
  if (isLoading) return <p className="text-sm text-gray-400">Loading history...</p>
  if (!data?.data?.length) return <p className="text-sm text-gray-400">No past assessments</p>

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-gray-800 text-sm">Recent Assessments</h3>
      {data.data.map((a: any, i: number) => (
        <div key={i} className="flex items-center gap-2 p-2 border rounded text-sm hover:bg-gray-50 cursor-pointer">
          <div className={`w-3 h-3 rounded-full ${ratingDot[a.overall_rating as keyof typeof ratingDot]}`} />
          <span className="font-medium">{a.postcode}</span>
          <span className="text-gray-400 text-xs ml-auto">{new Date(a.created_at).toLocaleDateString()}</span>
        </div>
      ))}
    </div>
  )
}
