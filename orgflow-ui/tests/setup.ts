import "fake-indexeddb/auto";

function createStorageMock() {
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

if (typeof globalThis.sessionStorage === "undefined") {
  globalThis.sessionStorage = createStorageMock() as Storage;
}

if (typeof globalThis.window === "object" && globalThis.window !== null) {
  const win = globalThis.window as typeof globalThis.window & {
    addEventListener?: typeof window.addEventListener;
    removeEventListener?: typeof window.removeEventListener;
    dispatchEvent?: typeof window.dispatchEvent;
  };

  if (typeof win.addEventListener !== "function") {
    win.addEventListener = () => undefined;
  }
  if (typeof win.removeEventListener !== "function") {
    win.removeEventListener = () => undefined;
  }
  if (typeof win.dispatchEvent !== "function") {
    win.dispatchEvent = () => true;
  }
}
