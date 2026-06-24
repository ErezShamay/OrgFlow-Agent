"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import Button from "@/components/ui/Button";
import { updateProjectApartment } from "@/lib/apartments/api";
import { sortByApartmentNumber } from "@/lib/apartments/sort";
import type { ProjectApartment } from "@/lib/apartments/types";
import { validateOptionalEmail } from "@/lib/validation/email";

const INVITE_STATUS_LABELS: Record<string, string> = {
  none: "לא הוזמן",
  pending: "ממתין להפעלה",
  active: "פעיל",
};

const inputClass =
  "h-9 w-full min-w-0 rounded-lg border border-zinc-200 bg-white px-2 text-sm outline-none focus:ring-2 focus:ring-brand/30 dark:border-zinc-700 dark:bg-zinc-900";

type ApartmentEditDraft = {
  apartment_number: string;
  owner_name: string;
  phone: string;
  email: string;
};

type ProjectApartmentsTableProps = {
  projectId: string;
  apartments: ProjectApartment[];
  onApartmentsChange: (apartments: ProjectApartment[]) => void;
};

function draftFromApartment(apartment: ProjectApartment): ApartmentEditDraft {
  return {
    apartment_number: apartment.apartment_number,
    owner_name: apartment.owner_name,
    phone: apartment.phone || "",
    email: apartment.email || "",
  };
}

export default function ProjectApartmentsTable({
  projectId,
  apartments,
  onApartmentsChange,
}: ProjectApartmentsTableProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<ApartmentEditDraft | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  const sortedApartments = useMemo(
    () => sortByApartmentNumber(apartments),
    [apartments]
  );

  const startEdit = (apartment: ProjectApartment) => {
    setEditingId(apartment.id);
    setDraft(draftFromApartment(apartment));
    setRowError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setDraft(null);
    setRowError(null);
  };

  const updateDraft = (key: keyof ApartmentEditDraft, value: string) => {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
  };

  const saveEdit = async (apartmentId: string) => {
    if (!draft) return;

    const apartmentNumber = draft.apartment_number.trim();
    const ownerName = draft.owner_name.trim();
    if (!apartmentNumber || !ownerName) {
      setRowError("מספר דירה ושם בעל הדירה הם שדות חובה");
      return;
    }

    const emailError = validateOptionalEmail(draft.email);
    if (emailError) {
      setRowError(emailError);
      return;
    }

    setSavingId(apartmentId);
    setRowError(null);
    try {
      const updated = await updateProjectApartment(projectId, apartmentId, {
        apartment_number: apartmentNumber,
        owner_name: ownerName,
        phone: draft.phone.trim() || null,
        email: draft.email.trim() || null,
      });
      onApartmentsChange(
        sortByApartmentNumber(
          apartments.map((apartment) =>
            apartment.id === apartmentId ? updated : apartment
          )
        )
      );
      cancelEdit();
    } catch (saveError) {
      setRowError(
        saveError instanceof Error
          ? saveError.message
          : "שגיאה בעדכון פרטי הדירה"
      );
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="of-card of-card-p6 max-h-[70vh] overflow-y-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-[var(--of-color-surface)]">
          <tr className="border-b text-right">
            <th className="px-3 py-2 font-medium">דירה</th>
            <th className="px-3 py-2 font-medium">בעל דירה</th>
            <th className="px-3 py-2 font-medium">טלפון</th>
            <th className="px-3 py-2 font-medium">מייל</th>
            <th className="px-3 py-2 font-medium">חשבון</th>
            <th className="px-3 py-2 font-medium">פעולות</th>
          </tr>
        </thead>
        <tbody>
          {sortedApartments.map((apartment) => {
            const isEditing = editingId === apartment.id;
            const isSaving = savingId === apartment.id;

            return (
              <tr
                key={apartment.id}
                className="border-b border-zinc-200/60 last:border-0 dark:border-zinc-700/60"
              >
                <td className="px-3 py-3">
                  {isEditing ? (
                    <input
                      value={draft?.apartment_number ?? ""}
                      onChange={(event) =>
                        updateDraft("apartment_number", event.target.value)
                      }
                      className={inputClass}
                      dir="ltr"
                      disabled={isSaving}
                    />
                  ) : (
                    <Link
                      href={`/projects/${projectId}/apartments/${apartment.id}`}
                      className="font-semibold text-brand hover:underline"
                    >
                      {apartment.apartment_number}
                    </Link>
                  )}
                </td>
                <td className="px-3 py-3">
                  {isEditing ? (
                    <input
                      value={draft?.owner_name ?? ""}
                      onChange={(event) =>
                        updateDraft("owner_name", event.target.value)
                      }
                      className={inputClass}
                      disabled={isSaving}
                    />
                  ) : (
                    apartment.owner_name
                  )}
                </td>
                <td className="px-3 py-3">
                  {isEditing ? (
                    <input
                      value={draft?.phone ?? ""}
                      onChange={(event) =>
                        updateDraft("phone", event.target.value)
                      }
                      className={inputClass}
                      dir="ltr"
                      disabled={isSaving}
                    />
                  ) : (
                    apartment.phone || "—"
                  )}
                </td>
                <td className="px-3 py-3">
                  {isEditing ? (
                    <input
                      value={draft?.email ?? ""}
                      onChange={(event) =>
                        updateDraft("email", event.target.value)
                      }
                      className={inputClass}
                      dir="ltr"
                      disabled={isSaving}
                    />
                  ) : (
                    apartment.email || "—"
                  )}
                </td>
                <td className="px-3 py-3">
                  {INVITE_STATUS_LABELS[apartment.invite_status] ||
                    apartment.invite_status}
                </td>
                <td className="px-3 py-3">
                  {isEditing ? (
                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        size="sm"
                        onClick={() => void saveEdit(apartment.id)}
                        disabled={isSaving}
                      >
                        {isSaving ? "שומר..." : "שמירה"}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={cancelEdit}
                        disabled={isSaving}
                      >
                        ביטול
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => startEdit(apartment)}
                      disabled={editingId !== null}
                    >
                      עריכה
                    </Button>
                  )}
                  {isEditing && rowError ? (
                    <p className="mt-2 text-xs text-red-600">{rowError}</p>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
