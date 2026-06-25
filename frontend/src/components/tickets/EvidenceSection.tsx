import { useEffect, useMemo, useState } from "react";

import { downloadAttachment, listTicketAttachments, uploadTicketAttachment } from "../../api/attachmentApi";
import type { TicketAttachment, TicketAttachmentType } from "../../types/attachment";
import { formatDate } from "./ticketUi";

const ATTACHMENT_TYPE_LABELS: Record<TicketAttachmentType, string> = {
  opening_evidence: "Abertura",
  progress_evidence: "Andamento",
  closing_evidence: "Conclusao",
};

interface Props {
  ticketId: number;
  token: string;
  initialAttachments: TicketAttachment[];
  canUpload: boolean;
  onUploaded: () => void;
}

export default function EvidenceSection({ ticketId, token, initialAttachments, canUpload, onUploaded }: Props) {
  const [attachments, setAttachments] = useState<TicketAttachment[]>(initialAttachments);
  const [selectedType, setSelectedType] = useState<TicketAttachmentType>("closing_evidence");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const attachmentCountLabel = useMemo(() => {
    if (attachments.length === 1) return "1 evidencia";
    return `${attachments.length} evidencias`;
  }, [attachments.length]);

  useEffect(() => {
    setAttachments(initialAttachments);
  }, [initialAttachments]);

  useEffect(() => {
    let isActive = true;
    setIsLoading(true);
    setError(null);

    listTicketAttachments(token, ticketId, 1, 50)
      .then((response) => {
        if (!isActive) return;
        setAttachments(response.items);
      })
      .catch((requestError: unknown) => {
        if (!isActive) return;
        setError(requestError instanceof Error ? requestError.message : "Nao foi possivel carregar as evidencias.");
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [ticketId, token]);

  function refreshAttachments() {
    return listTicketAttachments(token, ticketId, 1, 50).then((response) => {
      setAttachments(response.items);
    });
  }

  function handleUpload(event: React.FormEvent) {
    event.preventDefault();

    if (!selectedFile) {
      setError("Selecione um arquivo de evidencia.");
      return;
    }

    setIsUploading(true);
    setError(null);

    uploadTicketAttachment(token, ticketId, {
      file: selectedFile,
      attachment_type: selectedType,
    })
      .then(() => refreshAttachments())
      .then(() => {
        setSelectedFile(null);
        const input = document.getElementById("ticket-evidence-file") as HTMLInputElement | null;
        if (input) input.value = "";
        onUploaded();
      })
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : "Nao foi possivel enviar a evidencia.");
      })
      .finally(() => {
        setIsUploading(false);
      });
  }

  function handleDownload(attachment: TicketAttachment) {
    setError(null);
    downloadAttachment(token, attachment.id)
      .then(({ blob, filename }) => {
        const blobUrl = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = blobUrl;
        anchor.download = filename;
        anchor.target = "_blank";
        anchor.rel = "noreferrer";
        anchor.click();
        URL.revokeObjectURL(blobUrl);
      })
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : "Nao foi possivel baixar a evidencia.");
      });
  }

  return (
    <div className="panel panel--stack">
      <div className="section-heading">
        <div>
          <h3 style={{ margin: "0 0 6px" }}>Evidencias</h3>
          <p className="page__description" style={{ margin: 0 }}>
            Upload auditavel de abertura, andamento e conclusao. {attachmentCountLabel}.
          </p>
        </div>
        <span className="status-badge status-badge--muted">PDF e imagens</span>
      </div>

      {error ? <div className="state-card state-card--error">{error}</div> : null}

      {canUpload ? (
        <form className="evidence-uploader" onSubmit={handleUpload}>
          <label className="field">
            <span>Tipo da evidencia</span>
            <select value={selectedType} onChange={(event) => setSelectedType(event.target.value as TicketAttachmentType)}>
              {Object.entries(ATTACHMENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Arquivo</span>
            <input
              id="ticket-evidence-file"
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>

          <div className="evidence-uploader__actions">
            <p className="field__hint">Limite configuravel no backend. Use `closing_evidence` para resolver o chamado.</p>
            <button className="button-primary" type="submit" disabled={isUploading}>
              {isUploading ? "Enviando..." : "Enviar evidencia"}
            </button>
          </div>
        </form>
      ) : (
        <div className="state-card">Seu perfil pode visualizar as evidencias, mas nao pode enviar novos anexos nesta fase.</div>
      )}

      {isLoading ? <div className="state-card">Carregando evidencias...</div> : null}

      {!isLoading && attachments.length === 0 ? (
        <div className="state-card">Nenhuma evidencia enviada ainda para este chamado.</div>
      ) : null}

      {!isLoading && attachments.length > 0 ? (
        <div className="evidence-grid" style={{ maxHeight: "400px", overflowY: "auto", paddingRight: "8px" }}>
          {attachments.map((attachment) => (
            <article className="evidence-card" key={attachment.id}>
              <div className="evidence-card__header">
                <strong>{ATTACHMENT_TYPE_LABELS[attachment.attachment_type as TicketAttachmentType] ?? attachment.attachment_type}</strong>
                <span className="status-badge status-badge--muted">{attachment.file_type}</span>
              </div>
              <dl className="evidence-card__meta">
                <div>
                  <dt>Enviado por</dt>
                  <dd>{attachment.uploaded_by_user_name ?? `#${attachment.uploaded_by_user_id}`}</dd>
                </div>
                <div>
                  <dt>Data</dt>
                  <dd>{formatDate(attachment.created_at)}</dd>
                </div>
              </dl>
              <button className="button-secondary" type="button" onClick={() => handleDownload(attachment)}>
                Baixar ou visualizar
              </button>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
