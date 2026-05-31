"use client";

import Button from "@/components/ui/Button";
import { useI18n } from "@/providers/I18nProvider";

export default function PaginationControls({
  page,
  totalPages,
  pageNumbers,
  hasNextPage,
  hasPreviousPage,
  onPageChange,
  onNext,
  onPrevious,
}: {
  page: number;
  totalPages: number;
  pageNumbers: number[];
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  onPageChange: (page: number) => void;
  onNext: () => void;
  onPrevious: () => void;
}) {
  const { t } = useI18n();

  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      className="
        mt-8
        flex
        flex-wrap
        items-center
        justify-between
        gap-4
      "
      aria-label="Pagination"
    >
      <p className="text-sm text-zinc-500">
        {t("common.page")} {page} {t("common.of")} {totalPages}
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={!hasPreviousPage}
          onClick={onPrevious}
          aria-label={t("common.previous")}
        >
          {t("common.previous")}
        </Button>

        {pageNumbers.map((pageNumber) => (
          <Button
            key={pageNumber}
            variant={
              pageNumber === page ? "primary" : "secondary"
            }
            size="sm"
            onClick={() => onPageChange(pageNumber)}
            aria-current={
              pageNumber === page ? "page" : undefined
            }
          >
            {pageNumber}
          </Button>
        ))}

        <Button
          variant="secondary"
          size="sm"
          disabled={!hasNextPage}
          onClick={onNext}
          aria-label={t("common.next")}
        >
          {t("common.next")}
        </Button>
      </div>
    </nav>
  );
}
