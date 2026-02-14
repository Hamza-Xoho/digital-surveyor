import { useState } from "react"
import { Truck, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { VehicleCreateInput } from "@/hooks/useVehicles"

interface Props {
  onSubmit: (data: VehicleCreateInput) => void
  isPending: boolean
}

const initialState: VehicleCreateInput = {
  name: "",
  vehicle_class: "",
  width_m: 2.5,
  length_m: 7.0,
  height_m: 3.5,
  weight_kg: 7500,
  turning_radius_m: 8.0,
  mirror_width_m: 0.25,
}

export default function VehicleForm({ onSubmit, isPending }: Props) {
  const [form, setForm] = useState(initialState)
  const [open, setOpen] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !form.vehicle_class.trim()) return
    onSubmit({
      ...form,
      vehicle_class: form.vehicle_class.toLowerCase().replace(/\s+/g, "_"),
    })
    setForm(initialState)
    setOpen(false)
  }

  const update = (field: keyof VehicleCreateInput, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  if (!open) {
    return (
      <Button onClick={() => setOpen(true)} className="w-full">
        <Plus className="mr-2 size-4" />
        Add Custom Vehicle
      </Button>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Truck className="size-4" />
          New Vehicle Profile
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <Label htmlFor="veh-name" className="text-xs">Vehicle Name</Label>
              <Input
                id="veh-name"
                placeholder="e.g. Custom Box Truck"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div className="col-span-2">
              <Label htmlFor="veh-class" className="text-xs">Class ID</Label>
              <Input
                id="veh-class"
                placeholder="e.g. custom_box_truck"
                value={form.vehicle_class}
                onChange={(e) => update("vehicle_class", e.target.value)}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div>
              <Label htmlFor="veh-width" className="text-xs">Width (m)</Label>
              <Input
                id="veh-width"
                type="number"
                step="0.1"
                min="0.5"
                max="10"
                value={form.width_m}
                onChange={(e) => update("width_m", parseFloat(e.target.value))}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div>
              <Label htmlFor="veh-length" className="text-xs">Length (m)</Label>
              <Input
                id="veh-length"
                type="number"
                step="0.1"
                min="1"
                max="30"
                value={form.length_m}
                onChange={(e) => update("length_m", parseFloat(e.target.value))}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div>
              <Label htmlFor="veh-height" className="text-xs">Height (m)</Label>
              <Input
                id="veh-height"
                type="number"
                step="0.1"
                min="0.5"
                max="10"
                value={form.height_m}
                onChange={(e) => update("height_m", parseFloat(e.target.value))}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div>
              <Label htmlFor="veh-weight" className="text-xs">Weight (kg)</Label>
              <Input
                id="veh-weight"
                type="number"
                step="100"
                min="500"
                max="100000"
                value={form.weight_kg}
                onChange={(e) => update("weight_kg", parseInt(e.target.value))}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div>
              <Label htmlFor="veh-turn" className="text-xs">Turning Radius (m)</Label>
              <Input
                id="veh-turn"
                type="number"
                step="0.1"
                min="1"
                max="30"
                value={form.turning_radius_m}
                onChange={(e) => update("turning_radius_m", parseFloat(e.target.value))}
                className="mt-1 h-8 text-sm"
                required
              />
            </div>
            <div>
              <Label htmlFor="veh-mirror" className="text-xs">Mirror Width (m)</Label>
              <Input
                id="veh-mirror"
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={form.mirror_width_m}
                onChange={(e) => update("mirror_width_m", parseFloat(e.target.value))}
                className="mt-1 h-8 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={isPending}>
              {isPending ? "Creating..." : "Create Vehicle"}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
