import { expect, test } from "@playwright/test"

test("Dashboard shows welcome message", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("heading", { level: 1, name: /Welcome back/ })).toBeVisible()
  await expect(
    page.getByText("Assess vehicle access for UK properties"),
  ).toBeVisible()
})

test("Dashboard shows user greeting with email", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
})

test("Dashboard shows Quick Assessment card", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Quick Assessment")).toBeVisible()
  await expect(
    page.getByText("Enter a UK postcode to check vehicle access"),
  ).toBeVisible()
})

test("Dashboard shows Recent Assessments card", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Recent Assessments")).toBeVisible()
})

test("Dashboard Quick Assessment has postcode input", async ({
  page,
}) => {
  await page.goto("/")

  await expect(
    page.getByRole("textbox", { name: "e.g. BN1 1AB" }),
  ).toBeVisible()
})

test("Dashboard shows Data Sources card for superuser", async ({
  page,
}) => {
  await page.goto("/")

  await expect(page.getByText("Data Sources")).toBeVisible()
  await expect(page.getByText("Ordnance Survey")).toBeVisible()
})

test("Sidebar navigation links are visible", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Assessments" }),
  ).toBeVisible()
  await expect(page.getByRole("link", { name: "Settings", exact: true })).toBeVisible()
})

test("Sidebar shows Admin link for superuser", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("link", { name: "Admin" })).toBeVisible()
})

test("Sidebar shows Digital Surveyor logo", async ({ page }) => {
  await page.goto("/")

  await expect(
    page.getByRole("link", { name: "Digital Surveyor" }),
  ).toBeVisible()
})

test("Footer is visible with version text", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Digital Surveyor v")).toBeVisible()
})

test("Theme toggle button is visible", async ({ page }) => {
  await page.goto("/")

  await expect(
    page.getByRole("button", { name: /appearance|toggle theme/i }),
  ).toBeVisible()
})

test("User menu button is visible in sidebar", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByTestId("user-menu")).toBeVisible()
})

test("Dashboard stats show Total Assessments", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Total Assessments")).toBeVisible()
})

test("Dashboard stats show Vehicle Profiles", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Vehicle Profiles")).toBeVisible()
})
