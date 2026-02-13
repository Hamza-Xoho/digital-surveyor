import { expect, test } from "@playwright/test"

test.describe("Assessment Page Layout", () => {
  test("Assessment page renders map and search panel", async ({ page }) => {
    await page.goto("/assessments")

    // Map should be visible (Leaflet container)
    await expect(page.locator(".leaflet-container")).toBeVisible()

    // Search form should be visible
    await expect(page.getByText("Property Access Check")).toBeVisible()
    await expect(
      page.getByRole("textbox", { name: "e.g. BN1 1AB" }),
    ).toBeVisible()
    await expect(page.getByRole("button", { name: "Assess" })).toBeVisible()
  })

  test("Map has zoom controls", async ({ page }) => {
    await page.goto("/assessments")

    await expect(page.getByRole("button", { name: "Zoom in" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Zoom out" })).toBeVisible()
  })

  test("Map shows OpenStreetMap attribution", async ({ page }) => {
    await page.goto("/assessments")

    await expect(page.getByText("OpenStreetMap contributors")).toBeVisible()
  })
})

test.describe("Postcode Validation", () => {
  test("Submit empty postcode shows validation error", async ({ page }) => {
    await page.goto("/assessments")

    await page.getByRole("button", { name: "Assess" }).click()

    await expect(page.getByText("Enter a postcode")).toBeVisible()
  })

  test("Submit invalid postcode format shows validation error", async ({
    page,
  }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("INVALID")
    await page.getByRole("button", { name: "Assess" }).click()

    await expect(
      page.getByText("Invalid UK postcode format"),
    ).toBeVisible()
  })

  test("Submit partial postcode shows validation error", async ({ page }) => {
    await page.goto("/assessments")

    await page.getByRole("textbox", { name: "e.g. BN1 1AB" }).fill("BN1")
    await page.getByRole("button", { name: "Assess" }).click()

    await expect(
      page.getByText("Invalid UK postcode format"),
    ).toBeVisible()
  })

  test("Postcode input auto-uppercases", async ({ page }) => {
    await page.goto("/assessments")

    const input = page.getByRole("textbox", { name: "e.g. BN1 1AB" })
    await input.fill("bn1 1ab")

    await expect(input).toHaveValue("BN1 1AB")
  })

  test("Postcode input has max length of 8", async ({ page }) => {
    await page.goto("/assessments")

    const input = page.getByRole("textbox", { name: "e.g. BN1 1AB" })
    await expect(input).toHaveAttribute("maxlength", "8")
  })
})

test.describe("Assessment Flow", () => {
  test("Valid postcode returns assessment results", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    // Wait for results to appear (overall rating badge)
    await expect(page.getByText(/BN1 1AB — Overall:/)).toBeVisible({
      timeout: 15000,
    })
  })

  test("Assessment shows overall rating badge", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    // Overall rating should be GREEN, AMBER, or RED
    await expect(
      page.getByText(/BN1 1AB — Overall: (GREEN|AMBER|RED)/),
    ).toBeVisible({ timeout: 15000 })
  })

  test("Assessment shows three vehicle cards", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    // Wait for results
    await expect(page.getByText(/BN1 1AB — Overall:/)).toBeVisible({
      timeout: 15000,
    })

    // All three vehicle types should be present
    await expect(page.getByText("Luton Van 3.5t")).toBeVisible()
    await expect(page.getByText("Box Truck 7.5t")).toBeVisible()
    await expect(page.getByText("Pantechnicon 18t")).toBeVisible()
  })

  test("Assessment shows Vehicle Assessments heading", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    await expect(
      page.getByRole("heading", { name: "Vehicle Assessments" }),
    ).toBeVisible({ timeout: 15000 })
  })

  test("Assessment shows Road Width analysis section", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    await expect(page.getByText("Road Width")).toBeVisible({
      timeout: 15000,
    })
  })

  test("Vehicle cards show rating status text", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    // Wait for results
    await expect(page.getByText(/BN1 1AB — Overall:/)).toBeVisible({
      timeout: 15000,
    })

    // Each vehicle card should show a status (Clear, Caution, or No access)
    const statusTexts = page.getByText(/^(Clear|Caution|No access)$/)
    await expect(statusTexts.first()).toBeVisible()
  })
})

test.describe("Vehicle Card Expansion", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/assessments")
    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()
    await expect(page.getByText(/BN1 1AB — Overall:/)).toBeVisible({
      timeout: 15000,
    })
  })

  test("Expanding vehicle card shows check details", async ({ page }) => {
    // Click the expand/collapse chevron button near Luton Van
    // The card structure has the vehicle name, a truck icon, and an expand button
    const lutonCard = page.getByText("Luton Van 3.5t").locator("..").locator("..")
    await lutonCard.locator("button").click()

    // Should show individual checks
    await expect(page.getByText("Gradient", { exact: true })).toBeVisible()
    await expect(page.getByText("Turning Space", { exact: true })).toBeVisible()
    await expect(page.getByText("Route Restrictions", { exact: true })).toBeVisible()
  })

  test("Expanding vehicle card shows recommendation", async ({ page }) => {
    const firstCard = page.getByText("Luton Van 3.5t").locator("..")
    const expandBtn = firstCard.locator("..").locator("button").last()
    await expandBtn.click()

    // Should show recommendation text
    await expect(page.getByText(/Luton Van 3.5t .*/)).toBeVisible()
  })

  test("Expanding vehicle card shows confidence score", async ({ page }) => {
    const firstCard = page.getByText("Luton Van 3.5t").locator("..")
    const expandBtn = firstCard.locator("..").locator("button").last()
    await expandBtn.click()

    // Should show confidence percentage
    await expect(page.getByText(/Confidence: \d+%/)).toBeVisible()
  })
})

test.describe("Multiple Assessments", () => {
  test("Can run a second assessment after the first", async ({ page }) => {
    await page.goto("/assessments")

    // First assessment
    const input = page.getByRole("textbox", { name: "e.g. BN1 1AB" })
    await input.fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()
    await expect(page.getByText(/BN1 1AB — Overall:/)).toBeVisible({
      timeout: 15000,
    })

    // Second assessment with different postcode
    await input.fill("SW1A 1AA")
    await page.getByRole("button", { name: "Assess" }).click()
    await expect(page.getByText(/SW1A 1AA — Overall:/)).toBeVisible({
      timeout: 15000,
    })
  })
})

test.describe("Assessment Error Handling", () => {
  test("Non-existent postcode shows error message", async ({ page }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("ZZ99 9ZZ")
    await page.getByRole("button", { name: "Assess" }).click()

    // Should show the "Postcode not found" error from the backend
    await expect(
      page.getByText(/Postcode not found/),
    ).toBeVisible({ timeout: 15000 })
  })

  test("Assess button remains functional after assessment completes", async ({
    page,
  }) => {
    await page.goto("/assessments")

    await page
      .getByRole("textbox", { name: "e.g. BN1 1AB" })
      .fill("BN1 1AB")
    await page.getByRole("button", { name: "Assess" }).click()

    // After results load, the button should be enabled again
    await expect(page.getByText(/BN1 1AB — Overall:/)).toBeVisible({
      timeout: 15000,
    })
    await expect(
      page.getByRole("button", { name: "Assess" }),
    ).toBeEnabled()
  })
})
