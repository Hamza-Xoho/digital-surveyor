import { AlertTriangle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useUpdateAssessmentNotes, type AssessmentResult } from "@/hooks/useAssessment"
import VehicleCard from "./VehicleCard"
import ElevationChart from "./ElevationChart"
import DataSourceBanner from "./DataSourceBanner"
import AssessmentNotes from "./AssessmentNotes"

interface Props {
  result: AssessmentResult
  selectedVehicle: string | null
  onVehicleSelect: (vehicleClass: string | null) => void
}

const ratingConfig = {
  GREEN: { variant: "default" as const, className: "bg-green-600 hover:bg-green-700", label: "Clear Access" },
  AMBER: { variant: "default" as const, className: "bg-amber-500 hover:bg-amber-600", label: "Caution" },
  RED: { variant: "destructive" as const, className: "", label: "Restricted" },
}

function isDataAvailable(val: number | undefined | null): boolean {
  return val !== undefined && val !== null && val > 0
}

export default function AssessmentPanel({ result, selectedVehicle, onVehicleSelect }: Props) {
  const widthAvailable = result.width_analysis && isDataAvailable(result.width_analysis.max_width_m)
  const gradientAvailable = result.gradient_analysis && isDataAvailable(result.gradient_analysis.max_gradient_pct)
  const ratingCfg = ratingConfig[result.overall_rating]
  const notesMutation = useUpdateAssessmentNotes()

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-bold">{result.postcode}</p>
              <p className="text-xs text-muted-foreground">
                {result.latitude.toFixed(5)}, {result.longitude.toFixed(5)}
              </p>
            </div>
            <Badge className={ratingCfg.className} variant={ratingCfg.variant}>
              {ratingCfg.label}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Data warnings */}
      {(!widthAvailable || !gradientAvailable) && (
        <Alert variant="default" className="border-amber-300 bg-amber-50 dark:bg-amber-950/30">
          <AlertTriangle className="size-4 text-amber-600" />
          <AlertDescription className="text-sm">
            {!widthAvailable && !gradientAvailable
              ? "Road width and gradient data are limited. Results may use estimated values."
              : !widthAvailable
                ? "Road width data limited — using estimated values from road classification."
                : "Gradient data limited — elevation data may be approximate."}
          </AlertDescription>
        </Alert>
      )}

      {/* Road Width */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Road Width</CardTitle>
        </CardHeader>
        <CardContent>
          {widthAvailable ? (
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-xl font-bold">{result.width_analysis!.min_width_m.toFixed(1)}m</p>
                <p className="text-xs text-muted-foreground">Minimum</p>
              </div>
              <div>
                <p className="text-xl font-bold">{result.width_analysis!.mean_width_m.toFixed(1)}m</p>
                <p className="text-xs text-muted-foreground">Average</p>
              </div>
              <div>
                <p className="text-xl font-bold">{result.width_analysis!.max_width_m.toFixed(1)}m</p>
                <p className="text-xs text-muted-foreground">Maximum</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No road width data available
            </p>
          )}
        </CardContent>
      </Card>

      {/* Gradient */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Approach Gradient</CardTitle>
        </CardHeader>
        <CardContent>
          {gradientAvailable ? (
            <>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div>
                  <p className="text-xl font-bold">{result.gradient_analysis!.max_gradient_pct.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">Maximum</p>
                </div>
                <div>
                  <p className="text-xl font-bold">{result.gradient_analysis!.mean_gradient_pct.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">Average</p>
                </div>
              </div>
              {result.gradient_analysis!.steep_segments.length > 0 && (
                <p className="mt-2 text-xs text-amber-600">
                  {result.gradient_analysis!.steep_segments.length} steep segment(s) detected
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              No gradient data available
            </p>
          )}
        </CardContent>
      </Card>

      {/* Vehicle Assessments */}
      <div className="space-y-3">
        <h3 className="font-semibold">Vehicle Assessments</h3>
        {result.vehicle_assessments.map((va) => (
          <VehicleCard
            key={va.vehicle_class}
            assessment={va}
            isSelected={selectedVehicle === va.vehicle_class}
            onSelect={() => onVehicleSelect(selectedVehicle === va.vehicle_class ? null : va.vehicle_class)}
          />
        ))}
      </div>

      {/* Elevation Chart */}
      {result.gradient_analysis && gradientAvailable && (
        <ElevationChart gradient={result.gradient_analysis} />
      )}

      {/* Assessment Notes (only for persisted assessments) */}
      {result.id && (
        <AssessmentNotes
          assessmentId={result.id}
          initialNotes={result.notes ?? null}
          onSave={(id, notes) => notesMutation.mutate({ assessmentId: id, notes })}
          isSaving={notesMutation.isPending}
        />
      )}

      {/* Data Sources */}
      {result.data_sources && (
        <DataSourceBanner dataSources={result.data_sources} />
      )}
    </div>
  )
}
