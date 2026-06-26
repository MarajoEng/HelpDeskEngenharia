import { expect, test } from "@playwright/test";

import { mockAuthenticatedPortal } from "./support/mockPortal";

test("compacta a sidebar e preserva navegacao administrativa", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await mockAuthenticatedPortal(page);
  await page.goto("/dashboard");

  const nav = page.locator("aside nav");
  await expect(nav).toBeVisible();
  await expect(nav).toContainText("Dashboard");
  await expect(nav).toContainText("Chamados");
  await expect(nav).toContainText("Engenharia");
  await expect(nav).toContainText("Relatórios");
  await expect(nav).toContainText("Alertas");
  await expect(nav).toContainText("Configurações");

  await expect(nav).not.toContainText("Abrir chamado");
  await expect(nav).not.toContainText("Unidades");
  await expect(nav).not.toContainText("Usuários");
  await expect(nav).not.toContainText("Fornecedores");
  await expect(nav).not.toContainText("Alçadas");
  await expect(nav).not.toContainText("Auditoria");

  const expandedWidth = await page.locator("aside").evaluate((el) => Math.round(el.getBoundingClientRect().width));
  await page.getByRole("button", { name: "Recolher menu" }).click();
  await expect(page.locator("aside")).toHaveCSS("width", "88px");
  const collapsedWidth = await page.locator("aside").evaluate((el) => Math.round(el.getBoundingClientRect().width));
  expect(collapsedWidth).toBeLessThan(expandedWidth);
  await page.getByRole("button", { name: "Expandir menu" }).click();

  const routeChecks = [
    { path: "/dashboard", active: "Dashboard" },
    { path: "/tickets", active: "Chamados" },
    { path: "/tickets/1", active: "Chamados" },
    { path: "/engineering", active: "Engenharia" },
    { path: "/reports", active: "Relatórios" },
    { path: "/alerts", active: "Alertas" },
    { path: "/settings/tickets", active: "Configurações" },
    { path: "/settings/units", active: "Configurações" },
    { path: "/settings/users", active: "Configurações" },
    { path: "/settings/suppliers", active: "Configurações" },
    { path: "/settings/approval-levels", active: "Configurações" },
    { path: "/settings/audit-logs", active: "Configurações" },
  ];

  for (const route of routeChecks) {
    await page.goto(route.path);
    await expect(page.locator('aside nav a[aria-current="page"]')).toContainText(route.active);
  }

  await page.goto("/settings/units");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Chamados");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Unidades");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Usuários");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Fornecedores");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Alçadas");
  await expect(page.locator('nav[aria-label="Tabs de configurações"]')).toContainText("Auditoria");

  await page.goto("/create-ticket");
  await expect(page).toHaveURL(/\/tickets\/new$/);
  await page.goto("/units");
  await expect(page).toHaveURL(/\/settings\/units$/);
  await page.goto("/users");
  await expect(page).toHaveURL(/\/settings\/users$/);
  await page.goto("/suppliers");
  await expect(page).toHaveURL(/\/settings\/suppliers$/);
  await page.goto("/approval-levels");
  await expect(page).toHaveURL(/\/settings\/approval-levels$/);
  await page.goto("/audit-logs");
  await expect(page).toHaveURL(/\/settings\/audit-logs$/);

  await page.goto("/settings/tickets");
  await expect(page.locator('nav[aria-label="Abas internas de chamados"]')).toContainText("Categorias");
  await expect(page.locator('nav[aria-label="Abas internas de chamados"]')).toContainText("Subcategorias");
  await expect(page.locator('nav[aria-label="Abas internas de chamados"]')).toContainText("Tipos de chamado");
  await expect(page.locator('nav[aria-label="Abas internas de chamados"]')).toContainText("Prioridades");

  const sidebarMetrics = await nav.evaluate((el) => ({
    clientHeight: el.clientHeight,
    scrollHeight: el.scrollHeight,
  }));
  expect(sidebarMetrics.scrollHeight).toBeLessThanOrEqual(sidebarMetrics.clientHeight + 1);

  const layoutMetrics = await page.evaluate(() => {
    const main = document.querySelector("main");
    if (!main) {
      return null;
    }

    return {
      clientWidth: main.clientWidth,
      scrollWidth: main.scrollWidth,
    };
  });

  expect(layoutMetrics).not.toBeNull();
  expect(layoutMetrics?.scrollWidth).toBeLessThanOrEqual((layoutMetrics?.clientWidth ?? 0) + 32);
});
