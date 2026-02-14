import { expect, test } from "@playwright/test"

test.describe("Vehicles Page Layout", () => {
  test("Vehicles page renders with title and sections", async ({ page }) => {
    await page.goto("/vehicles")

    await expect(page.getByRole("heading", { name: "Vehicle Profiles" })).toBeVisible()
    await expect(page.getByText("Manage vehicle profiles used for access assessments")).toBeVisible()
    await expect(page.getByText("Custom Vehicles", { exact: true })).toBeVisible()
    await expect(page.getByText("Default Vehicles", { exact: true })).toBeVisible()
  })

  test("Default vehicles are displayed", async ({ page }) => {
    await page.goto("/vehicles")

    // Should show at least the Luton Van from defaults
    await expect(page.getByText("Luton Van 3.5t")).toBeVisible({ timeout: 10000 })
  })

  test("Default vehicle cards show dimensions", async ({ page }) => {
    await page.goto("/vehicles")

    await expect(page.getByText("Luton Van 3.5t")).toBeVisible({ timeout: 10000 })
    await expect(page.getByText("Dimensions").first()).toBeVisible()
    await expect(page.getByText("Weight").first()).toBeVisible()
    await expect(page.getByText("Turn Radius").first()).toBeVisible()
  })

  test("Add Custom Vehicle button is visible", async ({ page }) => {
    await page.goto("/vehicles")

    await expect(page.getByRole("button", { name: "Add Custom Vehicle" })).toBeVisible()
  })
})

test.describe("Custom Vehicle Form", () => {
  test("Clicking Add Custom Vehicle shows the form", async ({ page }) => {
    await page.goto("/vehicles")

    await page.getByRole("button", { name: "Add Custom Vehicle" }).click()

    await expect(page.getByText("New Vehicle Profile")).toBeVisible()
    await expect(page.getByLabel("Vehicle Name")).toBeVisible()
    await expect(page.getByLabel("Class ID")).toBeVisible()
    await expect(page.getByLabel("Width (m)", { exact: true })).toBeVisible()
    await expect(page.getByLabel("Length (m)", { exact: true })).toBeVisible()
    await expect(page.getByLabel("Height (m)", { exact: true })).toBeVisible()
    await expect(page.getByLabel("Weight (kg)", { exact: true })).toBeVisible()
    await expect(page.getByLabel("Turning Radius (m)", { exact: true })).toBeVisible()
    await expect(page.getByLabel("Mirror Width (m)", { exact: true })).toBeVisible()
  })

  test("Cancel button hides the form", async ({ page }) => {
    await page.goto("/vehicles")

    await page.getByRole("button", { name: "Add Custom Vehicle" }).click()
    await expect(page.getByText("New Vehicle Profile")).toBeVisible()

    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("button", { name: "Add Custom Vehicle" })).toBeVisible()
  })
})

test.describe("Custom Vehicle CRUD", () => {
  test("Create and delete a custom vehicle", async ({ page }) => {
    await page.goto("/vehicles")

    // Use a unique name to avoid collisions with leftover data from previous runs
    const uniqueName = `E2E Van ${Date.now()}`
    const uniqueClass = `e2e_van_${Date.now()}`

    // Open form
    await page.getByRole("button", { name: "Add Custom Vehicle" }).click()

    // Fill in the form
    await page.getByLabel("Vehicle Name").fill(uniqueName)
    await page.getByLabel("Class ID").fill(uniqueClass)
    await page.getByLabel("Width (m)", { exact: true }).fill("2.0")
    await page.getByLabel("Length (m)", { exact: true }).fill("6.0")
    await page.getByLabel("Height (m)", { exact: true }).fill("2.8")
    await page.getByLabel("Weight (kg)", { exact: true }).fill("3500")
    await page.getByLabel("Turning Radius (m)", { exact: true }).fill("6.5")

    await page.getByRole("button", { name: "Create Vehicle" }).click()

    // Custom vehicle should appear in the list with Custom badge
    await expect(page.getByText(uniqueName)).toBeVisible({ timeout: 5000 })
    await expect(page.getByText("Custom").first()).toBeVisible()

    // Now delete it — click the trash button (aria-label) which opens a confirmation dialog
    await page.getByRole("button", { name: `Delete ${uniqueName}` }).click()

    // Confirm the delete in the dialog
    await expect(page.getByRole("heading", { name: "Delete Vehicle" })).toBeVisible()
    await page.getByRole("button", { name: "Delete" }).click()

    // Vehicle should be removed
    await expect(page.getByText(uniqueName)).not.toBeVisible({ timeout: 5000 })
  })
})

test.describe("Vehicles Navigation", () => {
  test("Sidebar has Vehicles link", async ({ page }) => {
    await page.goto("/")

    await expect(page.getByRole("link", { name: "Vehicles" })).toBeVisible()
  })

  test("Vehicles link navigates to vehicles page", async ({ page }) => {
    await page.goto("/")

    await page.getByRole("link", { name: "Vehicles" }).click()
    await page.waitForURL("/vehicles")

    await expect(page.getByRole("heading", { name: "Vehicle Profiles" })).toBeVisible()
  })
})
