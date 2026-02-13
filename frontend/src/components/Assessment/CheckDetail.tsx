import { CheckCircle, AlertTriangle, XCircle } from "lucide-react"
import type { VehicleCheck } from "../../hooks/useAssessment"

interface Props {
  check: VehicleCheck
}

const icons = {
  GREEN: <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />,
  AMBER: <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />,
  RED:   <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" />,
}

const textColor = {
  GREEN: "text-green-700",
  AMBER: "text-amber-700",
  RED:   "text-red-700",
}

export default function CheckDetail({ check }: Props) {
  return (
    <div className="flex items-start gap-2">
      {icons[check.rating]}
      <div className="min-w-0">
        <p className={`text-xs font-medium ${textColor[check.rating]}`}>{check.name}</p>
        <p className="text-xs text-gray-600">{check.detail}</p>
      </div>
    </div>
  )
}
