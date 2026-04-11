import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import ConfidenceBar from "../components/results/ConfidenceBar";
import SentimentGauge from "../components/results/SentimentGauge";
import Button from "../components/ui/Button";
import { useHistory } from "../hooks/useHistory";
import type {
  ResultsNavigationState,
  URLAnalysisResult,
} from "../types/sentiment";

const LATEST_RESULT_STORAGE_KEY = "sentiscope_latest_result";

function isURLResult(
  result: ResultsNavigationState["result"],
): result is URLAnalysisResult {
  return "title" in result && "chunk_count" in result;
}

function readStoredResultsState(): ResultsNavigationState | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.sessionStorage.getItem(LATEST_RESULT_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as ResultsNavigationState;
  } catch {
    return null;
  }
}

function persistResultsState(state: ResultsNavigationState) {
  window.sessionStorage.setItem(LATEST_RESULT_STORAGE_KEY, JSON.stringify(state));
}

export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { addEntry } = useHistory();
  const rawState = location.state;
  const routedState: ResultsNavigationState | null =
    rawState &&
    typeof rawState === "object" &&
    "result" in rawState &&
    "mode" in rawState
      ? (rawState as ResultsNavigationState)
      : null;
  const [restoredState, setRestoredState] = useState<ResultsNavigationState | null>(
    () => routedState ?? readStoredResultsState(),
  );
  const state = routedState ?? restoredState;
  const [saved, setSaved] = useState(Boolean(state));
  const hasAutoSaved = useRef(false);

  useEffect(() => {
    if (!routedState) {
      return;
    }

    persistResultsState(routedState);
    setRestoredState(routedState);
  }, [routedState]);

  useEffect(() => {
    if (routedState && !hasAutoSaved.current) {
      hasAutoSaved.current = true;
      addEntry({
        mode: routedState.mode,
        input: routedState.input,
        result: routedState.result,
      });
      setSaved(true);
    }
  }, [routedState, addEntry]);

  if (!state) {
    return (
      <section className="surface-card fade-in rounded-3xl p-10 text-center">
        <h2 className="text-2xl font-semibold">No result loaded</h2>
        <p className="mt-3 text-[var(--text-muted)]">
          Go analyze something and your result will appear here.
        </p>
        <Button className="mt-6" onClick={() => navigate("/")}>
          Go analyze something
        </Button>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent)]">Results</p>
          <h2 className="text-3xl font-semibold">
            {isURLResult(state.result) ? state.result.title : "Direct text analysis"}
          </h2>
          <p className="text-sm text-[var(--text-muted)]">
            Mode: <span className="capitalize text-[var(--text-primary)]">{state.mode}</span>
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => navigate("/")}>
            Analyze Again
          </Button>
          <Button variant="secondary" disabled>
            {saved ? "Saved to History" : "Saving..."}
          </Button>
        </div>
      </div>

      {isURLResult(state.result) ? (
        <div className="space-y-4">
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] px-5 py-4">
            <p className="text-sm text-[var(--text-muted)]">Article title</p>
            <h3 className="mt-1 text-xl font-semibold">{state.result.title}</h3>
            <div className="mt-3 inline-flex rounded-full bg-[var(--accent-dim)] px-3 py-1 text-xs font-medium text-[var(--accent)]">
              {state.result.chunk_count} chunks analyzed
            </div>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <SentimentGauge result={state.result.result} />
            <ConfidenceBar breakdown={state.result.result.breakdown} />
          </div>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <SentimentGauge result={state.result} />
          <ConfidenceBar breakdown={state.result.breakdown} />
        </div>
      )}
    </section>
  );
}
