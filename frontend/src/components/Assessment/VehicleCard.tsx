import { useState } from "react"
import { Truck, ChevronDown, ChevronUp } from "lucide-react"
import type { VehicleAssessment } from "../../hooks/useAssessment"
import CheckDetail from "./CheckDetail"

interface Props {
  assessment: VehicleAssessment
  isSelected: boolean
  onSelect: () => void
}

const ratingConfig = {
  GREEN: { bg: "bg-green-500", ring: "ring-green-300", text: "Clear" },
  AMBER: { bg: "bg-amber-500", ring: "ring-amber-300", text: "Caution" },
  RED:   { bg: "bg-red-500",   ring: "ring-red-300",   text: "No access" },
}

export default function VehicleCard({ assessment, isSelected, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false)
  const config = ratingConfig[assessment.overall_rating]

  return (
    <div
      className={`border rounded-lg overflow-hidden cursor-pointer transition-all ${isSelected ? `ring-2 ${config.ring}` : "border-gray-200 hover:border-gray-300"}`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3 p-3">
        <div className={`w-4 h-4 rounded-full ${config.bg} flex-shrink-0`} />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-gray-900 truncate">{assessment.vehicle_name}</p>
          <p className="text-xs text-gray-500">{config.text}</p>
        </div>
        <Truck className="w-5 h-5 text-gray-400 flex-shrink-0" />
        <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }} className="p-1 hover:bg-gray-100 rounded">
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </button>
      </div>
      {expanded && (
        <div className="border-t px-3 py-2 bg-gray-50 space-y-2">
          {assessment.checks.map((check, i) => <CheckDetail key={i} check={check} />)}
          <p className="text-xs text-gray-500 italic mt-2">{assessment.recommendation}</p>
          {assessment.confidence < 1.0 && (
            <p className="text-xs text-amber-600">Confidence: {Math.round(assessment.confidence * 100)}% — some data unavailable</p>
          )}
        </div>
      )}
    </div>
  )
}
