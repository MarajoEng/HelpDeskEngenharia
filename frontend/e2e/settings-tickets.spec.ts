import { expect, test } from "@playwright/test";

import { mockAuthenticatedPortal } from "./support/mockPortal";

test("valida /settings/tickets com listagem, estado vazio, loading e erro de API", async ({ page }) => {
  await mockAuthenticatedPortal(page);

  await page.goto("/settings/tickets");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Chamados");
  await expect(page.locator('nav[aria-label="Abas internas de chamados"]')).toContainText("Categorias");
  await expect(page.getByRole("heading", { name: "Chamados", exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.locator("tbody tr").first()).toBeVisible();

  await page.getByRole("button", { name: "Prioridades" }).click();
  await expect(page.locator("tbody tr").first()).toBeVisible();

  await page.getByRole("button", { name: "Campos personalizados" }).click();
  await expect(page.getByText("Pressao da linha")).toBeVisible();

  await page.route("**/admin/ticket-categories**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, pages: 0 }),
    });
  });
  await page.route("**/admin/ticket-types**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 100, pages: 0 }),
    });
  });
  await page.goto("/settings/tickets");
  await expect(page.getByText("Nenhuma categoria encontrada")).toBeVisible();

  await page.route("**/admin/ticket-categories**", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10, pages: 0 }),
    });
  });
  await page.route("**/admin/ticket-types**", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 100, pages: 0 }),
    });
  });
  await page.goto("/settings/tickets");
  await expect(page.getByText("Carregando categorias")).toBeVisible();

  await page.route("**/admin/ticket-priorities**", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Falha forcada para teste." }),
    });
  });
  await page.goto("/settings/tickets?tab=priorities");
  await expect(page.getByText("O servidor nao concluiu a operacao. Tente novamente em instantes.")).toBeVisible();
});
