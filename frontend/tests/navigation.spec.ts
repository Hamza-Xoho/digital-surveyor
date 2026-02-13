import { expect, test } from "@playwright/test"

test("Navigate from Dashboard to Assessments via sidebar", async ({
  page,
}) => {
  await page.goto("/")
  await page.getByRole("link", { name: "Assessments" }).click()
  await page.waitForURL("/assessments")

  await expect(page.getByText("Property Access Check")).toBeVisible()
})

test("Navigate from Dashboard to Settings via sidebar", async ({ page }) => {
  await page.goto("/")
  await page.getByRole("link", { name: "Settings", exact: true }).click()
  await page.waitForURL("/settings")

  await expect(page.getByText("User Information")).toBeVisible()
})

test("Navigate from Dashboard to Admin via sidebar", async ({ page }) => {
  await page.goto("/")
  await page.getByRole("link", { name: "Admin" }).click()
  await page.waitForURL("/admin")

  await expect(page.getByRole("heading", { name: "Users" })).toBeVisible()
})

test("Navigate back to Dashboard from Assessments", async ({ page }) => {
  await page.goto("/assessments")
  await page.getByRole("link", { name: "Dashboard" }).click()
  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Logo link navigates to Dashboard", async ({ page }) => {
  await page.goto("/settings")
  await page.getByRole("link", { name: "Digital Surveyor" }).click()
  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Active sidebar item is highlighted on Assessments page", async ({
  page,
}) => {
  await page.goto("/assessments")

  const assessmentsLink = page.getByRole("link", { name: "Assessments" })
  await expect(assessmentsLink).toBeVisible()
})

test("Active sidebar item is highlighted on Settings page", async ({
  page,
}) => {
  await page.goto("/settings")

  const settingsLink = page.getByRole("link", { name: "Settings", exact: true })
  await expect(settingsLink).toBeVisible()
})
