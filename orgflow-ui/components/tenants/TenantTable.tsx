"use client";

import Button from "@/components/ui/Button";
import type { Tenant } from "@/lib/tenants/types";

type Props = {
  tenants: Tenant[];
  onChange: (tenants: Tenant[]) => void;
};

const inputClass =
  "h-9 w-full rounded-lg border border-zinc-200 bg-white px-2 text-sm outline-none focus:ring-2 focus:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-900";

export default function TenantTable({ tenants, onChange }: Props) {
  const update = (i: number, key: keyof Tenant, value: string) => {
    const next = [...tenants];
    next[i] = { ...next[i], [key]: value };
    onChange(next);
  };

  const remove = (i: number) => onChange(tenants.filter((_, idx) => idx !== i));

  const add = () =>
    onChange([
      ...tenants,
      {
        apartment: "",
        name: "",
        phone: "",
        email: "",
        building: "",
        entrance: "",
      },
    ]);

  const showBuilding = tenants.some((t) => t.building);
  const showEntrance = tenants.some((t) => t.entrance);

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
        <div>
          <h3 className="font-semibold">רשימת דיירים</h3>
          <p className="text-xs text-zinc-500">{tenants.length} רשומות - ניתן לערוך</p>
        </div>
        <Button variant="secondary" size="sm" type="button" onClick={add}>
          + הוסף דייר
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 text-xs uppercase text-zinc-500 dark:bg-zinc-900">
            <tr>
              <th className="px-3 py-3 text-right font-medium">דירה</th>
              {showBuilding && (
                <th className="px-3 py-3 text-right font-medium">בניין</th>
              )}
              {showEntrance && (
                <th className="px-3 py-3 text-right font-medium">כניסה</th>
              )}
              <th className="px-3 py-3 text-right font-medium">שם בעל הדירה</th>
              <th className="px-3 py-3 text-right font-medium">טלפון</th>
              <th className="px-3 py-3 text-right font-medium">מייל</th>
              <th className="w-12" />
            </tr>
          </thead>
          <tbody>
            {tenants.map((t, i) => (
              <tr
                key={i}
                className="border-t border-zinc-100 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900/50"
              >
                <td className="p-2">
                  <input
                    value={t.apartment}
                    onChange={(e) => update(i, "apartment", e.target.value)}
                    className={inputClass}
                  />
                </td>
                {showBuilding && (
                  <td className="p-2">
                    <input
                      value={t.building || ""}
                      onChange={(e) => update(i, "building", e.target.value)}
                      className={inputClass}
                    />
                  </td>
                )}
                {showEntrance && (
                  <td className="p-2">
                    <input
                      value={t.entrance || ""}
                      onChange={(e) => update(i, "entrance", e.target.value)}
                      className={inputClass}
                    />
                  </td>
                )}
                <td className="p-2">
                  <input
                    value={t.name}
                    onChange={(e) => update(i, "name", e.target.value)}
                    className={inputClass}
                  />
                </td>
                <td className="p-2">
                  <input
                    value={t.phone}
                    onChange={(e) => update(i, "phone", e.target.value)}
                    className={inputClass}
                    dir="ltr"
                  />
                </td>
                <td className="p-2">
                  <input
                    value={t.email}
                    onChange={(e) => update(i, "email", e.target.value)}
                    className={inputClass}
                    dir="ltr"
                  />
                </td>
                <td className="p-2 text-center">
                  <button
                    type="button"
                    onClick={() => remove(i)}
                    className="text-red-600 hover:text-red-700"
                    aria-label="מחק"
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
