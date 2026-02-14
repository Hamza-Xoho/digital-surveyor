import { useState, FormEvent } from "react"
import { Search, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface Props {
  onSubmit: (postcode: string) => void
  isLoading: boolean
  error?: string | null
}

const POSTCODE_RE = /^[A-Za-z]{1,2}\d[A-Za-z\d]?\s*\d[A-Za-z]{2}$/

function formatPostcode(value: string): string {
  const clean = value.replace(/\s+/g, "").toUpperCase()
  if (clean.length > 3) {
    return `${clean.slice(0, -3)} ${clean.slice(-3)}`
  }
  return clean
}

export default function PostcodeSearch({ onSubmit, isLoading, error }: Props) {
  const [postcode, setPostcode] = useState("")
  const [validationError, setValidationError] = useState("")

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setValidationError("")
    const trimmed = postcode.trim()
    if (!trimmed) { setValidationError("Enter a postcode"); return }
    if (!POSTCODE_RE.test(trimmed)) { setValidationError("Invalid UK postcode format"); return }
    onSubmit(trimmed)
  }

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold">Property Access Check</h2>
        <p className="text-sm text-muted-foreground">
          Enter a UK postcode to assess vehicle access
        </p>
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          type="text"
          value={postcode}
          onChange={(e) => { setPostcode(formatPostcode(e.target.value)); setValidationError("") }}
          placeholder="e.g. BN1 1AB"
          disabled={isLoading}
          maxLength={9}
          className="flex-1"
          data-testid="postcode-input"
        />
        <Button type="submit" disabled={isLoading} data-testid="assess-button">
          {isLoading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Search className="mr-2 size-4" />}
          Assess
        </Button>
      </form>
      {validationError && <p className="text-sm text-destructive">{validationError}</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
