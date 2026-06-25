import { ApiError, apiBaseUrl, requestJson } from "./http";
import type { TicketAttachment, TicketAttachmentListResponse, TicketAttachmentType } from "../types/attachment";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function uploadTicketAttachment(
  token: string,
  ticketId: number,
  payload: { file: File; attachment_type: TicketAttachmentType | string },
) {
  const formData = new FormData();
  formData.append("attachment_type", payload.attachment_type);
  formData.append("file", payload.file);

  return requestJson<TicketAttachment>(`/tickets/${ticketId}/attachments`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
}

export function listTicketAttachments(token: string, ticketId: number, page = 1, pageSize = 20) {
  return requestJson<TicketAttachmentListResponse>(
    `/tickets/${ticketId}/attachments?page=${page}&page_size=${pageSize}`,
    {
      headers: authHeaders(token),
    },
  );
}

export async function downloadAttachment(token: string, attachmentId: number) {
  const response = await fetch(new URL(`/attachments/${attachmentId}/download`, apiBaseUrl).toString(), {
    headers: authHeaders(token),
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) {
        detail = data.detail;
      }
    }

    throw new ApiError(response.status, detail);
  }

  return {
    blob: await response.blob(),
    contentType: response.headers.get("content-type") || "application/octet-stream",
    filename:
      response.headers
        .get("content-disposition")
        ?.split("filename=")[1]
        ?.replace(/"/g, "")
        ?.trim() || `attachment-${attachmentId}`,
  };
}
