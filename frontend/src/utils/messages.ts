const GENERIC_MESSAGE = "Ocorreu um erro inesperado. Tente novamente em instantes.";

function normalizeDetail(detail: string) {
  return detail.trim().toLowerCase();
}

export function getApiErrorMessage(status: number, detail?: string) {
  const normalizedDetail = detail ? normalizeDetail(detail) : "";

  if (status === 400 && normalizedDetail.includes("upload")) {
    return "O arquivo informado nao pode ser processado.";
  }
  if (status === 401 && normalizedDetail.includes("credential")) {
    return "Email ou senha invalidos.";
  }
  if (status === 401) {
    return "Sua sessao expirou. Faca login novamente.";
  }
  if (status === 403) {
    return "Voce nao tem permissao para executar esta acao.";
  }
  if (status === 404) {
    return "O recurso solicitado nao foi encontrado.";
  }
  if (status === 409) {
    return detail || "A operacao nao pode ser concluida no estado atual.";
  }
  if (status === 413) {
    return "O arquivo excede o limite permitido.";
  }
  if (status === 415) {
    return "Formato de arquivo invalido para esta operacao.";
  }
  if (status === 422 && normalizedDetail.includes("exportacao excede o limite")) {
    return detail || "A exportacao excede o limite permitido para esta operacao.";
  }
  if (status === 422) {
    return "Revise os campos informados e tente novamente.";
  }
  if (status === 429 && normalizedDetail.includes("login")) {
    return "Muitas tentativas de login. Aguarde alguns minutos antes de tentar de novo.";
  }
  if (status === 429) {
    return "Muitas requisicoes em pouco tempo. Aguarde um instante e tente novamente.";
  }
  if (status >= 500) {
    return "O servidor nao concluiu a operacao. Tente novamente em instantes.";
  }

  return detail || GENERIC_MESSAGE;
}

export function getErrorMessage(error: unknown, fallback = GENERIC_MESSAGE) {
  if (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    typeof (error as { status: unknown }).status === "number" &&
    "message" in error &&
    typeof (error as { message: unknown }).message === "string"
  ) {
    return getApiErrorMessage(
      (error as { status: number }).status,
      (error as { message: string }).message,
    );
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}

export const LIST_EMPTY_MESSAGES = {
  alerts: "Nenhum alerta encontrado para os filtros atuais.",
  approvals: "Nenhuma alcada encontrada para os filtros informados.",
  audit: "Nenhum evento de auditoria encontrado.",
  suppliers: "Nenhum fornecedor encontrado para os filtros atuais.",
  reports: "Nenhum dado encontrado para os filtros atuais deste relatorio.",
  tickets: "Nenhum chamado encontrado para os filtros selecionados.",
  engineering: "Nenhum chamado da fila de engenharia corresponde aos filtros selecionados.",
  units: "Nenhuma unidade encontrada para os filtros atuais.",
  users: "Nenhum usuario encontrado para os filtros atuais.",
} as const;
