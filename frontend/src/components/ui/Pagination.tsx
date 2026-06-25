import Button from "./Button";
import { cx } from "./cx";

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
  className,
}: PaginationProps) {
  return (
    <div className={cx("ui-pagination", className)}>
      <span className="ui-pagination__summary">
        {total} {label} · pagina {page} de {Math.max(pages, 1)}
      </span>
      <div className="ui-pagination__actions">
        <Button variant="secondary" onClick={onPrevious} disabled={page <= 1}>
          Anterior
        </Button>
        <Button variant="secondary" onClick={onNext} disabled={pages === 0 || page >= pages}>
          Proxima
        </Button>
      </div>
    </div>
  );
}
