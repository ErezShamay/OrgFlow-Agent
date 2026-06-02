"use client";

import { useMemo, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

import Button from "@/components/ui/Button";
import { useLockBodyScroll } from "@/hooks/useLockBodyScroll";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_LIST_BUTTON,
} from "@/lib/field-reports/touch-input-class";

export type CatalogFamily = {
  top_family: string;
  label_he?: string;
  issue_count?: number;
};

export type CatalogCategory = {
  top_family: string;
  category_id: string;
  category_name_he: string;
};

export type CatalogIssue = {
  issue_id: string;
  issue_name_he: string;
  standard_ref?: string | null;
  top_family: string;
  category_id: string;
  category_name_he: string;
  severity?: string | null;
  description?: string | null;
};

type CatalogIssuePickerProps = {
  families: CatalogFamily[];
  categories: CatalogCategory[];
  issues: CatalogIssue[];
  disabled?: boolean;
  onClose: () => void;
  onConfirm: (issue: CatalogIssue) => void;
};

export default function CatalogIssuePicker({
  families,
  categories,
  issues,
  disabled = false,
  onClose,
  onConfirm,
}: CatalogIssuePickerProps) {
  const [selectedFamily, setSelectedFamily] = useState<string | null>(
    null
  );
  const [selectedCategoryId, setSelectedCategoryId] = useState<
    string | null
  >(null);
  const [selectedIssue, setSelectedIssue] = useState<CatalogIssue | null>(
    null
  );
  const [search, setSearch] = useState("");

  useLockBodyScroll(true);

  const searchResults = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return [];
    }

    return issues
      .filter((issue) => {
        const haystack = [
          issue.issue_id,
          issue.issue_name_he,
          issue.category_name_he,
          issue.standard_ref || "",
        ]
          .join(" ")
          .toLowerCase();
        return haystack.includes(query);
      })
      .slice(0, 30);
  }, [issues, search]);

  const visibleCategories = useMemo(() => {
    if (!selectedFamily) {
      return [];
    }

    return categories.filter(
      (category) => category.top_family === selectedFamily
    );
  }, [categories, selectedFamily]);

  const visibleIssues = useMemo(() => {
    if (!selectedCategoryId) {
      return [];
    }

    return issues.filter(
      (issue) => issue.category_id === selectedCategoryId
    );
  }, [issues, selectedCategoryId]);

  function selectFamily(topFamily: string) {
    setSelectedFamily(topFamily);
    setSelectedCategoryId(null);
    setSelectedIssue(null);
    setSearch("");
  }

  function selectCategory(categoryId: string) {
    setSelectedCategoryId(categoryId);
    setSelectedIssue(null);
    setSearch("");
  }

  const pickerBody = (
  <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden">
      <input
        className={FR_TOUCH_INPUT}
        placeholder="חיפוש לפי מזהה, שם, קטגוריה או תקן"
        value={search}
        onChange={(event) => {
          setSearch(event.target.value);
          if (event.target.value.trim()) {
            setSelectedFamily(null);
            setSelectedCategoryId(null);
            setSelectedIssue(null);
          }
        }}
      />

      {search.trim() ? (
        <ul className="min-h-0 flex-1 space-y-2 overflow-y-auto overscroll-contain text-sm">
          {searchResults.length === 0 ? (
            <li className="text-zinc-500">לא נמצאו תוצאות.</li>
          ) : (
            searchResults.map((issue) => (
              <li key={issue.issue_id}>
                <IssueListButton
                  issue={issue}
                  active={selectedIssue?.issue_id === issue.issue_id}
                  disabled={disabled}
                  onSelect={() => setSelectedIssue(issue)}
                />
              </li>
            ))
          )}
        </ul>
      ) : (
        <div className="grid min-h-0 flex-1 gap-4 overflow-y-auto overscroll-contain lg:grid-cols-3">
          <PickerColumn title="משפחה">
            {families.map((family) => {
              const active = selectedFamily === family.top_family;
              return (
                <div key={family.top_family}>
                  <button
                    type="button"
                    className={
                      active
                        ? `${FR_TOUCH_LIST_BUTTON} border-brand bg-brand text-white`
                        : `${FR_TOUCH_LIST_BUTTON} border-zinc-200 bg-white hover:border-brand dark:border-zinc-700 dark:bg-zinc-900`
                    }
                    onClick={() => selectFamily(family.top_family)}
                    disabled={disabled}
                  >
                    {family.label_he || family.top_family}
                    {family.issue_count != null ? (
                      <span className="block text-xs opacity-80">
                        {family.issue_count} ממצאים
                      </span>
                    ) : null}
                  </button>
                </div>
              );
            })}
          </PickerColumn>

          <PickerColumn title="קטגוריה">
            {!selectedFamily ? (
              <p className="text-sm text-zinc-500">בחר משפחה תחילה.</p>
            ) : (
              visibleCategories.map((category) => {
                const active =
                  selectedCategoryId === category.category_id;
                return (
                  <div key={category.category_id}>
                    <button
                      type="button"
                      className={
                        active
                          ? `${FR_TOUCH_LIST_BUTTON} border-brand bg-brand text-white`
                          : `${FR_TOUCH_LIST_BUTTON} border-zinc-200 bg-white hover:border-brand dark:border-zinc-700 dark:bg-zinc-900`
                      }
                      onClick={() =>
                        selectCategory(category.category_id)
                      }
                      disabled={disabled}
                    >
                      {category.category_name_he}
                    </button>
                  </div>
                );
              })
            )}
          </PickerColumn>

          <PickerColumn title="ממצא">
            {!selectedCategoryId ? (
              <p className="text-sm text-zinc-500">בחר קטגוריה תחילה.</p>
            ) : (
              visibleIssues.map((issue) => (
                <li key={issue.issue_id}>
                  <IssueListButton
                    issue={issue}
                    active={selectedIssue?.issue_id === issue.issue_id}
                    disabled={disabled}
                    onSelect={() => setSelectedIssue(issue)}
                  />
                </li>
              ))
            )}
          </PickerColumn>
        </div>
      )}

      {selectedIssue ? (
        <div className="shrink-0 space-y-3 rounded-xl border border-zinc-200 bg-white p-4 text-sm dark:bg-zinc-900">
          <p className="font-medium">{selectedIssue.issue_name_he}</p>
          <p className="text-zinc-600">
            {selectedIssue.issue_id} · {selectedIssue.category_name_he}
          </p>
          {selectedIssue.standard_ref ? (
            <p>
              <span className="font-medium">תקן: </span>
              {selectedIssue.standard_ref}
            </p>
          ) : (
            <p className="text-zinc-500">ללא תקן במפרט</p>
          )}
          {selectedIssue.severity ? (
            <p>
              <span className="font-medium">חומרה: </span>
              {selectedIssue.severity}
            </p>
          ) : null}
          {selectedIssue.description ? (
            <p className="whitespace-pre-wrap text-zinc-700">
              {selectedIssue.description}
            </p>
          ) : null}
          <Button
            type="button"
            size="lg"
            className={`w-full ${FR_TOUCH_BUTTON}`}
            disabled={disabled}
            onClick={() => onConfirm(selectedIssue)}
          >
            אישור והוספה לדוח
          </Button>
        </div>
      ) : null}
    </div>
  );

  const desktopPanel = (
    <div className="hidden space-y-4 rounded-xl border border-brand/30 bg-brand/5 p-4 lg:block">
      <PickerHeader disabled={disabled} onClose={onClose} />
      {pickerBody}
    </div>
  );

  const tabletPanel =
    typeof document !== "undefined"
      ? createPortal(
          <div
            className="fixed inset-0 z-[60] flex flex-col bg-zinc-50 dark:bg-zinc-950 lg:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="בחירת ממצא מהמפרט"
          >
            <header className="shrink-0 border-b border-zinc-200 bg-white px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))] dark:border-zinc-800 dark:bg-zinc-900">
              <PickerHeader disabled={disabled} onClose={onClose} />
            </header>
            <div className="flex min-h-0 flex-1 flex-col px-4 py-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
              {pickerBody}
            </div>
          </div>,
          document.body
        )
      : null;

  return (
    <>
      {desktopPanel}
      {tabletPanel}
    </>
  );
}

function PickerHeader({
  disabled,
  onClose,
}: {
  disabled: boolean;
  onClose: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="text-lg font-semibold lg:text-base lg:font-medium">
        בחירת ממצא מהמפרט
      </h3>
      <Button
        variant="secondary"
        size="lg"
        className={FR_TOUCH_BUTTON}
        type="button"
        disabled={disabled}
        onClick={onClose}
      >
        סגור
      </Button>
    </div>
  );
}

function PickerColumn({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-0 flex-col gap-2">
      <p className="text-xs font-medium text-zinc-500">{title}</p>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto overscroll-contain">
        {children}
      </div>
    </div>
  );
}

function IssueListButton({
  issue,
  active,
  disabled,
  onSelect,
}: {
  issue: CatalogIssue;
  active: boolean;
  disabled: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      className={
        active
          ? `${FR_TOUCH_LIST_BUTTON} border-brand bg-brand/10`
          : `${FR_TOUCH_LIST_BUTTON} border-zinc-200 bg-white hover:border-brand dark:border-zinc-700 dark:bg-zinc-900`
      }
      onClick={onSelect}
      disabled={disabled}
    >
      <div className="font-medium">{issue.issue_name_he}</div>
      <div className="text-zinc-500">
        {issue.issue_id}
        {issue.standard_ref ? ` · ${issue.standard_ref}` : ""}
      </div>
    </button>
  );
}
