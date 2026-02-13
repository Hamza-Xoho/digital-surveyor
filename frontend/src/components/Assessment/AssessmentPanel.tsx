import type { AssessmentResult } from "../../hooks/useAssessment"
import VehicleCard from "./VehicleCard"
import ElevationChart from "./ElevationChart"

interface Props {
  result: AssessmentResult
  selectedVehicle: string | null
  onVehicleSelect: (vehicleClass: string | null) => void
}

const ratingColors = {
  GREEN: "bg-green-100 text-green-800 border-green-300",
  AMBER: "bg-amber-100 text-amber-800 border-amber-300",
  RED: "bg-red-100 text-red-800 border-red-300",
}

export default function AssessmentPanel({ result, selectedVehicle, onVehicleSelect }: Props) {
  return (
    <div className="space-y-4">
      <div className={`p-3 rounded-lg border text-center font-semibold ${ratingColors[result.overall_rating]}`}>
        {result.postcode} — Overall: {result.overall_rating}
      </div>

      {result.width_analysis && (
        <div className="p-3 bg-gray-50 rounded-lg text-sm">
          <p className="font-medium text-gray-700 mb-1">Road Width</p>
          <p className="text-gray-600">
            Min: {result.width_analysis.min_width_m}m | Mean: {result.width_analysis.mean_width_m}m | Max: {result.width_analysis.max_width_m}m
          </p>
        </div>
      )}

      {result.gradient_analysis && (
        <div className="p-3 bg-gray-50 rounded-lg text-sm">
          <p className="font-medium text-gray-700 mb-1">Approach Gradient</p>
          <p className="text-gray-600">
            Max: {result.gradient_analysis.max_gradient_pct}% | Mean: {result.gradient_analysis.mean_gradient_pct}%
          </p>
          {result.gradient_analysis.steep_segments.length > 0 && (
            <p className="text-amber-600 mt-1">
              {result.gradient_analysis.steep_segments.length} steep segment(s) detected
            </p>
          )}
        </div>
      )}

      <div className="space-y-3">
        <h3 className="font-semibold text-gray-800">Vehicle Assessments</h3>
        {result.vehicle_assessments.map((va) => (
          <VehicleCard
            key={va.vehicle_class}
            assessment={va}
            isSelected={selectedVehicle === va.vehicle_class}
            onSelect={() => onVehicleSelect(selectedVehicle === va.vehicle_class ? null : va.vehicle_class)}
          />
        ))}
      </div>

      {result.gradient_analysis && <ElevationChart gradient={result.gradient_analysis} />}
    </div>
  )
}
