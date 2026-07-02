import { vi } from "vitest";

export function createStorageMock() {
  const store = new Map<string, string>();

  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
  };
}

/** Stubs browser storage without breaking fake-indexeddb or Capacitor globals. */
export function stubBrowserStorage() {
  const localStorage = createStorageMock();
  const sessionStorage = createStorageMock();

  vi.stubGlobal("localStorage", localStorage);
  vi.stubGlobal("sessionStorage", sessionStorage);

  const baseWindow =
    typeof globalThis.window === "object" && globalThis.window !== null
      ? (globalThis.window as unknown as Record<string, unknown>)
      : {
          addEventListener: () => undefined,
          removeEventListener: () => undefined,
          dispatchEvent: () => true,
        };

  vi.stubGlobal("window", {
    ...baseWindow,
    localStorage,
    sessionStorage,
  });

  return { localStorage, sessionStorage };
}
