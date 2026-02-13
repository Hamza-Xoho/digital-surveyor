import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { request as __request } from "@/client/core/request"

export interface ApiKeyStatus {
  os_api_key: string
  here_api_key: string
  mapillary_token: string
  os_configured: boolean
  here_configured: boolean
  mapillary_configured: boolean
}

interface ApiKeyUpdate {
  os_api_key?: string | null
  here_api_key?: string | null
  mapillary_token?: string | null
}

async function fetchApiKeyStatus(): Promise<ApiKeyStatus> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/settings/api-keys",
  })
}

async function updateApiKeys(data: ApiKeyUpdate): Promise<ApiKeyStatus> {
  return __request(OpenAPI, {
    method: "PUT",
    url: "/api/v1/settings/api-keys",
    body: data,
    mediaType: "application/json",
  })
}

export function useApiKeyStatus() {
  return useQuery({
    queryKey: ["api-key-status"],
    queryFn: fetchApiKeyStatus,
    retry: false,
  })
}

export function useUpdateApiKeys() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: updateApiKeys,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-key-status"] })
    },
  })
}
