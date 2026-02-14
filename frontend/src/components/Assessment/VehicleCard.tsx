import { useState } from "react"
import { Truck, ChevronDown, ChevronUp } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import type { VehicleAssessment } from "@/hooks/useAssessment"
import { useVehicleProfiles } from "@/hooks/useVehicles"
import CheckDetail from "./CheckDetail"

interface Props {
  assessment: VehicleAssessment
  isSelected: boolean
  onSelect: () => void
}

const ratingConfig = {
  GREEN: { badge: "bg-green-600", ring: "ring-green-400", label: "Clear" },
  AMBER: { badge: "bg-amber-500", ring: "ring-amber-400", label: "Caution" },
  RED: { badge: "bg-red-600", ring: "ring-red-400", label: "No access" },
}

export default function VehicleCard({ assessment, isSelected, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false)
  const config = ratingConfig[assessment.overall_rating]
  const { data: vehicles } = useVehicleProfiles()
  const profile = vehicles?.find((v) => v.vehicle_class === assessment.vehicle_class)

  return (
    <Card
      className={`cursor-pointer transition-all ${isSelected ? `ring-2 ${config.ring}` : "hover:border-foreground/20"}`}
      onClick={onSelect}
    >
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          <Truck className="size-5 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate">{assessment.vehicle_name}</p>
            {profile && (
              <p className="text-xs text-muted-foreground">
                {profile.width_m}m W x {profile.length_m}m L x {profile.height_m}m H
              </p>
            )}
          </div>
          <Badge className={config.badge}>{config.label}</Badge>
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          >
            {expanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
          </Button>
        </div>

        {/* Confidence bar */}
        <div className="mt-2 flex items-center gap-2">
          <Progress value={assessment.confidence * 100} className="h-1.5 flex-1" />
          <span className="text-xs text-muted-foreground">
            {Math.round(assessment.confidence * 100)}%
          </span>
        </div>

        {expanded && (
          <div className="mt-3 space-y-2 border-t pt-3">
            {assessment.checks.map((check, i) => <CheckDetail key={i} check={check} />)}
            <p className="text-xs italic text-muted-foreground mt-2">{assessment.recommendation}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
