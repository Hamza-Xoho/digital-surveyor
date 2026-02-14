import { useState } from "react"
import { createFileRoute } from "@tanstack/react-router"
import { Truck, Trash2, Ruler, Weight, RotateCcw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  useVehicleProfiles,
  useCustomVehicles,
  useCreateVehicle,
  useDeleteVehicle,
  type VehicleProfile,
} from "@/hooks/useVehicles"
import VehicleForm from "@/components/Vehicles/VehicleForm"

export const Route = createFileRoute("/_layout/vehicles")({
  component: VehiclesPage,
  head: () => ({
    meta: [{ title: "Vehicles - Digital Surveyor" }],
  }),
})

function VehicleProfileCard({
  vehicle,
  isCustom,
  onDelete,
}: {
  vehicle: VehicleProfile
  isCustom?: boolean
  onDelete?: () => void
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
              <Truck className="size-5 text-primary" />
            </div>
            <div>
              <p className="font-medium">{vehicle.name}</p>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {vehicle.vehicle_class}
                </Badge>
                {isCustom && (
                  <Badge variant="secondary" className="text-xs">Custom</Badge>
                )}
              </div>
            </div>
          </div>
          {isCustom && onDelete && (
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-destructive"
              aria-label={`Delete ${vehicle.name}`}
              onClick={onDelete}
            >
              <Trash2 className="size-4" />
            </Button>
          )}
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 text-center text-sm">
          <div className="rounded-md bg-muted/50 p-2">
            <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
              <Ruler className="size-3" />
              Dimensions
            </div>
            <p className="mt-1 font-medium">
              {vehicle.width_m} x {vehicle.length_m} x {vehicle.height_m}m
            </p>
          </div>
          <div className="rounded-md bg-muted/50 p-2">
            <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
              <Weight className="size-3" />
              Weight
            </div>
            <p className="mt-1 font-medium">
              {(vehicle.weight_kg / 1000).toFixed(1)}t
            </p>
          </div>
          <div className="rounded-md bg-muted/50 p-2">
            <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
              <RotateCcw className="size-3" />
              Turn Radius
            </div>
            <p className="mt-1 font-medium">{vehicle.turning_radius_m}m</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function VehiclesPage() {
  const { data: defaults = [], isLoading: loadingDefaults } = useVehicleProfiles()
  const { data: custom = [], isLoading: loadingCustom } = useCustomVehicles()
  const createMutation = useCreateVehicle()
  const deleteMutation = useDeleteVehicle()
  const [deleteTarget, setDeleteTarget] = useState<VehicleProfile | null>(null)

  const isLoading = loadingDefaults || loadingCustom

  const handleConfirmDelete = () => {
    if (deleteTarget?.id) {
      deleteMutation.mutate(deleteTarget.id)
    }
    setDeleteTarget(null)
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Vehicle Profiles</h1>
        <p className="text-sm text-muted-foreground">
          Manage vehicle profiles used for access assessments
        </p>
      </div>

      {/* Custom vehicles section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Custom Vehicles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <VehicleForm
            onSubmit={(data) => createMutation.mutate(data)}
            isPending={createMutation.isPending}
          />
          {loadingCustom ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : custom.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              No custom vehicles yet. Add one above to use it in assessments.
            </p>
          ) : (
            <div className="space-y-3">
              {custom.map((v) => (
                <VehicleProfileCard
                  key={v.id}
                  vehicle={v}
                  isCustom
                  onDelete={() => setDeleteTarget(v)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Default vehicles */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Default Vehicles</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {defaults.map((v) => (
                <VehicleProfileCard key={v.vehicle_class} vehicle={v} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(open: boolean) => !open && setDeleteTarget(null)}>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>Delete Vehicle</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteTarget?.name}&rdquo;? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
