import { expect, test } from "@playwright/test"

test("Dashboard shows welcome message with user email", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("heading", { level: 1 })).toContainText("Hi,")
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Dashboard shows user greeting with email", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
})

test("Dashboard shows Run Assessment card", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Run Assessment")).toBeVisible()
  await expect(
    page.getByText("Check vehicle access for a UK postcode"),
  ).toBeVisible()
})

test("Dashboard shows Account Settings card", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Account Settings")).toBeVisible()
  await expect(
    page.getByText("Manage your profile and preferences"),
  ).toBeVisible()
})

test("Dashboard Run Assessment card links to assessments page", async ({
  page,
}) => {
  await page.goto("/")

  await page.getByText("Run Assessment").click()
  await page.waitForURL("/assessments")
})

test("Dashboard Account Settings card links to settings page", async ({
  page,
}) => {
  await page.goto("/")

  await page.getByText("Account Settings").click()
  await page.waitForURL("/settings")
})

test("Dashboard shows API Configuration card for superuser", async ({
  page,
}) => {
  await page.goto("/")

  await expect(page.getByText("API Configuration")).toBeVisible()
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

test("Footer is visible with copyright text", async ({ page }) => {
  await page.goto("/")

  await expect(page.getByText("Digital Surveyor ©")).toBeVisible()
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
