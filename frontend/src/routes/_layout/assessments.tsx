import { useState, useEffect } from "react"
import { createFileRoute, useSearch } from "@tanstack/react-router"
import { Loader2, MapPin } from "lucide-react"
import MapContainer from "@/components/Map/MapContainer"
import PostcodeSearch from "@/components/Assessment/PostcodeSearch"
import AssessmentPanel from "@/components/Assessment/AssessmentPanel"
import SavedLocations from "@/components/Assessment/SavedLocations"
import { useRunAssessment, type AssessmentResult } from "@/hooks/useAssessment"

export const Route = createFileRoute("/_layout/assessments")({
  component: AssessmentsPage,
  head: () => ({
    meta: [{ title: "Assessments - Digital Surveyor" }],
  }),
  validateSearch: (search: Record<string, unknown>) => ({
    postcode: (search.postcode as string) || undefined,
  }),
})

function AssessmentsPage() {
  const { postcode: searchPostcode } = useSearch({ from: "/_layout/assessments" })
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

  // Auto-run assessment when navigated with ?postcode= param
  useEffect(() => {
    if (searchPostcode && !result && !mutation.isPending) {
      handleSearch(searchPostcode)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchPostcode])

  return (
    <div className="-m-6 md:-m-8 flex h-[calc(100vh-4rem)]">
      {/* Map — 60% width */}
      <div className="relative w-[60%]">
        <MapContainer
          assessment={result}
          selectedVehicle={selectedVehicle}
        />
      </div>

      {/* Panel — 40% width */}
      <div className="w-[40%] overflow-y-auto border-l bg-background p-5">
        <PostcodeSearch
          onSubmit={handleSearch}
          isLoading={mutation.isPending}
          error={mutation.error?.message}
        />

        <div className="mt-3">
          <SavedLocations
            onSelectPostcode={handleSearch}
            currentPostcode={result?.postcode}
          />
        </div>

        {mutation.isPending && (
          <div className="mt-8 flex flex-col items-center gap-3 text-muted-foreground">
            <Loader2 className="size-8 animate-spin" />
            <p className="text-sm">Analysing property access...</p>
          </div>
        )}

        {!mutation.isPending && !result && (
          <div className="mt-12 flex flex-col items-center gap-3 text-muted-foreground">
            <MapPin className="size-12 opacity-30" />
            <div className="text-center">
              <p className="text-sm font-medium">No assessment yet</p>
              <p className="text-xs mt-1">
                Enter a UK postcode above to get started
              </p>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-4">
            <AssessmentPanel
              result={result}
              selectedVehicle={selectedVehicle}
              onVehicleSelect={setSelectedVehicle}
            />
          </div>
        )}
      </div>
    </div>
  )
}
