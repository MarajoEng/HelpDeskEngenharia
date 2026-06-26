import { expect, test } from "@playwright/test";

import { mockPortalLogin } from "./support/mockPortal";

test("realiza login local e redireciona para o dashboard", async ({ page }) => {
  await mockPortalLogin(page);
  await page.goto("/login");

  await page.getByLabel("Email").fill("admin@local.test");
  await page.getByLabel("Senha").fill("admin123");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Visao executiva e operacional da rede" })).toBeVisible();
  await expect(page.locator(".form-message--error")).toHaveCount(0);
  await expect(page.getByText(/cors/i)).toHaveCount(0);
  await expect(page.getByText(/invalid email or password/i)).toHaveCount(0);
});
