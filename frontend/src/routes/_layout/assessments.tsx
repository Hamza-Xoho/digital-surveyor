import { useState } from "react"
import { createFileRoute } from "@tanstack/react-router"
import MapContainer from "../../components/Map/MapContainer"
import PostcodeSearch from "../../components/Assessment/PostcodeSearch"
import AssessmentPanel from "../../components/Assessment/AssessmentPanel"
import { useRunAssessment, type AssessmentResult } from "../../hooks/useAssessment"

export const Route = createFileRoute("/_layout/assessments")({
  component: AssessmentsPage,
})

function AssessmentsPage() {
  const [result, setResult] = useState<AssessmentResult | null>(null)
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null)
  const mutation = useRunAssessment()

  const handleSearch = (postcode: string) => {
    mutation.mutate(postcode, {
      onSuccess: (data) => {
        setResult(data)
        setSelectedVehicle(null)
      },
    })
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-0">
      {/* Map — 70% width */}
      <div className="w-[70%] relative">
        <MapContainer
          assessment={result}
          selectedVehicle={selectedVehicle}
        />
      </div>

      {/* Panel — 30% width */}
      <div className="w-[30%] overflow-y-auto border-l bg-white p-4">
        <PostcodeSearch
          onSubmit={handleSearch}
          isLoading={mutation.isPending}
          error={mutation.error?.message}
        />

        {result && (
          <AssessmentPanel
            result={result}
            selectedVehicle={selectedVehicle}
            onVehicleSelect={setSelectedVehicle}
          />
        )}
      </div>
    </div>
  )
}
