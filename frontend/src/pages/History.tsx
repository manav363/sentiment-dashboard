import { useNavigate } from "react-router-dom";

import Button from "../components/ui/Button";
import { useHistory } from "../hooks/useHistory";

const labelClasses = {
  positive: "bg-[rgba(34,197,94,0.15)] text-[var(--positive)]",
  neutral: "bg-[rgba(245,158,11,0.15)] text-[var(--neutral)]",
  negative: "bg-[rgba(239,68,68,0.15)] text-[var(--negative)]",
} as const;

const modeLabels = {
  text: "Text",
  url: "URL",
} as const;

function getDominantLabel(entry: ReturnType<typeof useHistory>["history"][number]) {
  if ("result" in entry.result) {
    return entry.result.result.label;
  }
  return entry.result.label;
}

export default function History() {
  const navigate = useNavigate();
  const { history, clearHistory, removeEntry } = useHistory();

  if (!history.length) {
    return (
      <section className="surface-card fade-in rounded-3xl p-10 text-center">
        <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-primary)] text-2xl">
          ◎
        </div>
        <h2 className="text-2xl font-semibold">No analyses yet</h2>
        <p className="mt-3 text-[var(--text-muted)]">
          Your saved sentiment analyses will appear here once you start exploring.
        </p>
        <Button className="mt-6" onClick={() => navigate("/")}>
          Start analyzing
        </Button>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent)]">History</p>
          <h2 className="mt-2 text-3xl font-semibold">Saved analyses</h2>
        </div>
        <Button
          variant="danger"
          onClick={() => {
            if (window.confirm("Clear all saved analyses?")) {
              clearHistory();
            }
          }}
        >
          Clear All
        </Button>
      </div>

      <div className="grid gap-4">
        {history.map((entry) => {
          const dominantLabel = getDominantLabel(entry);
          return (
            <article
              key={entry.id}
              className="surface-card fade-in flex flex-col gap-4 rounded-3xl p-5 md:flex-row md:items-center md:justify-between"
            >
              <button
                type="button"
                onClick={() =>
                  navigate("/results", {
                    state: { result: entry.result, mode: entry.mode, input: entry.input },
                  })
                }
                className="flex flex-1 items-center gap-4 text-left"
                aria-label={`View ${entry.mode} analysis: ${entry.input.slice(0, 60)}`}
              >
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--bg-primary)] text-sm font-semibold text-[var(--accent)]"
                  aria-hidden="true"
                >
                  {modeLabels[entry.mode]}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-base font-medium text-[var(--text-primary)]">
                    {entry.input}
                  </p>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">
                    {new Date(entry.timestamp).toLocaleString()}
                  </p>
                </div>
              </button>

              <div className="flex items-center gap-3">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                    labelClasses[dominantLabel as keyof typeof labelClasses] ?? labelClasses.neutral
                  }`}
                >
                  {dominantLabel}
                </span>
                <Button variant="secondary" size="sm" onClick={() => removeEntry(entry.id)}>
                  Remove
                </Button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
