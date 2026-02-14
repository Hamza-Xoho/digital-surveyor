import { expect, test } from "@playwright/test"

test.describe("Saved Locations on Assessment Page", () => {
  test("Saved Locations section is visible on assessments page", async ({ page }) => {
    await page.goto("/assessments")

    await expect(page.getByText("Saved Locations")).toBeVisible()
  })

  test("Add button is visible", async ({ page }) => {
    await page.goto("/assessments")

    await expect(page.getByRole("button", { name: "Add" })).toBeVisible()
  })

  test("Clicking Add shows the save location form", async ({ page }) => {
    await page.goto("/assessments")

    await page.getByRole("button", { name: "Add" }).click()

    await expect(page.getByPlaceholder("Label (e.g. Client Home)")).toBeVisible()
    await expect(page.getByPlaceholder("Postcode (e.g. BN1 1AB)")).toBeVisible()
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible()
  })

  test("Cancel hides the form", async ({ page }) => {
    await page.goto("/assessments")

    await page.getByRole("button", { name: "Add" }).click()
    await expect(page.getByPlaceholder("Label (e.g. Client Home)")).toBeVisible()

    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByPlaceholder("Label (e.g. Client Home)")).not.toBeVisible()
  })

  test("Save and delete a location", async ({ page }) => {
    await page.goto("/assessments")

    // Use a unique label to avoid collisions with leftover data from previous runs
    const uniqueLabel = `E2E Loc ${Date.now()}`

    // Open form and save a location
    await page.getByRole("button", { name: "Add" }).click()
    await page.getByPlaceholder("Label (e.g. Client Home)").fill(uniqueLabel)
    await page.getByPlaceholder("Postcode (e.g. BN1 1AB)").fill("SW1A 1AA")
    await page.getByRole("button", { name: "Save" }).click()

    // Location should appear in the list
    const savedBtn = page.getByRole("button", { name: new RegExp(uniqueLabel) })
    await expect(savedBtn).toBeVisible({ timeout: 5000 })
    await expect(savedBtn.getByText("SW1A 1AA")).toBeVisible()

    // Delete it — the trash button is the next sibling of the location button
    const deleteBtn = savedBtn.locator("xpath=following-sibling::button")
    await deleteBtn.click()

    // Location should be removed
    await expect(page.getByText(uniqueLabel)).not.toBeVisible({ timeout: 5000 })
  })

  test("Save Current button appears after running assessment", async ({ page }) => {
    await page.goto("/assessments")

    // Run an assessment first
    await page.getByRole("textbox", { name: "e.g. BN1 1AB" }).fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    // Wait for assessment to complete
    await expect(page.locator("p.text-lg.font-bold", { hasText: "BN1 1AB" })).toBeVisible({
      timeout: 15000,
    })

    // Save Current button should appear
    await expect(page.getByRole("button", { name: "Save Current" })).toBeVisible()
  })
})
