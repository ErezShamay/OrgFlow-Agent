"use client";

import Link from "next/link";

import Button from "@/components/ui/Button";

type FieldReportsOfflineGuideProps = {
  expiresAt: string | null;
  catalogVersion?: string | null;
  importedInProgressCount?: number;
  onDismiss?: () => void;
  dismissible?: boolean;
};

export default function FieldReportsOfflineGuide({
  expiresAt,
  catalogVersion,
  importedInProgressCount = 0,
  onDismiss,
  dismissible = false,
}: FieldReportsOfflineGuideProps) {
  return (
    <div
      className="space-y-3 rounded-lg border border-sky-200 bg-sky-50 px-4 py-4 text-sm text-sky-950 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-100"
      role="status"
    >
      <p className="font-semibold">מדריך עבודה בשטח (אופליין)</p>
      <p className="text-sky-900 dark:text-sky-200">
        ההכנה שומרת קטלוג, פרויקטים ודוחות בעבודה במכשיר
        {expiresAt
          ? ` עד ${new Date(expiresAt).toLocaleString("he-IL")}`
          : ""}
        {catalogVersion ? ` · קטלוג ${catalogVersion}` : ""}.
        {importedInProgressCount > 0
          ? ` יובאו ${importedInProgressCount} דוחות מהמשרד.`
          : ""}
      </p>
      <ol className="list-decimal space-y-1.5 pr-5 text-sky-900 dark:text-sky-200">
        <li>
          <strong>לפני יציאה מהמשרד:</strong> לחץ «הכנה לא מקוון» (דורש רשת).
        </li>
        <li>
          <strong>דוח חדש:</strong> «דוח ביקור חדש» - נשמר במכשיר גם בלי רשת.
        </li>
        <li>
          <strong>דוח מהמשרד:</strong> פתח דוח «בעבודה» מהרשימה - ימשיך
          אופליין אחרי ההכנה.
        </li>
        <li>
          <strong>בשטח:</strong> ערוך כותרת, שורות ותמונות; השינויים נשמרים
          אוטומטית.
        </li>
        <li>
          <strong>סיום:</strong> «סיום דוח» + PDF במכשיר - גם ללא רשת.
        </li>
        <li>
          <strong>אחרי רשת:</strong> שליחה לליבה / סנכרון (בשלב הבא - כפתור
          העלאה).
        </li>
        <li>
          <strong>יציאה מהמערכת:</strong> לא ניתן להתנתק כשיש דוחות ממתינים
          לסנכרון באותו משתמש.
        </li>
      </ol>
      <p className="text-xs text-sky-800 dark:text-sky-300">
        <Link href="/field-reports" className="font-medium text-brand hover:underline">
          רשימת הדוחות
        </Link>
        {" · "}
        <Link
          href="/field-reports/new"
          className="font-medium text-brand hover:underline"
        >
          דוח חדש
        </Link>
      </p>
      {dismissible && onDismiss ? (
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={onDismiss}
        >
          הסתר מדריך
        </Button>
      ) : null}
    </div>
  );
}
