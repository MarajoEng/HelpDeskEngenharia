import type { Page, Route } from "@playwright/test";

const authToken = "e2e-auth-token";

const currentUser = {
  id: 1,
  name: "Admin Local",
  email: "admin@local.test",
  role: "admin",
  unit_id: null,
};

export async function resetBrowserState(page: Page) {
  await page.context().clearCookies();
}

const units = [
  {
    id: 1,
    code: "01-001",
    name: "Unidade Centro",
    city: "Sao Paulo",
    state: "SP",
    region: "Sudeste",
    group_code: "01",
    branch_code: "001",
    is_active: true,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const categories = [
  {
    id: 1,
    name: "Bombas de combustivel",
    legacy_value: "fuel_pump",
    description: "Falhas em bombas.",
    is_active: true,
    display_order: 10,
    requires_attachment: true,
    requires_location: true,
    type_ids: [1, 2],
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
  {
    id: 2,
    name: "Eletrica",
    legacy_value: "electrical",
    description: "Falhas eletricas.",
    is_active: true,
    display_order: 20,
    requires_attachment: true,
    requires_location: true,
    type_ids: [1, 3],
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const subcategoriesByCategory: Record<number, Array<Record<string, unknown>>> = {
  1: [
    {
      id: 11,
      category_id: 1,
      category_name: "Bombas de combustivel",
      name: "Falha de pressao",
      description: "Queda de desempenho.",
      is_active: true,
      display_order: 10,
      created_at: "2026-06-25T12:00:00Z",
      updated_at: "2026-06-25T12:00:00Z",
    },
  ],
  2: [
    {
      id: 21,
      category_id: 2,
      category_name: "Eletrica",
      name: "Quadro eletrico",
      description: "Sem energia no quadro.",
      is_active: true,
      display_order: 10,
      created_at: "2026-06-25T12:00:00Z",
      updated_at: "2026-06-25T12:00:00Z",
    },
  ],
};

const ticketTypes = [
  {
    id: 1,
    name: "Corretiva",
    description: "Correcao imediata.",
    is_active: true,
    display_order: 10,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
  {
    id: 2,
    name: "Preventiva",
    description: "Prevencao.",
    is_active: true,
    display_order: 20,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
  {
    id: 3,
    name: "Emergencial",
    description: "Urgencia.",
    is_active: true,
    display_order: 30,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const priorities = [
  {
    id: 1,
    name: "Baixa",
    legacy_value: "low",
    description: "Pode esperar.",
    color: "#3b82f6",
    weight: 10,
    sla_hours: 72,
    requires_reason: false,
    is_active: true,
    display_order: 10,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
  {
    id: 2,
    name: "Alta",
    legacy_value: "high",
    description: "Prioridade alta.",
    color: "#f97316",
    weight: 30,
    sla_hours: 24,
    requires_reason: true,
    is_active: true,
    display_order: 20,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const statuses = [
  {
    id: 1,
    name: "Aberto",
    legacy_value: "open",
    description: "Chamado aberto.",
    color: "#2563eb",
    is_initial: true,
    is_final: false,
    pauses_sla: false,
    allows_reopen: false,
    is_active: true,
    display_order: 10,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
  {
    id: 2,
    name: "Triagem",
    legacy_value: "triage",
    description: "Chamado em triagem.",
    color: "#7c3aed",
    is_initial: false,
    is_final: false,
    pauses_sla: false,
    allows_reopen: false,
    is_active: true,
    display_order: 20,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const statusTransitions = [
  {
    id: 1,
    from_status_id: 1,
    from_status_name: "Aberto",
    to_status_id: 2,
    to_status_name: "Triagem",
    to_status_color: "#7c3aed",
    requires_comment: true,
    requires_attachment: false,
    allowed_roles_json: ["admin", "engineering"],
    is_active: true,
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const customFields = [
  {
    id: 101,
    category_id: 1,
    category_name: "Bombas de combustivel",
    subcategory_id: null,
    subcategory_name: null,
    name: "pressao_linha",
    label: "Pressao da linha",
    description: "Leitura operacional opcional.",
    field_type: "text",
    is_required: false,
    is_active: true,
    display_order: 10,
    placeholder: "Ex.: baixa",
    help_text: "Informe se a unidade ja tiver medido.",
    validation_json: null,
    options: [],
    created_at: "2026-06-25T12:00:00Z",
    updated_at: "2026-06-25T12:00:00Z",
  },
];

const ticketSummary = {
  id: 1,
  ticket_number: "ENG-20260625-000001",
  unit_id: 1,
  opened_by_user_id: 1,
  assigned_to_user_id: null,
  category_id: 1,
  subcategory_id: 11,
  type_id: 1,
  priority_id: 2,
  category: "fuel_pump",
  category_name: "Bombas de combustivel",
  subcategory_name: "Falha de pressao",
  type_name: "Corretiva",
  problem_type: "Falha de pressao",
  title: "Bomba principal sem operacao",
  description: "A bomba principal da pista 2 parou de funcionar.",
  priority: "high",
  priority_name: "Alta",
  severity: "critical",
  status: "open",
  status_id: 1,
  status_name: "Aberto",
  status_color: "#2563eb",
  operational_impact: "Pista 2 parada.",
  fuel_nozzles_stopped: 2,
  estimated_daily_loss: "1500.00",
  estimated_loss_total: "3000.00",
  estimated_cost: "8000.00",
  approved_cost: null,
  final_cost: null,
  requires_approval: true,
  opened_at: "2026-06-25T12:00:00Z",
  triaged_at: null,
  approved_at: null,
  started_at: null,
  resolved_at: null,
  closed_at: null,
  sla_due_at: null,
  expected_resolution_at: null,
  supplier_id: null,
  created_at: "2026-06-25T12:00:00Z",
  updated_at: "2026-06-25T12:00:00Z",
  unit_name: "Unidade Centro",
  unit_code: "01-001",
  opened_by_user_name: "Admin Local",
  assigned_to_user_name: null,
  supplier_name: null,
  has_closing_evidence: false,
};

const ticketDetail = {
  ...ticketSummary,
  unit: {
    id: 1,
    code: "U-001",
    name: "Unidade Centro",
    city: "Sao Paulo",
    state: "SP",
  },
  opened_by: {
    id: 1,
    name: "Admin Local",
  },
  assigned_to: null,
  supplier: null,
  history: [],
  approvals: [],
  attachments: [],
  indicators: {
    estimated_loss_total: "3000.00",
    elapsed_hours: 4,
    is_late: false,
    sla_status: "no_sla",
    elapsed_execution_hours: null,
    execution_is_late: false,
    total_hours: 4,
    resolution_hours: null,
    closure_hours: null,
    final_cost: null,
    has_closing_evidence: false,
  },
  custom_fields: [],
};

function pageResponse<T>(items: T[]) {
  return {
    items,
    total: items.length,
    page: 1,
    page_size: items.length || 1,
    pages: items.length > 0 ? 1 : 0,
  };
}

function dashboardOverview() {
  return {
    total_tickets: 1,
    open_tickets: 1,
    triage_tickets: 0,
    waiting_approval_tickets: 0,
    approved_tickets: 0,
    in_progress_tickets: 0,
    resolved_tickets: 0,
    closed_tickets: 0,
    canceled_tickets: 0,
    late_tickets: 0,
    critical_tickets: 1,
    tickets_with_fuel_nozzles_stopped: 1,
    total_fuel_nozzles_stopped: 2,
    estimated_daily_loss_total: 1500,
    estimated_cost_total: 8000,
    approved_cost_total: 0,
    final_cost_total: 0,
    average_resolution_hours: 0,
    average_closure_hours: 0,
    sla_compliance_rate: 100,
    executive_cards: {
      total_open: 1,
      total_late: 0,
      total_critical: 1,
      total_in_progress: 0,
      total_fuel_nozzles_stopped: 2,
      estimated_daily_loss_total: 1500,
      final_cost_total: 0,
      sla_compliance_rate: 100,
    },
    ranking_units_by_tickets: [
      {
        unit_id: 1,
        unit_code: "01-001",
        unit_name: "Unidade Centro",
        total_tickets: 1,
        late_tickets: 0,
        critical_tickets: 1,
      },
    ],
    ranking_units_by_cost: [
      {
        unit_id: 1,
        unit_code: "01-001",
        unit_name: "Unidade Centro",
        estimated_cost_total: 8000,
        final_cost_total: 0,
      },
    ],
    ranking_units_by_fuel_nozzles: [
      {
        unit_id: 1,
        unit_code: "01-001",
        unit_name: "Unidade Centro",
        total_fuel_nozzles_stopped: 2,
        estimated_daily_loss_total: 1500,
      },
    ],
    tickets_by_status: [{ status: "open", total: 1 }],
    tickets_by_category: [{ category: "fuel_pump", total: 1 }],
    tickets_by_priority: [{ priority: "high", total: 1 }],
    tickets_by_severity: [{ severity: "critical", total: 1 }],
    sla_summary: {
      total_with_sla: 1,
      on_track: 1,
      late: 0,
      closed_on_time: 0,
      closed_late: 0,
      compliance_rate: 100,
    },
    late_tickets_preview: [],
  };
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export async function mockAuthenticatedPortal(page: Page) {
  await resetBrowserState(page);
  await page.addInitScript((token: string) => {
    window.localStorage.setItem("portal_chamados_auth_token", token);
  }, authToken);

  await mockPortalApi(page);
}

export async function mockPortalLogin(page: Page) {
  await resetBrowserState(page);
  await mockPortalApi(page);
}

async function mockPortalApi(page: Page) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const { pathname } = url;
    const method = request.method();

    if (pathname === "/auth/login" && method === "POST") {
      await fulfillJson(route, { access_token: authToken, token_type: "bearer" });
      return;
    }

    if (pathname === "/auth/me") {
      await fulfillJson(route, currentUser);
      return;
    }

    if (pathname === "/dashboard/overview") {
      await fulfillJson(route, dashboardOverview());
      return;
    }

    if (pathname === "/alerts") {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    if (pathname === "/tickets" && method === "GET") {
      await fulfillJson(route, pageResponse([ticketSummary]));
      return;
    }

    if (pathname === "/tickets" && method === "POST") {
      const payload = request.postDataJSON() as Record<string, unknown>;
      await fulfillJson(route, {
        ...ticketSummary,
        id: 99,
        ticket_number: "ENG-20260625-000099",
        title: payload.title ?? ticketSummary.title,
        description: payload.description ?? ticketSummary.description,
        problem_type: payload.problem_type ?? ticketSummary.problem_type,
        category_id: payload.category_id ?? ticketSummary.category_id,
        subcategory_id: payload.subcategory_id ?? ticketSummary.subcategory_id,
        type_id: payload.type_id ?? ticketSummary.type_id,
        priority_id: payload.priority_id ?? ticketSummary.priority_id,
        status_id: ticketSummary.status_id,
        status_name: ticketSummary.status_name,
        status_color: ticketSummary.status_color,
      }, 201);
      return;
    }

    if (pathname === "/tickets/form-schema") {
      const categoryId = Number(url.searchParams.get("category_id"));
      await fulfillJson(route, {
        category_id: categoryId,
        subcategory_id: url.searchParams.get("subcategory_id")
          ? Number(url.searchParams.get("subcategory_id"))
          : null,
        fields: customFields.filter((field) => field.category_id === categoryId),
      });
      return;
    }

    if (pathname === "/tickets/1" || pathname === "/tickets/99") {
      await fulfillJson(route, {
        ...ticketDetail,
        id: pathname === "/tickets/99" ? 99 : 1,
        ticket_number: pathname === "/tickets/99" ? "ENG-20260625-000099" : ticketDetail.ticket_number,
      });
      return;
    }

    if (pathname.match(/^\/tickets\/\d+\/available-transitions$/)) {
      await fulfillJson(route, {
        ticket_id: 1,
        current_status_id: 1,
        current_status_name: "Aberto",
        transitions: statusTransitions.map((transition) => ({
          transition_id: transition.id,
          from_status_id: transition.from_status_id,
          to_status_id: transition.to_status_id,
          to_status_name: transition.to_status_name,
          to_status_color: transition.to_status_color,
          requires_comment: transition.requires_comment,
          requires_attachment: transition.requires_attachment,
        })),
      });
      return;
    }

    if (pathname.match(/^\/tickets\/\d+\/transition$/) && method === "PATCH") {
      await fulfillJson(route, {
        ...ticketDetail,
        status: "triage",
        status_id: 2,
        status_name: "Triagem",
        status_color: "#7c3aed",
      });
      return;
    }

    if (pathname.match(/^\/tickets\/\d+\/attachments$/)) {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    if (pathname.match(/^\/attachments\/\d+\/download$/)) {
      await route.fulfill({
        status: 200,
        contentType: "application/octet-stream",
        body: "",
      });
      return;
    }

    if (pathname === "/units") {
      await fulfillJson(route, pageResponse(units));
      return;
    }

    if (pathname === "/units/groups") {
      await fulfillJson(route, [{ group_code: "01", total_units: 1 }]);
      return;
    }

    if (pathname === "/units/1") {
      await fulfillJson(route, units[0]);
      return;
    }

    if (pathname === "/users") {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    if (pathname === "/suppliers") {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    if (pathname === "/approval-levels") {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    if (pathname === "/audit-logs") {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    if (pathname === "/ticket-categories") {
      await fulfillJson(route, pageResponse(categories));
      return;
    }

    if (pathname.startsWith("/ticket-categories/") && pathname.endsWith("/subcategories")) {
      const categoryId = Number(pathname.split("/")[2]);
      await fulfillJson(route, pageResponse(subcategoriesByCategory[categoryId] ?? []));
      return;
    }

    if (pathname === "/ticket-types") {
      await fulfillJson(route, pageResponse(ticketTypes));
      return;
    }

    if (pathname === "/ticket-priorities") {
      await fulfillJson(route, pageResponse(priorities));
      return;
    }

    if (pathname === "/ticket-statuses") {
      await fulfillJson(route, pageResponse(statuses));
      return;
    }

    if (pathname === "/admin/ticket-categories") {
      await fulfillJson(route, pageResponse(categories));
      return;
    }

    if (pathname === "/admin/ticket-subcategories") {
      await fulfillJson(route, pageResponse(Object.values(subcategoriesByCategory).flat()));
      return;
    }

    if (pathname === "/admin/ticket-types") {
      await fulfillJson(route, pageResponse(ticketTypes));
      return;
    }

    if (pathname === "/admin/ticket-priorities") {
      await fulfillJson(route, pageResponse(priorities));
      return;
    }

    if (pathname === "/admin/ticket-statuses") {
      if (method === "POST") {
        const payload = request.postDataJSON() as Record<string, unknown>;
        await fulfillJson(route, { ...statuses[0], ...payload, id: 99 }, 201);
        return;
      }
      await fulfillJson(route, pageResponse(statuses));
      return;
    }

    if (pathname.match(/^\/admin\/ticket-statuses\/\d+$/) && method === "PATCH") {
      const payload = request.postDataJSON() as Record<string, unknown>;
      await fulfillJson(route, { ...statuses[0], ...payload });
      return;
    }

    if (pathname === "/admin/ticket-status-transitions") {
      if (method === "POST") {
        const payload = request.postDataJSON() as Record<string, unknown>;
        await fulfillJson(route, { ...statusTransitions[0], ...payload, id: 99 }, 201);
        return;
      }
      await fulfillJson(route, pageResponse(statusTransitions));
      return;
    }

    if (pathname.match(/^\/admin\/ticket-status-transitions\/\d+$/) && method === "PATCH") {
      const payload = request.postDataJSON() as Record<string, unknown>;
      await fulfillJson(route, { ...statusTransitions[0], ...payload });
      return;
    }

    if (pathname === "/admin/ticket-custom-fields") {
      await fulfillJson(route, pageResponse(customFields));
      return;
    }

    if (pathname.startsWith("/reports/")) {
      await fulfillJson(route, pageResponse([]));
      return;
    }

    await fulfillJson(route, {});
  });
}
