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
        "flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="text-sm text-slate-500">
        {total} {label} · pagina {page} de {Math.max(pages, 1)}
      </span>
      <div className="grid grid-cols-2 gap-2 sm:flex sm:items-center">
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
