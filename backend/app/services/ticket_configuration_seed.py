from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_category import TicketCategoryConfig
from app.models.ticket_priority import TicketPriorityConfig
from app.models.ticket_status import TicketStatusConfig, TicketStatusTransitionConfig
from app.models.ticket_subcategory import TicketSubcategoryConfig
from app.models.ticket_type import TicketTypeConfig
from app.repositories.ticket_configuration_repository import replace_ticket_category_types


CATEGORY_SEED = [
    {
        "name": "Bombas de combustivel",
        "legacy_value": "fuel_pump",
        "description": "Falhas estruturais ou operacionais em bombas de abastecimento.",
        "display_order": 10,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Emergencial", "Inspecao"],
    },
    {
        "name": "Bicos de combustivel",
        "legacy_value": "fuel_nozzle",
        "description": "Problemas de vazamento, travamento ou indisponibilidade em bicos.",
        "display_order": 20,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Emergencial", "Inspecao"],
    },
    {
        "name": "Eletrica",
        "legacy_value": "electrical",
        "description": "Ocorrencias em rede eletrica, iluminacao e quadros.",
        "display_order": 30,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Emergencial", "Inspecao"],
    },
    {
        "name": "Hidraulica",
        "legacy_value": "plumbing",
        "description": "Vazamentos, entupimentos e falhas em encanamento ou sanitarios.",
        "display_order": 40,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Emergencial"],
    },
    {
        "name": "Vazamentos",
        "legacy_value": "leak",
        "description": "Incidentes com perda de combustivel, agua ou outros fluidos.",
        "display_order": 50,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Emergencial", "Inspecao"],
    },
    {
        "name": "Estrutura",
        "legacy_value": "structure",
        "description": "Avarias estruturais, rachaduras, bases e sustentacao.",
        "display_order": 60,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Inspecao"],
    },
    {
        "name": "Cobertura",
        "legacy_value": "roof",
        "description": "Demandas relacionadas a telhado, cobertura e calhas.",
        "display_order": 70,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Emergencial"],
    },
    {
        "name": "Pavimento",
        "legacy_value": "pavement",
        "description": "Buracos, desniveis e manutencao de pista ou patio.",
        "display_order": 80,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Preventiva", "Inspecao"],
    },
    {
        "name": "Risco ambiental",
        "legacy_value": "environmental_risk",
        "description": "Ocorrencias com potencial de impacto ambiental ou regulatorio.",
        "display_order": 90,
        "requires_attachment": True,
        "requires_location": True,
        "type_names": ["Corretiva", "Emergencial", "Inspecao"],
    },
    {
        "name": "Outros",
        "legacy_value": "other",
        "description": "Chamados que nao se enquadram nas categorias operacionais padrao.",
        "display_order": 100,
        "requires_attachment": False,
        "requires_location": False,
        "type_names": ["Corretiva", "Preventiva", "Inspecao"],
    },
]

SUBCATEGORY_SEED = [
    ("Bombas de combustivel", "Falha de pressao", "Queda de desempenho ou indisponibilidade da bomba.", 10),
    ("Bombas de combustivel", "Parada total", "Bomba sem operacao ou sem resposta eletrica.", 20),
    ("Bicos de combustivel", "Vazamento no bico", "Bico vazando durante o abastecimento.", 10),
    ("Bicos de combustivel", "Travamento", "Bico preso ou com retorno incorreto.", 20),
    ("Eletrica", "Iluminacao", "Falha em luminarias, postes ou refletores.", 10),
    ("Eletrica", "Quadro eletrico", "Problemas em disjuntores ou alimentacao.", 20),
    ("Hidraulica", "Banheiros", "Pias, descargas ou pontos de agua internos.", 10),
    ("Hidraulica", "Tubulacao", "Rompimentos ou obstrucoes em encanamentos.", 20),
    ("Vazamentos", "Combustivel", "Perda de combustivel em tanques, linhas ou conexoes.", 10),
    ("Vazamentos", "Agua", "Vazamento de agua com impacto operacional.", 20),
    ("Estrutura", "Rachaduras", "Fissuras ou danos em paredes, bases e estruturas.", 10),
    ("Cobertura", "Telhas", "Danos, desprendimento ou quebra de telhas.", 10),
    ("Cobertura", "Calhas", "Entupimento ou falha de escoamento.", 20),
    ("Pavimento", "Buracos", "Aberturas ou erosoes em pista e patio.", 10),
    ("Risco ambiental", "Contencao", "Falha de barreira ou drenagem ambiental.", 10),
    ("Outros", "Avaliacao geral", "Demandas administrativas ou de apoio operacional.", 10),
]

TYPE_SEED = [
    {"name": "Corretiva", "description": "Atendimento para corrigir falha ja ocorrida.", "display_order": 10},
    {"name": "Preventiva", "description": "Intervencao programada para evitar falhas.", "display_order": 20},
    {"name": "Emergencial", "description": "Acionamento urgente com impacto operacional alto.", "display_order": 30},
    {"name": "Inspecao", "description": "Vistoria tecnica, laudo ou avaliacao de risco.", "display_order": 40},
    {"name": "Orcamento", "description": "Levantamento tecnico para estimativa de custo.", "display_order": 50},
]

PRIORITY_SEED = [
    {
        "name": "Baixa",
        "legacy_value": "low",
        "description": "Pode ser tratada em janela operacional planejada.",
        "color": "#3b82f6",
        "weight": 10,
        "sla_hours": 72,
        "requires_reason": False,
        "display_order": 10,
    },
    {
        "name": "Media",
        "legacy_value": "medium",
        "description": "Exige acompanhamento, mas sem risco imediato severo.",
        "color": "#14b8a6",
        "weight": 20,
        "sla_hours": 48,
        "requires_reason": False,
        "display_order": 20,
    },
    {
        "name": "Alta",
        "legacy_value": "high",
        "description": "Impacto operacional relevante com necessidade de priorizacao.",
        "color": "#f97316",
        "weight": 30,
        "sla_hours": 24,
        "requires_reason": True,
        "display_order": 30,
    },
    {
        "name": "Critica",
        "legacy_value": "critical",
        "description": "Risco imediato para operacao, seguranca ou compliance.",
        "color": "#dc2626",
        "weight": 40,
        "sla_hours": 8,
        "requires_reason": True,
        "display_order": 40,
    },
]

STATUS_SEED = [
    {
        "name": "Aberto",
        "legacy_value": "open",
        "description": "Chamado aberto aguardando triagem.",
        "color": "#2563eb",
        "is_initial": True,
        "is_final": False,
        "pauses_sla": False,
        "allows_reopen": False,
        "display_order": 10,
    },
    {
        "name": "Triagem",
        "legacy_value": "triage",
        "description": "Chamado em analise tecnica.",
        "color": "#7c3aed",
        "is_initial": False,
        "is_final": False,
        "pauses_sla": False,
        "allows_reopen": False,
        "display_order": 20,
    },
    {
        "name": "Aguardando aprovacao",
        "legacy_value": "waiting_approval",
        "description": "Chamado aguardando aprovacao.",
        "color": "#d97706",
        "is_initial": False,
        "is_final": False,
        "pauses_sla": True,
        "allows_reopen": False,
        "display_order": 30,
    },
    {
        "name": "Aprovado",
        "legacy_value": "approved",
        "description": "Chamado aprovado para execucao.",
        "color": "#059669",
        "is_initial": False,
        "is_final": False,
        "pauses_sla": False,
        "allows_reopen": False,
        "display_order": 40,
    },
    {
        "name": "Rejeitado",
        "legacy_value": "rejected",
        "description": "Chamado rejeitado no fluxo de aprovacao.",
        "color": "#dc2626",
        "is_initial": False,
        "is_final": True,
        "pauses_sla": False,
        "allows_reopen": True,
        "display_order": 50,
    },
    {
        "name": "Em atendimento",
        "legacy_value": "in_progress",
        "description": "Chamado em execucao.",
        "color": "#0891b2",
        "is_initial": False,
        "is_final": False,
        "pauses_sla": False,
        "allows_reopen": False,
        "display_order": 60,
    },
    {
        "name": "Aguardando fornecedor",
        "legacy_value": "waiting_supplier",
        "description": "Chamado pausado aguardando fornecedor.",
        "color": "#9333ea",
        "is_initial": False,
        "is_final": False,
        "pauses_sla": True,
        "allows_reopen": False,
        "display_order": 70,
    },
    {
        "name": "Aguardando unidade",
        "legacy_value": "waiting_unit",
        "description": "Chamado pausado aguardando unidade.",
        "color": "#ca8a04",
        "is_initial": False,
        "is_final": False,
        "pauses_sla": True,
        "allows_reopen": False,
        "display_order": 80,
    },
    {
        "name": "Resolvido",
        "legacy_value": "resolved",
        "description": "Chamado resolvido aguardando fechamento.",
        "color": "#16a34a",
        "is_initial": False,
        "is_final": True,
        "pauses_sla": False,
        "allows_reopen": True,
        "display_order": 90,
    },
    {
        "name": "Fechado",
        "legacy_value": "closed",
        "description": "Chamado fechado.",
        "color": "#475569",
        "is_initial": False,
        "is_final": True,
        "pauses_sla": False,
        "allows_reopen": False,
        "display_order": 100,
    },
    {
        "name": "Cancelado",
        "legacy_value": "canceled",
        "description": "Chamado cancelado.",
        "color": "#991b1b",
        "is_initial": False,
        "is_final": True,
        "pauses_sla": False,
        "allows_reopen": True,
        "display_order": 110,
    },
]

TRANSITION_SEED = [
    ("open", "triage", True, False, ["admin", "engineering"]),
    ("waiting_unit", "triage", True, False, ["admin", "engineering"]),
    ("triage", "waiting_approval", True, False, ["admin", "engineering"]),
    ("triage", "in_progress", True, False, ["admin", "engineering"]),
    ("waiting_approval", "approved", True, False, None),
    ("waiting_approval", "rejected", True, False, None),
    ("approved", "in_progress", True, False, ["admin", "engineering"]),
    ("in_progress", "waiting_supplier", True, False, ["admin", "engineering"]),
    ("in_progress", "waiting_unit", True, False, ["admin", "engineering"]),
    ("waiting_supplier", "in_progress", True, False, ["admin", "engineering"]),
    ("waiting_unit", "in_progress", True, False, ["admin", "engineering"]),
    ("in_progress", "resolved", True, True, ["admin", "engineering"]),
    ("resolved", "closed", True, False, ["admin", "engineering"]),
    ("resolved", "in_progress", True, False, ["admin", "engineering"]),
    ("rejected", "triage", True, False, ["admin", "engineering"]),
    ("canceled", "triage", True, False, ["admin"]),
]


def seed_ticket_configurations(session: Session) -> dict[str, list]:
    types_by_name: dict[str, TicketTypeConfig] = {}
    categories_by_name: dict[str, TicketCategoryConfig] = {}
    priorities: list[TicketPriorityConfig] = []
    statuses_by_legacy: dict[str, TicketStatusConfig] = {}
    transitions: list[TicketStatusTransitionConfig] = []
    subcategories: list[TicketSubcategoryConfig] = []

    for data in TYPE_SEED:
        ticket_type = session.scalar(select(TicketTypeConfig).where(TicketTypeConfig.name == data["name"]))
        if ticket_type is None:
            ticket_type = TicketTypeConfig(**data, is_active=True)
            session.add(ticket_type)
            session.flush()
        else:
            ticket_type.description = data["description"]
            ticket_type.display_order = data["display_order"]
            ticket_type.is_active = True
        types_by_name[data["name"]] = ticket_type

    for data in CATEGORY_SEED:
        category = session.scalar(select(TicketCategoryConfig).where(TicketCategoryConfig.name == data["name"]))
        if category is None:
            category = TicketCategoryConfig(
                name=data["name"],
                legacy_value=data["legacy_value"],
                description=data["description"],
                display_order=data["display_order"],
                requires_attachment=data["requires_attachment"],
                requires_location=data["requires_location"],
                is_active=True,
            )
            session.add(category)
            session.flush()
        else:
            category.description = data["description"]
            category.legacy_value = data["legacy_value"]
            category.display_order = data["display_order"]
            category.requires_attachment = data["requires_attachment"]
            category.requires_location = data["requires_location"]
            category.is_active = True

        replace_ticket_category_types(
            session,
            category,
            [types_by_name[type_name].id for type_name in data["type_names"]],
        )
        categories_by_name[data["name"]] = category

    for category_name, name, description, display_order in SUBCATEGORY_SEED:
        category = categories_by_name[category_name]
        subcategory = session.scalar(
            select(TicketSubcategoryConfig).where(
                TicketSubcategoryConfig.category_id == category.id,
                TicketSubcategoryConfig.name == name,
            )
        )
        if subcategory is None:
            subcategory = TicketSubcategoryConfig(
                category_id=category.id,
                name=name,
                description=description,
                display_order=display_order,
                is_active=True,
            )
            session.add(subcategory)
            session.flush()
        else:
            subcategory.category_id = category.id
            subcategory.description = description
            subcategory.display_order = display_order
            subcategory.is_active = True
        subcategories.append(subcategory)

    for data in PRIORITY_SEED:
        priority = session.scalar(select(TicketPriorityConfig).where(TicketPriorityConfig.name == data["name"]))
        if priority is None:
            priority = TicketPriorityConfig(**data, is_active=True)
            session.add(priority)
            session.flush()
        else:
            priority.legacy_value = data["legacy_value"]
            priority.description = data["description"]
            priority.color = data["color"]
            priority.weight = data["weight"]
            priority.sla_hours = data["sla_hours"]
            priority.requires_reason = data["requires_reason"]
            priority.display_order = data["display_order"]
            priority.is_active = True
        priorities.append(priority)

    for data in STATUS_SEED:
        status = session.scalar(
            select(TicketStatusConfig).where(TicketStatusConfig.legacy_value == data["legacy_value"])
        )
        if status is None:
            status = TicketStatusConfig(**data, is_active=True)
            session.add(status)
            session.flush()
        else:
            status.name = data["name"]
            status.description = data["description"]
            status.color = data["color"]
            status.is_initial = data["is_initial"]
            status.is_final = data["is_final"]
            status.pauses_sla = data["pauses_sla"]
            status.allows_reopen = data["allows_reopen"]
            status.display_order = data["display_order"]
            status.is_active = True
        statuses_by_legacy[data["legacy_value"]] = status

    for from_legacy, to_legacy, requires_comment, requires_attachment, allowed_roles in TRANSITION_SEED:
        from_status = statuses_by_legacy[from_legacy]
        to_status = statuses_by_legacy[to_legacy]
        transition = session.scalar(
            select(TicketStatusTransitionConfig).where(
                TicketStatusTransitionConfig.from_status_id == from_status.id,
                TicketStatusTransitionConfig.to_status_id == to_status.id,
            )
        )
        if transition is None:
            transition = TicketStatusTransitionConfig(
                from_status_id=from_status.id,
                to_status_id=to_status.id,
                requires_comment=requires_comment,
                requires_attachment=requires_attachment,
                allowed_roles_json=allowed_roles,
                is_active=True,
            )
            session.add(transition)
            session.flush()
        else:
            transition.requires_comment = requires_comment
            transition.requires_attachment = requires_attachment
            transition.allowed_roles_json = allowed_roles
            transition.is_active = True
        transitions.append(transition)

    return {
        "categories": list(categories_by_name.values()),
        "subcategories": subcategories,
        "types": list(types_by_name.values()),
        "priorities": priorities,
        "statuses": list(statuses_by_legacy.values()),
        "transitions": transitions,
    }
