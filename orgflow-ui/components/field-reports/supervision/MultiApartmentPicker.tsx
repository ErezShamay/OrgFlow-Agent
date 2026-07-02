"use client";

import {
  startTransition,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { listProjectApartments } from "@/lib/apartments/api";
import { sortByApartmentNumber } from "@/lib/apartments/sort";
import type { ProjectApartment } from "@/lib/apartments/types";
import type { SupervisionVisitedApartment } from "@/lib/field-reports/schema/types";
import {
  apartmentSelectionToVisitedApartment,
  formatVisitedApartmentsSummaryHe,
} from "@/lib/field-reports/visited-apartments-summary";
import { FR_TOUCH_INPUT, FR_TOUCH_LIST_BUTTON } from "@/lib/field-reports/touch-input-class";

const APARTMENT_LIST_VISIBLE_COUNT = 5;
const APARTMENT_LIST_ROW_GAP_PX = 8;

type MultiApartmentPickerProps = {
  projectId: string;
  value: SupervisionVisitedApartment[];
  onChange: (value: SupervisionVisitedApartment[]) => void;
  canLoadFromApi: boolean;
  offlineApartments?: ProjectApartment[];
};

function apartmentKey(apartment: SupervisionVisitedApartment): string {
  return apartment.apartment_id?.trim() || `adhoc:${apartment.apartment_number}`;
}

function createAdHocApartment(
  apartmentNumber: string,
  ownerName?: string
): SupervisionVisitedApartment {
  return apartmentSelectionToVisitedApartment({
    apartmentId: crypto.randomUUID(),
    apartmentNumber: apartmentNumber.trim(),
    ownerName: ownerName?.trim() || null,
    adHocApartment: true,
  });
}

export default function MultiApartmentPicker({
  projectId,
  value,
  onChange,
  canLoadFromApi,
  offlineApartments = [],
}: MultiApartmentPickerProps) {
  const [apartments, setApartments] = useState<ProjectApartment[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [showAdHocForm, setShowAdHocForm] = useState(false);
  const [adHocNumber, setAdHocNumber] = useState("");
  const [adHocOwner, setAdHocOwner] = useState("");
  const [listMaxHeight, setListMaxHeight] = useState<number | undefined>();
  const sampleRowRef = useRef<HTMLButtonElement | null>(null);

  const sortedApartments = useMemo(
    () => sortByApartmentNumber(apartments),
    [apartments]
  );

  const selectedKeys = useMemo(
    () => new Set(value.map((apartment) => apartmentKey(apartment))),
    [value]
  );

  useLayoutEffect(() => {
    const sample = sampleRowRef.current;
    if (!sample || sortedApartments.length === 0) {
      setListMaxHeight(undefined);
      return;
    }

    const rowHeight = sample.offsetHeight;
    setListMaxHeight(
      APARTMENT_LIST_VISIBLE_COUNT * rowHeight
        + (APARTMENT_LIST_VISIBLE_COUNT - 1) * APARTMENT_LIST_ROW_GAP_PX
    );
  }, [sortedApartments.length, loading]);

  useEffect(() => {
    if (!projectId) {
      setApartments([]);
      return;
    }

    if (!canLoadFromApi) {
      setApartments(offlineApartments);
      setLoadError("");
      setLoading(false);
      return;
    }

    let cancelled = false;

    startTransition(() => {
      void (async () => {
        try {
          setLoading(true);
          setLoadError("");
          const items = await listProjectApartments(projectId);
          if (!cancelled) {
            setApartments(items);
          }
        } catch (err: unknown) {
          if (!cancelled) {
            setLoadError(
              err instanceof Error ? err.message : "טעינת דירות נכשלה"
            );
            setApartments(offlineApartments);
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      })();
    });

    return () => {
      cancelled = true;
    };
  }, [projectId, canLoadFromApi, offlineApartments]);

  function toggleApartment(apartment: ProjectApartment) {
    const next = apartmentSelectionToVisitedApartment({
      apartmentId: apartment.id,
      apartmentNumber: apartment.apartment_number,
      ownerName: apartment.owner_name || null,
      adHocApartment: false,
    });
    const key = apartmentKey(next);

    if (selectedKeys.has(key)) {
      onChange(value.filter((entry) => apartmentKey(entry) !== key));
      return;
    }

    onChange([...value, next]);
  }

  function submitAdHocApartment() {
    const number = adHocNumber.trim();
    if (!number) {
      return;
    }

    const next = createAdHocApartment(number, adHocOwner);
    const key = apartmentKey(next);
    if (!selectedKeys.has(key)) {
      onChange([...value, next]);
    }

    setAdHocNumber("");
    setAdHocOwner("");
    setShowAdHocForm(false);
  }

  const summary = formatVisitedApartmentsSummaryHe(value);

  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium">בחירת דירות לביקור אחד</legend>
      <p className="text-sm text-zinc-600 dark:text-zinc-300">
        בחר שתי דירות או יותר — ייווצר דוח אחד עם סיכום הביקור.
      </p>

      {loading ? (
        <p className="text-sm text-zinc-500">טוען דירות...</p>
      ) : null}

      {loadError ? (
        <p className="text-sm text-amber-700 dark:text-amber-300">{loadError}</p>
      ) : null}

      {!loading && apartments.length === 0 && canLoadFromApi ? (
        <p className="text-sm text-zinc-600">אין דירות רשומות בפרויקט.</p>
      ) : null}

      {!loading && apartments.length === 0 && !canLoadFromApi ? (
        <p className="text-sm text-zinc-600">
          אין דירות בחבילת ההכנה — הוסף דירה ידנית.
        </p>
      ) : null}

      {sortedApartments.length > 0 ? (
        <div
          className="space-y-2 overflow-y-auto overscroll-contain"
          style={listMaxHeight ? { maxHeight: listMaxHeight } : undefined}
        >
          {sortedApartments.map((apartment, index) => {
            const selection = apartmentSelectionToVisitedApartment({
              apartmentId: apartment.id,
              apartmentNumber: apartment.apartment_number,
              ownerName: apartment.owner_name || null,
              adHocApartment: false,
            });
            const selected = selectedKeys.has(apartmentKey(selection));

            return (
              <button
                key={apartment.id}
                ref={index === 0 ? sampleRowRef : undefined}
                type="button"
                className={`${FR_TOUCH_LIST_BUTTON} ${
                  selected
                    ? "border-brand bg-brand/5 text-brand dark:border-brand-light dark:text-brand-light"
                    : "border-zinc-200 bg-white hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950 dark:hover:bg-zinc-900"
                }`}
                aria-pressed={selected}
                onClick={() => toggleApartment(apartment)}
              >
                <span className="block font-medium">
                  {selected ? "✓ " : ""}
                  דירה {apartment.apartment_number}
                </span>
                {apartment.owner_name ? (
                  <span className="mt-0.5 block text-sm text-zinc-500 dark:text-zinc-400">
                    {apartment.owner_name}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}

      {showAdHocForm ? (
        <div className="space-y-3 rounded-xl border border-zinc-200 p-4 dark:border-zinc-700">
          <label className="block space-y-1 text-sm">
            <span className="font-medium">מספר דירה</span>
            <input
              type="text"
              className={FR_TOUCH_INPUT}
              value={adHocNumber}
              onChange={(event) => setAdHocNumber(event.target.value)}
              required
            />
          </label>
          <label className="block space-y-1 text-sm">
            <span className="font-medium">שם בעלים (אופציונלי)</span>
            <input
              type="text"
              className={FR_TOUCH_INPUT}
              value={adHocOwner}
              onChange={(event) => setAdHocOwner(event.target.value)}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={`${FR_TOUCH_LIST_BUTTON} border-brand bg-brand text-white hover:bg-brand-dark dark:bg-brand-light dark:text-brand-dark`}
              disabled={!adHocNumber.trim()}
              onClick={submitAdHocApartment}
            >
              הוסף לביקור
            </button>
            <button
              type="button"
              className={`${FR_TOUCH_LIST_BUTTON} border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-950`}
              onClick={() => setShowAdHocForm(false)}
            >
              ביטול
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          className={`${FR_TOUCH_LIST_BUTTON} border-dashed border-zinc-300 bg-zinc-50 text-zinc-700 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-200`}
          onClick={() => setShowAdHocForm(true)}
        >
          + הוסף דירה
        </button>
      )}

      {value.length > 0 ? (
        <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-900 dark:bg-sky-950/40 dark:text-sky-200">
          {summary}
        </p>
      ) : null}
    </fieldset>
  );
}
