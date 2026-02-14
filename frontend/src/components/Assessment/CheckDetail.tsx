import { CheckCircle, AlertTriangle, XCircle } from "lucide-react"
import type { VehicleCheck } from "../../hooks/useAssessment"

interface Props {
  check: VehicleCheck
}

const icons = {
  GREEN: <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />,
  AMBER: <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />,
  RED:   <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />,
}

const textColor = {
  GREEN: "text-green-700 dark:text-green-300",
  AMBER: "text-amber-700 dark:text-amber-300",
  RED:   "text-red-700 dark:text-red-300",
}

export default function CheckDetail({ check }: Props) {
  return (
    <div className="flex items-start gap-2">
      {icons[check.rating]}
      <div className="min-w-0">
        <p className={`text-xs font-medium ${textColor[check.rating]}`}>{check.name}</p>
        <p className="text-xs text-muted-foreground">{check.detail}</p>
      </div>
    </div>
  )
}
