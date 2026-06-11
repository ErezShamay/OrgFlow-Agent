"use client";

import { CONTRACTOR_VISIBLE_STATUSES } from "@/lib/quality-issues/contractor-issues-view";
import {
  QUALITY_ISSUE_STATUS_LABELS_HE,
} from "@/lib/quality-issues/types";

const VISIBLE_STATUS_LABELS = CONTRACTOR_VISIBLE_STATUSES.map(
  (status) => QUALITY_ISSUE_STATUS_LABELS_HE[status]
).join(" · ");

export default function ContractorIssuesBanner() {
  return (
    <div
      className="
        of-card
        of-card-p6
        border-amber-200/80
        bg-amber-50/80
        text-sm
        text-amber-950
        dark:border-amber-900/60
        dark:bg-amber-950/30
        dark:text-amber-100
      "
      role="status"
    >
      <p className="font-semibold">תצוגת קבלן</p>
      <p className="mt-1 leading-relaxed">
        מוצגים רק ליקויים בסטטוס {VISIBLE_STATUS_LABELS}. ליקויים שנסגרו,
        ממתינים לאימות מפקח, או שחזרו - אינם זמינים בתצוגה זו.
      </p>
    </div>
  );
}
