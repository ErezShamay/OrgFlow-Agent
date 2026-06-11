"use client";

import { useEffect, useRef, useState } from "react";

import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import {
  contractorStatusFilterAllLabel,
  isContractorIssuesView,
} from "@/lib/quality-issues/contractor-issues-view";
import {
  availableStatusFilterOptions,
  createEmptyIssuesFilterState,
  hasActiveIssuesFilters,
  type IssuesFilterState,
} from "@/lib/quality-issues/filters";
import {
  QUALITY_ISSUE_SEVERITIES,
  QUALITY_ISSUE_SEVERITY_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  type QualityIssueSeverity,
  type QualityIssueStatus,
} from "@/lib/quality-issues/types";

const selectClass =
  "of-input of-focus-ring w-full px-4 py-3 text-sm";

export type IssuesFiltersProps = {
  value: IssuesFilterState;
  onChange: (value: IssuesFilterState) => void;
  role?: string | null;
  className?: string;
};

export default function IssuesFilters({
  value,
  onChange,
  role,
  className = "",
}: IssuesFiltersProps) {
  const [tradeDraft, setTradeDraft] = useState(value.trade);
  const valueRef = useRef(value);
  const statusOptions = availableStatusFilterOptions(role);
  const contractorView = isContractorIssuesView(role);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    setTradeDraft(value.trade);
  }, [value.trade]);

  const debouncedTradeChange = useDebouncedCallback((trade: string) => {
    onChange({
      ...valueRef.current,
      trade,
    });
  }, 400);

  function updateStatus(status: QualityIssueStatus | "") {
    onChange({
      ...value,
      status,
    });
  }

  function updateSeverity(severity: QualityIssueSeverity | "") {
    onChange({
      ...value,
      severity,
    });
  }

  function updateTrade(trade: string) {
    setTradeDraft(trade);
    debouncedTradeChange(trade);
  }

  function clearFilters() {
    const empty = createEmptyIssuesFilterState();
    setTradeDraft("");
    onChange(empty);
  }

  return (
    <div
      className={`
        of-card
        of-card-p6
        grid
        gap-4
        md:grid-cols-4
        ${className}
      `}
    >
      <label className="block md:col-span-1">
        <span className="mb-2 block text-sm font-medium text-zinc-600 dark:text-zinc-400">
          סטטוס
        </span>
        <select
          value={value.status}
          onChange={(event) =>
            updateStatus(event.target.value as QualityIssueStatus | "")
          }
          className={selectClass}
          aria-label="סינון לפי סטטוס"
        >
          <option value="">
            {contractorView
              ? contractorStatusFilterAllLabel()
              : "כל הסטטוסים"}
          </option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {QUALITY_ISSUE_STATUS_LABELS_HE[status]}
            </option>
          ))}
        </select>
      </label>

      <label className="block md:col-span-1">
        <span className="mb-2 block text-sm font-medium text-zinc-600 dark:text-zinc-400">
          חומרה
        </span>
        <select
          value={value.severity}
          onChange={(event) =>
            updateSeverity(event.target.value as QualityIssueSeverity | "")
          }
          className={selectClass}
          aria-label="סינון לפי חומרה"
        >
          <option value="">כל רמות החומרה</option>
          {QUALITY_ISSUE_SEVERITIES.map((severity) => (
            <option key={severity} value={severity}>
              {QUALITY_ISSUE_SEVERITY_LABELS_HE[severity]}
            </option>
          ))}
        </select>
      </label>

      <label className="block md:col-span-1">
        <span className="mb-2 block text-sm font-medium text-zinc-600 dark:text-zinc-400">
          מלאכה
        </span>
        <input
          type="search"
          value={tradeDraft}
          onChange={(event) => updateTrade(event.target.value)}
          placeholder="למשל: אינסטלציה"
          className={selectClass}
          aria-label="סינון לפי מלאכה"
        />
      </label>

      <div className="flex items-end md:col-span-1">
        <button
          type="button"
          onClick={clearFilters}
          disabled={!hasActiveIssuesFilters(value)}
          className="
            w-full
            rounded-2xl
            border
            border-zinc-300
            px-4
            py-3
            text-sm
            font-semibold
            transition
            enabled:hover:bg-zinc-100
            disabled:cursor-not-allowed
            disabled:opacity-40
            dark:border-zinc-700
            enabled:dark:hover:bg-zinc-800
          "
        >
          נקה סינון
        </button>
      </div>
    </div>
  );
}
