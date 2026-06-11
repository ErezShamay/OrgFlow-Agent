"use client";

import { useRef, useState } from "react";

import Button from "@/components/ui/Button";
import { extractTenantsFromText } from "@/lib/tenants/extract";
import { asContactRows, mergeByOwnerName } from "@/lib/tenants/merge";
import {
  parseApartmentsExcel,
  parseContactsExcel,
  parseExcelToText,
} from "@/lib/tenants/parsers";
import type { Tenant } from "@/lib/tenants/types";

type Slot = "apartments" | "contacts";

type ParsedFile = {
  fileName: string;
  tenants: Tenant[];
};

type Props = {
  onTenants: (tenants: Tenant[]) => void;
};

export default function TenantMergeUploader({ onTenants }: Props) {
  const [fileA, setFileA] = useState<ParsedFile | null>(null);
  const [fileB, setFileB] = useState<ParsedFile | null>(null);
  const [loadingSlot, setLoadingSlot] = useState<Slot | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputARef = useRef<HTMLInputElement>(null);
  const inputBRef = useRef<HTMLInputElement>(null);

  async function handleFile(slot: Slot, file: File) {
    setLoadingSlot(slot);
    setError(null);
    setMessage("קורא את הקובץ...");
    try {
      const name = file.name.toLowerCase();
      const isExcel =
        name.endsWith(".xlsx") ||
        name.endsWith(".xls") ||
        name.endsWith(".csv");
      if (!isExcel) {
        setError("נא להעלות קובץ Excel/CSV");
        return;
      }

      setMessage("מנתח גיליון Excel...");
      const direct =
        slot === "apartments"
          ? await parseApartmentsExcel(file)
          : await parseContactsExcel(file);
      if (direct && direct.length > 0) {
        const parsed: ParsedFile = {
          fileName: file.name,
          tenants: slot === "contacts" ? asContactRows(direct) : direct,
        };
        if (slot === "apartments") setFileA(parsed);
        else setFileB(parsed);
        setMessage(`נמצאו ${direct.length} שורות ב-${file.name}`);
        return;
      }

      setMessage("מחלץ נתונים בעזרת AI...");
      const text = await parseExcelToText(file);
      const result = await extractTenantsFromText(text);
      if (result.error) {
        setError(result.error);
        return;
      }
      if (!result.tenants.length) {
        setError("לא נמצאו דיירים בקובץ");
        return;
      }
      const parsed: ParsedFile = {
        fileName: file.name,
        tenants:
          slot === "contacts"
            ? asContactRows(result.tenants)
            : result.tenants,
      };
      if (slot === "apartments") setFileA(parsed);
      else setFileB(parsed);
      setMessage(`נמצאו ${result.tenants.length} שורות ב-${file.name}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "שגיאה בעיבוד הקובץ");
    } finally {
      setLoadingSlot(null);
      setTimeout(() => setMessage(null), 4000);
    }
  }

  function runMerge() {
    if (!fileA || !fileB) {
      setError("יש להעלות את שני הקבצים לפני האיחוד");
      return;
    }
    const report = mergeByOwnerName(fileA.tenants, fileB.tenants);
    onTenants(report.merged);
    setMessage(
      `אוחדו ${report.merged.length} שורות (${report.matched} התאמות, ${report.unmatched} בעלי דירות ללא איש קשר)`,
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-zinc-500">
        קובץ א׳ - דירות (מספר דירה, בניין, כניסה, שם בעלים). קובץ ב׳ - אנשי קשר
        (שם, טלפון, מייל). האיחוד מתבצע לפי שם בעל הדירה.
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <SlotCard
          title="קובץ דירות (א׳)"
          file={fileA}
          loading={loadingSlot === "apartments"}
          inputRef={inputARef}
          onPick={(f) => handleFile("apartments", f)}
        />
        <SlotCard
          title="קובץ אנשי קשר (ב׳)"
          file={fileB}
          loading={loadingSlot === "contacts"}
          inputRef={inputBRef}
          onPick={(f) => handleFile("contacts", f)}
        />
      </div>

      <Button
        type="button"
        disabled={!fileA || !fileB || loadingSlot !== null}
        onClick={runMerge}
      >
        אחד קבצים
      </Button>

      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}

function SlotCard({
  title,
  file,
  loading,
  inputRef,
  onPick,
}: {
  title: string;
  file: ParsedFile | null;
  loading: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onPick: (file: File) => void;
}) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <h4 className="font-medium">{title}</h4>
      {file ? (
        <p className="mt-2 text-sm text-zinc-600">
          {file.fileName} - {file.tenants.length} שורות
        </p>
      ) : (
        <p className="mt-2 text-sm text-zinc-400">טרם הועלה קובץ</p>
      )}
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onPick(f);
        }}
      />
      <Button
        variant="secondary"
        size="sm"
        type="button"
        className="mt-4"
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? "מעבד..." : file ? "החלף קובץ" : "העלה קובץ"}
      </Button>
    </div>
  );
}
