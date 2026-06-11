"use client";

import Button from "@/components/ui/Button";
import {
  constructionProgressTitleHe,
  defaultConstructionProgressRows,
  PROGRESS_STATUS_SUGGESTIONS,
  type ConstructionProgressRow,
} from "@/lib/field-reports/construction-progress";

type ReportConstructionProgressSectionProps = {
  visitType: string;
  rows: ConstructionProgressRow[];
  disabled: boolean;
  onChange: (rows: ConstructionProgressRow[]) => void;
};

export default function ReportConstructionProgressSection({
  visitType,
  rows,
  disabled,
  onChange,
}: ReportConstructionProgressSectionProps) {
  const title = constructionProgressTitleHe(visitType);
  const tableRows = rows.length ? rows : [{ description: "", status: "", completion_date: "" }];

  function updateRow(
    index: number,
    field: keyof ConstructionProgressRow,
    value: string
  ) {
    const next = [...tableRows];
    next[index] = { ...next[index], [field]: value };
    onChange(next);
  }

  function addRow() {
    onChange([
      ...tableRows,
      { description: "", status: "", completion_date: "" },
    ]);
  }

  function removeRow(index: number) {
    const next = tableRows.filter((_, rowIndex) => rowIndex !== index);
    onChange(
      next.length
        ? next
        : [{ description: "", status: "", completion_date: "" }]
    );
  }

  function restoreDefaults() {
    onChange(defaultConstructionProgressRows(visitType));
  }

  return (
    <section className="space-y-4 rounded-xl border border-zinc-200 p-4">
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-zinc-500">
          טבלת התקדמות ל-PDF - תיאור עבודה, סטטוס ותאריך. ניתן למלא בשטח או
          במשרד.
          {visitType === "FINISHING_APARTMENTS" ? (
            <span className="mt-1 block text-amber-800 dark:text-amber-200">
              מטריצת דירות מלאה (בעלים / חשמל / אינסטלציה לפי דירה) - בשלב 6.1.
            </span>
          ) : null}
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-right">
              <th className="px-2 py-2 font-medium">תיאור עבודה</th>
              <th className="w-36 px-2 py-2 font-medium">סטטוס</th>
              <th className="w-40 px-2 py-2 font-medium">
                תאריך ביצוע / סיום
              </th>
              {disabled ? null : <th className="w-16 px-2 py-2" />}
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row, index) => (
              <tr
                key={`progress-${index}`}
                className="border-b border-zinc-100 align-top"
              >
                <td className="px-2 py-2">
                  <input
                    className="of-input w-full"
                    value={row.description}
                    disabled={disabled}
                    placeholder="למשל: יציקת רצפת קומה 3"
                    onChange={(event) =>
                      updateRow(index, "description", event.target.value)
                    }
                  />
                </td>
                <td className="px-2 py-2">
                  <input
                    className="of-input w-full"
                    list="field-report-progress-status"
                    value={row.status}
                    disabled={disabled}
                    placeholder="בוצע / בתהליך"
                    onChange={(event) =>
                      updateRow(index, "status", event.target.value)
                    }
                  />
                </td>
                <td className="px-2 py-2">
                  <input
                    className="of-input w-full"
                    value={row.completion_date}
                    disabled={disabled}
                    placeholder="01/06/26"
                    onChange={(event) =>
                      updateRow(
                        index,
                        "completion_date",
                        event.target.value
                      )
                    }
                  />
                </td>
                {disabled ? null : (
                  <td className="px-2 py-2">
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={
                        tableRows.length === 1
                        && !row.description.trim()
                        && !row.status.trim()
                        && !row.completion_date.trim()
                      }
                      onClick={() => removeRow(index)}
                    >
                      הסר
                    </Button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <datalist id="field-report-progress-status">
        {PROGRESS_STATUS_SUGGESTIONS.map((status) => (
          <option key={status} value={status} />
        ))}
      </datalist>

      {disabled ? null : (
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={addRow}>
            הוסף שורה
          </Button>
          <Button type="button" variant="secondary" onClick={restoreDefaults}>
            שחזר תבנית ברירת מחדל
          </Button>
        </div>
      )}
    </section>
  );
}
