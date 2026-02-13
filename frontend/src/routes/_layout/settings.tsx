import { createFileRoute } from "@tanstack/react-router"

import ApiKeySetupWizard from "@/components/UserSettings/ApiKeySetupWizard"
import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"

const tabsConfig = [
  { value: "my-profile", title: "My profile", component: UserInformation },
  { value: "password", title: "Password", component: ChangePassword },
  { value: "api-keys", title: "API Keys", component: ApiKeySetupWizard, superuserOnly: true },
  { value: "danger-zone", title: "Danger zone", component: DeleteAccount, hideSuperuser: true },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: "Settings - Digital Surveyor",
      },
    ],
  }),
})

function UserSettings() {
  const { user: currentUser } = useAuth()

  if (!currentUser) {
    return null
  }

  const visibleTabs = tabsConfig.filter((tab) => {
    if (tab.superuserOnly && !currentUser.is_superuser) return false
    if (tab.hideSuperuser && currentUser.is_superuser) return false
    return true
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and application configuration
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
          {visibleTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} data-testid={`tab-${tab.value}`}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {visibleTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
