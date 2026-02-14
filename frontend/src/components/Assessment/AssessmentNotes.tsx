import React, { useState } from "react"
import { Pencil, Save, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Props {
  assessmentId: string
  initialNotes: string | null
  onSave: (assessmentId: string, notes: string) => void
  isSaving?: boolean
}

export default function AssessmentNotes({ assessmentId, initialNotes, onSave, isSaving }: Props) {
  const [editing, setEditing] = useState(false)
  const [notes, setNotes] = useState(initialNotes || "")

  const handleSave = () => {
    onSave(assessmentId, notes)
    setEditing(false)
  }

  const handleCancel = () => {
    setNotes(initialNotes || "")
    setEditing(false)
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <span>Notes</span>
          {!editing && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => setEditing(true)}
            >
              <Pencil className="mr-1 size-3" />
              {initialNotes ? "Edit" : "Add"}
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {editing ? (
          <div className="space-y-2">
            <Textarea
              placeholder="Add notes about access, parking, obstacles..."
              value={notes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
              className="min-h-[80px] text-sm"
              maxLength={2000}
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {notes.length}/2000
              </span>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  className="h-7 text-xs"
                  onClick={handleSave}
                  disabled={isSaving}
                >
                  <Save className="mr-1 size-3" />
                  {isSaving ? "Saving..." : "Save"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={handleCancel}
                >
                  <X className="mr-1 size-3" />
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        ) : initialNotes ? (
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{initialNotes}</p>
        ) : (
          <p className="text-xs text-muted-foreground italic">No notes yet</p>
        )}
      </CardContent>
    </Card>
  )
}
