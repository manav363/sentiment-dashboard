import { useEffect, useState } from "react";

import type { ScoreBreakdown } from "../../types/sentiment";

type ConfidenceBarProps = {
  breakdown: ScoreBreakdown[];
};

const colors: Record<string, string> = {
  positive: "var(--positive)",
  neutral: "var(--neutral)",
  negative: "var(--negative)",
};

export default function ConfidenceBar({ breakdown }: ConfidenceBarProps) {
  const [animated, setAnimated] = useState(false);
  const dominant = breakdown.reduce((best, current) => (current.score > best.score ? current : best), breakdown[0]);

  // Reset animation when breakdown data changes, then re-trigger
  useEffect(() => {
    setAnimated(false);
    const timer = window.setTimeout(() => setAnimated(true), 50);
    return () => window.clearTimeout(timer);
  }, [breakdown]);

  return (
    <div className="surface-card fade-in rounded-3xl p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold">Confidence breakdown</h3>
        <p className="text-sm text-[var(--text-muted)]">
          Compare the model&apos;s score across all three sentiment classes.
        </p>
      </div>

      <div className="space-y-4">
        {breakdown.map((item) => {
          const isDominant = item.label === dominant.label;
          const percentage = Math.round(item.score * 100);

          return (
            <div key={item.label} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className={isDominant ? "font-semibold text-[var(--text-primary)]" : "text-[var(--text-muted)]"}>
                  {item.label}
                </span>
                <span className={isDominant ? "font-semibold text-[var(--text-primary)]" : "text-[var(--text-muted)]"}>
                  {percentage}% ({item.score.toFixed(3)})
                </span>
              </div>
              <div
                className="h-3 overflow-hidden rounded-full bg-[var(--bg-elevated)]"
                role="progressbar"
                aria-valuenow={percentage}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${item.label}: ${percentage}%`}
              >
                <div
                  className="h-full rounded-full transition-[width] duration-700 ease-out"
                  style={{
                    width: `${animated ? percentage : 0}%`,
                    backgroundColor: colors[item.label],
                    filter: isDominant ? "brightness(1.15)" : "none",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
