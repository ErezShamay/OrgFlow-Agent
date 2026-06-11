"use client";

import Link from "next/link";

import ReportBulkUploadPanel from "@/components/reports/ReportBulkUploadPanel";
import Button from "@/components/ui/Button";
import LoadingState from "@/components/ui/LoadingState";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";

export default function FieldReportsUploadPage() {
  const { isEnabled, loading, error, reload } = useFieldReportModule();

  if (loading) {
    return (
      <div className="of-container mx-auto max-w-3xl p-8">
        <LoadingState message="טוען..." variant="spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="of-container mx-auto max-w-3xl space-y-4 p-8">
        <p className="text-sm text-red-600">{error}</p>
        <Button variant="secondary" onClick={() => void reload()}>
          נסה שוב
        </Button>
      </div>
    );
  }

  if (!isEnabled) {
    return (
      <div className="of-container mx-auto max-w-3xl space-y-4 p-8">
        <h1 className="of-page-title text-2xl">העלאת מסמכים</h1>
        <p className="of-page-desc text-sm">
          מודול דוחות שטח אינו מופעל עבור הארגון הנוכחי. פנה למנהל המערכת
          להפעלה.
        </p>
        <Link href="/field-reports" className="text-sm text-brand hover:underline">
          חזרה לדוחות שטח
        </Link>
      </div>
    );
  }

  return (
    <main className="of-dashboard-page">
      <div className="of-container mx-auto max-w-3xl">
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="of-page-title">העלאת מסמכים</h1>
            <p className="of-page-desc mt-4">
              העלאת דוחות לצורך ניתוח AI תפעולי - ניתן לבחור מספר קבצים בבת אחת
              עם מעקב התקדמות לכל קובץ ולכל ההעלאה
            </p>
          </div>
          <Link
            href="/field-reports"
            className="text-sm text-brand hover:underline"
          >
            חזרה לדוחות שטח
          </Link>
        </div>

        <ReportBulkUploadPanel fileInputId="field-reports-upload-file" />
      </div>
    </main>
  );
}
