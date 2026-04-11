import { useCallback, useEffect, useState } from "react";

import type { HistoryEntry } from "../types/sentiment";

const STORAGE_KEY = "sentiment_history";
const HISTORY_EVENT = "sentiment-history-updated";
const MAX_ENTRIES = 50;

function readHistory(): HistoryEntry[] {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    return JSON.parse(raw) as HistoryEntry[];
  } catch {
    return [];
  }
}

function writeHistory(entries: HistoryEntry[]) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  window.dispatchEvent(new Event(HISTORY_EVENT));
}

export function useHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>(() => readHistory());

  useEffect(() => {
    const sync = () => setHistory(readHistory());
    window.addEventListener(HISTORY_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(HISTORY_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const addEntry = useCallback((entry: Omit<HistoryEntry, "id" | "timestamp">) => {
    const nextEntry: HistoryEntry = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      ...entry,
    };
    const nextHistory = [nextEntry, ...readHistory()].slice(0, MAX_ENTRIES);
    writeHistory(nextHistory);
    setHistory(nextHistory);
  }, []);

  const clearHistory = useCallback(() => {
    writeHistory([]);
    setHistory([]);
  }, []);

  const removeEntry = useCallback((id: string) => {
    const nextHistory = readHistory().filter((entry) => entry.id !== id);
    writeHistory(nextHistory);
    setHistory(nextHistory);
  }, []);

  return { history, addEntry, clearHistory, removeEntry };
}
