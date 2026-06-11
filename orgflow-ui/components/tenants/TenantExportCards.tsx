"use client";

import Button from "@/components/ui/Button";
import {
  buildEmailContactsCsv,
  buildPhoneContactsVcf,
  buildZohoApartmentsCsv,
  buildZohoContactsCsv,
  downloadCsv,
  downloadOutlookCsv,
  downloadVcf,
} from "@/lib/tenants/exports";
import type { Tenant } from "@/lib/tenants/types";

type Props = { tenants: Tenant[]; projectAddress: string };

const cards = [
  {
    key: "phone",
    title: "אנשי קשר לטלפון (VCF)",
    desc: "שם דייר + דירה + כתובת פרויקט - מוכן לייבוא לטלפון",
    file: "contacts-phone.vcf",
    run: (tenants: Tenant[], projectAddress: string) =>
      downloadVcf(buildPhoneContactsVcf(tenants, projectAddress), "contacts-phone.vcf"),
  },
  {
    key: "email",
    title: "אנשי קשר למייל",
    desc: "שם דייר + מס׳ דירה + כתובת מייל",
    file: "contacts-email.csv",
    run: (tenants: Tenant[], projectAddress: string) => {
      void projectAddress;
      downloadOutlookCsv(
        buildEmailContactsCsv(tenants),
        "contacts-email.csv",
      );
    },
  },
  {
    key: "zoho-apt",
    title: "ייבוא דירות לזוהו",
    desc: "פרטי הדייר והדירה + שם פרויקט",
    file: "zoho-apartments.csv",
    run: (tenants: Tenant[], projectAddress: string) =>
      downloadCsv(buildZohoApartmentsCsv(tenants, projectAddress), "zoho-apartments.csv"),
  },
  {
    key: "zoho-contacts",
    title: "ייבוא אנשי קשר לזוהו",
    desc: "פורמט מלא עם שם פרטי/משפחה, נייד, דוא״ל וכתובת הדירה",
    file: "zoho-contacts.csv",
    run: (tenants: Tenant[], projectAddress: string) =>
      downloadCsv(buildZohoContactsCsv(tenants, projectAddress), "zoho-contacts.csv"),
  },
] as const;

export default function TenantExportCards({
  tenants,
  projectAddress,
}: Props) {
  const downloadAll = () => {
    cards.forEach((c) => c.run(tenants, projectAddress));
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">הפקת קבצים (4 סוגים)</h3>
        <Button size="sm" type="button" onClick={downloadAll}>
          הורד הכל
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {cards.map((c) => (
          <div
            key={c.key}
            className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
          >
            <h4 className="font-semibold">{c.title}</h4>
            <p className="mt-1 text-sm text-zinc-500">{c.desc}</p>
            <Button
              variant="secondary"
              size="sm"
              type="button"
              className="mt-4"
              onClick={() => c.run(tenants, projectAddress)}
            >
              הורד {c.file}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
