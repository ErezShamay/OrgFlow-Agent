"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getDocumentDirection,
  translate,
  type Locale,
  type TranslationKey,
} from "@/lib/ui/i18n";

type I18nContextValue = {
  locale: Locale;
  direction: "rtl" | "ltr";
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
};

const I18nContext = createContext<I18nContextValue | null>(
  null
);

const STORAGE_KEY = "orgflow-locale";

export function I18nProvider({
  children,
  defaultLocale = "he",
}: {
  children: ReactNode;
  defaultLocale?: Locale;
}) {
  const [locale, setLocaleState] = useState<Locale>(
    defaultLocale
  );

  useEffect(() => {
    const stored = window.localStorage.getItem(
      STORAGE_KEY
    ) as Locale | null;

    if (stored === "he" || stored === "en") {
      setLocaleState(stored);
    }
  }, []);

  useEffect(() => {
    const direction = getDocumentDirection(locale);
    document.documentElement.lang = locale;
    document.documentElement.dir = direction;
    window.localStorage.setItem(STORAGE_KEY, locale);
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
  }, []);

  const value = useMemo(
    () => ({
      locale,
      direction: getDocumentDirection(locale),
      setLocale,
      t: (key: TranslationKey) => translate(locale, key),
    }),
    [locale, setLocale]
  );

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error(
      "useI18n must be used within I18nProvider"
    );
  }

  return context;
}
