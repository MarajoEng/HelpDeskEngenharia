import Button from "./Button";

interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  label?: string;
  onPrevious: () => void;
  onNext: () => void;
  className?: string;
}

export default function Pagination({
  page,
  pages,
  total,
  label = "registro(s)",
  onPrevious,
  onNext,
  className = "",
}: PaginationProps) {
  return (
    <div
      className={[
        "flex items-center justify-between gap-4 flex-wrap",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="text-sm text-slate-500">
        {total} {label} · pagina {page} de {Math.max(pages, 1)}
      </span>
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={onPrevious} disabled={page <= 1}>
          Anterior
        </Button>
        <Button variant="secondary" size="sm" onClick={onNext} disabled={pages === 0 || page >= pages}>
          Proxima
        </Button>
      </div>
    </div>
  );
}
