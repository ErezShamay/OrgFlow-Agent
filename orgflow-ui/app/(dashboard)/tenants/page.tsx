"use client";

import { useState } from "react";

import TenantExportCards from "@/components/tenants/TenantExportCards";
import TenantFileUploader from "@/components/tenants/TenantFileUploader";
import TenantMergeUploader from "@/components/tenants/TenantMergeUploader";
import TenantTable from "@/components/tenants/TenantTable";
import type { Tenant } from "@/lib/tenants/types";

type UploadMode = "single" | "merge";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [projectAddress, setProjectAddress] = useState("פינלס 9 תל אביב");
  const [mode, setMode] = useState<UploadMode>("single");

  const withPhone = tenants.filter((t) => t.phone).length;
  const withEmail = tenants.filter((t) => t.email).length;

  return (
    <div className="of-dashboard-page of-container mx-auto max-w-5xl space-y-10">
      <header>
        <h1 className="of-page-title text-2xl md:text-3xl">מנהל דיירים</h1>
        <p className="of-page-desc max-w-2xl text-sm">
          העלה קובץ Excel של רשימת דיירים — המערכת תחלץ את הנתונים, תאפשר עריכה,
          ותפיק 4 קבצי ייבוא: טלפון (VCF), מייל (CSV), דירות לזוהו, אנשי קשר
          לזוהו.
        </p>
      </header>

      <section>
        <SectionTitle step="1" title="העלאת קובץ" />
        <div className="of-card of-card-p6 mb-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setMode("single")}
            className={`rounded-xl px-3 py-2 text-sm font-medium transition ${
              mode === "single"
                ? "bg-gradient-to-l from-blue-600 to-violet-600 text-white shadow-md"
                : "text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            }`}
          >
            קובץ אחד
          </button>
          <button
            type="button"
            onClick={() => setMode("merge")}
            className={`rounded-xl px-3 py-2 text-sm font-medium transition ${
              mode === "merge"
                ? "bg-gradient-to-l from-blue-600 to-violet-600 text-white shadow-md"
                : "text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            }`}
          >
            איחוד שני קבצים
          </button>
        </div>
        {mode === "single" ? (
          <TenantFileUploader onTenants={setTenants} />
        ) : (
          <TenantMergeUploader onTenants={setTenants} />
        )}
      </section>

      {tenants.length > 0 && (
        <>
          <section className="of-card of-card-p6 border-emerald-500/30 bg-emerald-500/5">
            <h3 className="font-semibold">החילוץ הושלם</h3>
            <p className="mt-1 text-sm text-zinc-500">
              {tenants.length} דיירים · {withPhone} עם טלפון · {withEmail} עם
              מייל
            </p>
          </section>

          <section>
            <SectionTitle step="2" title="עריכה ואישור" />
            <TenantTable tenants={tenants} onChange={setTenants} />
          </section>

          <section>
            <SectionTitle step="3" title="כתובת הפרויקט" />
            <div className="of-card of-card-p6">
              <label className="mb-2 block text-sm font-medium">
                כתובת הפרויקט (תופיע בכל איש קשר ב-VCF ובייצוא לזוהו)
              </label>
              <input
                type="text"
                value={projectAddress}
                onChange={(e) => setProjectAddress(e.target.value)}
                placeholder="לדוגמה: פינלס 9 תל אביב"
                className="of-input of-focus-ring px-3 py-2 text-sm"
              />
            </div>
          </section>

          <section>
            <SectionTitle step="4" title="הפקת הקבצים" />
            <TenantExportCards
              tenants={tenants}
              projectAddress={projectAddress}
            />
          </section>
        </>
      )}
    </div>
  );
}

function SectionTitle({ step, title }: { step: string; title: string }) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 text-sm font-bold text-white">
        {step}
      </div>
      <h2 className="text-xl font-semibold">{title}</h2>
    </div>
  );
}
