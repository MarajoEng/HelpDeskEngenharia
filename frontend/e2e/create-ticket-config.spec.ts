import { expect, test } from "@playwright/test";

import { mockAuthenticatedPortal } from "./support/mockPortal";

test("CreateTicketPage carrega configuracoes reais e atualiza subcategorias por categoria", async ({ page }) => {
  await mockAuthenticatedPortal(page);
  await page.goto("/tickets/new");

  await expect(page.getByLabel("Categoria", { exact: true })).toContainText("Bombas de combustivel");
  await expect(page.getByLabel("Prioridade")).toContainText("Alta");
  await expect(page.getByLabel("Tipo de chamado")).toContainText("Preventiva");
  await expect(page.getByText("Pressao da linha")).toBeVisible();

  await page.getByLabel("Grupo").selectOption("01");
  await page.getByLabel("Filial").selectOption("1");
  await page.getByLabel("Categoria", { exact: true }).selectOption("2");
  await expect(page.getByLabel("Subcategoria", { exact: true })).toContainText("Quadro eletrico");
  await expect(page.getByLabel("Tipo de chamado")).not.toContainText("Preventiva");
  await expect(page.getByLabel("Tipo de chamado")).toContainText("Emergencial");
  await expect(page.getByText("Sem campos adicionais")).toBeVisible();

  await page.getByLabel("Subcategoria", { exact: true }).selectOption("21");
  await page.getByLabel("Tipo de chamado").selectOption("3");
  await page.getByLabel("Tipo do problema").fill("Quadro sem energia");
  await page.getByLabel("Titulo").fill("Falha eletrica na pista 2");
  await page.getByLabel("Descricao").fill("Sem energia no quadro principal da pista 2.");
  await page.getByLabel("Prioridade").selectOption("2");
  await page.getByRole("button", { name: "Criar chamado" }).click();

  await expect(page.getByText("Chamado criado com sucesso.")).toBeVisible();
  await expect(page.getByText("ENG-20260625-000099")).toBeVisible();
});

test("CreateTicketPage bloqueia abertura quando nao ha categorias ativas", async ({ page }) => {
  await mockAuthenticatedPortal(page);
  await page.route("**/ticket-categories**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 100, pages: 0 }),
    });
  });

  await page.goto("/tickets/new");

  await expect(page.getByText("Configuracao de chamados indisponivel")).toBeVisible();
  await expect(page.getByRole("button", { name: "Criar chamado" })).toHaveCount(0);
});

test("CreateTicketPage trata erro de API sem quebrar a tela", async ({ page }) => {
  await mockAuthenticatedPortal(page);
  await page.route("**/ticket-priorities**", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Falha forcada para teste." }),
    });
  });

  await page.goto("/tickets/new");

  await expect(page.getByText("Nao foi possivel carregar a configuracao do chamado.")).toBeVisible();
});
