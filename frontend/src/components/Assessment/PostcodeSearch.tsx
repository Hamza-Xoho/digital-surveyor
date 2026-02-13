import { useState, FormEvent } from "react"
import { Search, Loader2 } from "lucide-react"

interface Props {
  onSubmit: (postcode: string) => void
  isLoading: boolean
  error?: string | null
}

const POSTCODE_RE = /^[A-Za-z]{1,2}\d[A-Za-z\d]?\s*\d[A-Za-z]{2}$/

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
    <div className="mb-6">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">
        Property Access Check
      </h2>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={postcode}
          onChange={(e) => { setPostcode(e.target.value.toUpperCase()); setValidationError("") }}
          placeholder="e.g. BN1 1AB"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
          maxLength={8}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          Assess
        </button>
      </form>
      {validationError && <p className="mt-2 text-sm text-red-600">{validationError}</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}
