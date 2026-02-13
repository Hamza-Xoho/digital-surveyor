import { useState } from "react"
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Key,
  Loader2,
  MapPin,
  Navigation,
  Camera,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useApiKeyStatus, useUpdateApiKeys } from "@/hooks/useApiKeys"
import useCustomToast from "@/hooks/useCustomToast"

interface StepConfig {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  required: boolean
  fieldName: "os_api_key" | "here_api_key" | "mapillary_token"
  configuredKey: "os_configured" | "here_configured" | "mapillary_configured"
  maskedKey: "os_api_key" | "here_api_key" | "mapillary_token"
  instructions: {
    provider: string
    steps: string[]
    url: string
    urlLabel: string
  }
}

const STEPS: StepConfig[] = [
  {
    id: "os",
    title: "Ordnance Survey Data Hub",
    description:
      "Required for road geometry data. OS MasterMap provides surveyed road edges, building footprints, and kerb lines used for width analysis.",
    icon: <MapPin className="size-5" />,
    required: true,
    fieldName: "os_api_key",
    configuredKey: "os_configured",
    maskedKey: "os_api_key",
    instructions: {
      provider: "Ordnance Survey",
      steps: [
        "Go to the OS Data Hub and create a free account",
        'Create a new project and add the "OS Features API" to it',
        "Copy the API key from your project dashboard",
        "Paste it below",
      ],
      url: "https://osdatahub.os.uk/",
      urlLabel: "OS Data Hub",
    },
  },
  {
    id: "here",
    title: "HERE Routing API",
    description:
      "Optional. Provides truck-specific route restrictions including weight limits, low bridges, and width restrictions along the approach route.",
    icon: <Navigation className="size-5" />,
    required: false,
    fieldName: "here_api_key",
    configuredKey: "here_configured",
    maskedKey: "here_api_key",
    instructions: {
      provider: "HERE",
      steps: [
        "Sign up for a free HERE developer account",
        'Create a new project and generate a "REST API" key',
        "Ensure the Routing API is enabled for your project",
        "Copy the API key and paste it below",
      ],
      url: "https://developer.here.com/",
      urlLabel: "HERE Developer Portal",
    },
  },
  {
    id: "mapillary",
    title: "Mapillary Street Imagery",
    description:
      "Optional. Reserved for future street-level imagery features. Mapillary provides crowd-sourced street photos that can supplement satellite data.",
    icon: <Camera className="size-5" />,
    required: false,
    fieldName: "mapillary_token",
    configuredKey: "mapillary_configured",
    maskedKey: "mapillary_token",
    instructions: {
      provider: "Mapillary",
      steps: [
        "Sign in to Mapillary with your Facebook account",
        "Go to the developer dashboard and register a new application",
        "Copy the client token from your application settings",
        "Paste it below",
      ],
      url: "https://www.mapillary.com/developer",
      urlLabel: "Mapillary Developer",
    },
  },
]

export default function ApiKeySetupWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({
    os_api_key: "",
    here_api_key: "",
    mapillary_token: "",
  })

  const { data: status, isLoading: statusLoading } = useApiKeyStatus()
  const updateMutation = useUpdateApiKeys()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const step = STEPS[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === STEPS.length - 1
  const isConfigured = status?.[step.configuredKey] ?? false

  const handleSaveKey = () => {
    const value = keyInputs[step.fieldName]?.trim()
    if (!value) return

    updateMutation.mutate(
      { [step.fieldName]: value },
      {
        onSuccess: () => {
          showSuccessToast(`${step.instructions.provider} API key saved`)
          setKeyInputs((prev) => ({ ...prev, [step.fieldName]: "" }))
        },
        onError: () => {
          showErrorToast("Failed to save API key")
        },
      },
    )
  }

  const handleRemoveKey = () => {
    updateMutation.mutate(
      { [step.fieldName]: "" },
      {
        onSuccess: () => {
          showSuccessToast(`${step.instructions.provider} API key removed`)
        },
        onError: () => {
          showErrorToast("Failed to remove API key")
        },
      },
    )
  }

  const configuredCount = status
    ? [status.os_configured, status.here_configured, status.mapillary_configured].filter(Boolean).length
    : 0

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6" data-testid="api-key-wizard">
      {/* Progress indicator */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => {
          const configured = status?.[s.configuredKey] ?? false
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => setCurrentStep(i)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                i === currentStep
                  ? "bg-primary text-primary-foreground"
                  : configured
                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    : "bg-muted text-muted-foreground"
              }`}
              data-testid={`wizard-step-${s.id}`}
            >
              {configured ? (
                <CheckCircle2 className="size-3.5" />
              ) : (
                <span className="size-3.5 rounded-full border border-current opacity-50" />
              )}
              {s.instructions.provider}
            </button>
          )
        })}
        <div className="ml-auto text-xs text-muted-foreground">
          {configuredCount}/3 configured
        </div>
      </div>

      {/* Current step card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              {step.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <CardTitle>{step.title}</CardTitle>
                {step.required ? (
                  <Badge variant="destructive" className="text-[10px]">
                    Required
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-[10px]">
                    Optional
                  </Badge>
                )}
              </div>
              <CardDescription>{step.description}</CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Status indicator */}
          {isConfigured && (
            <Alert>
              <CheckCircle2 className="size-4 text-green-600" />
              <AlertTitle className="text-green-700 dark:text-green-400">
                Configured
              </AlertTitle>
              <AlertDescription>
                Current key: <code className="text-xs">{status?.[step.maskedKey]}</code>
              </AlertDescription>
            </Alert>
          )}

          {/* Instructions */}
          <div className="rounded-lg border bg-muted/50 p-4">
            <h4 className="mb-3 flex items-center gap-2 text-sm font-medium">
              <Key className="size-4" />
              How to get your {step.instructions.provider} API key
            </h4>
            <ol className="space-y-2 text-sm text-muted-foreground">
              {step.instructions.steps.map((instruction, i) => (
                <li key={i} className="flex gap-2">
                  <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                    {i + 1}
                  </span>
                  {instruction}
                </li>
              ))}
            </ol>
            <a
              href={step.instructions.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            >
              {step.instructions.urlLabel}
              <ExternalLink className="size-3" />
            </a>
          </div>

          {/* Key input */}
          <div className="flex gap-2">
            <Input
              type="password"
              placeholder={`Paste your ${step.instructions.provider} API key here`}
              value={keyInputs[step.fieldName]}
              onChange={(e) =>
                setKeyInputs((prev) => ({
                  ...prev,
                  [step.fieldName]: e.target.value,
                }))
              }
              data-testid={`api-key-input-${step.id}`}
            />
            <Button
              onClick={handleSaveKey}
              disabled={!keyInputs[step.fieldName]?.trim() || updateMutation.isPending}
              data-testid={`save-key-${step.id}`}
            >
              {updateMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                "Save"
              )}
            </Button>
          </div>

          {isConfigured && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRemoveKey}
              disabled={updateMutation.isPending}
              className="text-destructive hover:text-destructive"
              data-testid={`remove-key-${step.id}`}
            >
              Remove key
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setCurrentStep((s) => s - 1)}
          disabled={isFirstStep}
          data-testid="wizard-prev"
        >
          <ChevronLeft className="mr-1 size-4" />
          Previous
        </Button>
        <Button
          onClick={() => setCurrentStep((s) => s + 1)}
          disabled={isLastStep}
          data-testid="wizard-next"
        >
          Next
          <ChevronRight className="ml-1 size-4" />
        </Button>
      </div>
    </div>
  )
}
