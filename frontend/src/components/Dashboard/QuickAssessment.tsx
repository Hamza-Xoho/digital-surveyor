import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { MapPin, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function QuickAssessment() {
  const [postcode, setPostcode] = useState("")
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!postcode.trim()) return
    navigate({
      to: "/assessments",
      search: { postcode: postcode.trim().toUpperCase() },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="size-4 text-blue-600" />
          Quick Assessment
        </CardTitle>
        <CardDescription>
          Enter a UK postcode to check vehicle access
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            placeholder="e.g. BN1 1AB"
            value={postcode}
            onChange={(e) => setPostcode(e.target.value.toUpperCase())}
            className="flex-1"
            data-testid="quick-postcode-input"
          />
          <Button type="submit" size="sm" disabled={!postcode.trim()}>
            Assess
            <ArrowRight className="ml-1 size-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
