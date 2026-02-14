import { useState } from "react"
import { MapPin, Plus, Trash2, Navigation } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  useSavedLocations,
  useCreateLocation,
  useDeleteLocation,
} from "@/hooks/useSavedLocations"

interface Props {
  onSelectPostcode: (postcode: string) => void
  currentPostcode?: string
}

export default function SavedLocations({ onSelectPostcode, currentPostcode }: Props) {
  const { data: locations = [], isLoading } = useSavedLocations()
  const createMutation = useCreateLocation()
  const deleteMutation = useDeleteLocation()
  const [showForm, setShowForm] = useState(false)
  const [label, setLabel] = useState("")
  const [postcode, setPostcode] = useState("")

  const handleSave = () => {
    if (!label.trim() || !postcode.trim()) return
    createMutation.mutate(
      { label: label.trim(), postcode: postcode.trim().toUpperCase() },
      {
        onSuccess: () => {
          setLabel("")
          setPostcode("")
          setShowForm(false)
        },
      }
    )
  }

  const handleSaveCurrent = () => {
    if (!currentPostcode) return
    setPostcode(currentPostcode)
    setShowForm(true)
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <MapPin className="size-4" />
            Saved Locations
          </span>
          <div className="flex gap-1">
            {currentPostcode && !showForm && (
              <Button variant="ghost" size="sm" onClick={handleSaveCurrent} className="h-7 text-xs">
                <Plus className="mr-1 size-3" />
                Save Current
              </Button>
            )}
            {!showForm && (
              <Button variant="ghost" size="sm" onClick={() => setShowForm(true)} className="h-7 text-xs">
                <Plus className="mr-1 size-3" />
                Add
              </Button>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {showForm && (
          <div className="mb-3 space-y-2 rounded border p-2">
            <Input
              placeholder="Label (e.g. Client Home)"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="h-8 text-sm"
            />
            <Input
              placeholder="Postcode (e.g. BN1 1AB)"
              value={postcode}
              onChange={(e) => setPostcode(e.target.value.toUpperCase())}
              className="h-8 text-sm"
            />
            <div className="flex gap-1">
              <Button size="sm" className="h-7 text-xs" onClick={handleSave} disabled={createMutation.isPending}>
                {createMutation.isPending ? "Saving..." : "Save"}
              </Button>
              <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : locations.length === 0 ? (
          <p className="py-2 text-center text-xs text-muted-foreground">
            No saved locations yet
          </p>
        ) : (
          <div className="space-y-1">
            {locations.map((loc) => (
              <div
                key={loc.id}
                className="flex items-center gap-2 rounded p-1.5 transition-colors hover:bg-muted/50"
              >
                <button
                  className="flex flex-1 items-center gap-2 text-left text-sm"
                  onClick={() => onSelectPostcode(loc.postcode)}
                >
                  <Navigation className="size-3 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-xs">{loc.label}</p>
                    <p className="text-xs text-muted-foreground">{loc.postcode}</p>
                  </div>
                </button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 shrink-0 p-0 text-muted-foreground hover:text-destructive"
                  onClick={() => deleteMutation.mutate(loc.id)}
                >
                  <Trash2 className="size-3" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
