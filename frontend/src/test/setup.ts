import "@testing-library/jest-dom/vitest";

class MemoryStorage implements Storage {
  private store = new Map<string, string>();

  get length() {
    return this.store.size;
  }

  clear() {
    this.store.clear();
  }

  getItem(key: string) {
    return this.store.get(key) ?? null;
  }

  key(index: number) {
    return Array.from(this.store.keys())[index] ?? null;
  }

  removeItem(key: string) {
    this.store.delete(key);
  }

  setItem(key: string, value: string) {
    this.store.set(key, value);
  }
}

function ensureStorage(name: "localStorage" | "sessionStorage") {
  const currentValue = window[name];
  if (!currentValue || typeof currentValue.getItem !== "function") {
    Object.defineProperty(window, name, {
      configurable: true,
      value: new MemoryStorage(),
    });
  }
}

ensureStorage("localStorage");
ensureStorage("sessionStorage");
