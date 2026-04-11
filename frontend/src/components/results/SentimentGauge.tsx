import type { SentimentResult } from "../../types/sentiment";

type SentimentGaugeProps = {
  result: SentimentResult;
};

/**
 * Compute a weighted needle angle from breakdown scores.
 * Maps the score distribution to a 0°–180° arc where:
 *   0° = fully negative, 90° = fully neutral, 180° = fully positive.
 * Each label pulls the needle toward its zone proportionally.
 */
function computeNeedleAngle(result: SentimentResult): number {
  const scores: Record<string, number> = {};
  for (const item of result.breakdown) {
    scores[item.label] = item.score;
  }

  const neg = scores["negative"] ?? 0;
  const neu = scores["neutral"] ?? 0;
  const pos = scores["positive"] ?? 0;

  // Weighted average: negative→30°, neutral→90°, positive→150°
  const total = neg + neu + pos || 1;
  const angle = (neg * 30 + neu * 90 + pos * 150) / total;

  return Math.max(10, Math.min(170, angle));
}

function arcPath(startX: number, startY: number, endX: number, endY: number) {
  return `M ${startX} ${startY} A 70 70 0 0 1 ${endX} ${endY}`;
}

export default function SentimentGauge({ result }: SentimentGaugeProps) {
  const angle = computeNeedleAngle(result);
  const percentage = Math.round(result.score * 100);

  return (
    <div className="surface-card fade-in rounded-3xl p-6">
      <div className="mx-auto max-w-md">
        <svg viewBox="0 0 200 140" className="w-full" role="img" aria-label={`Sentiment gauge showing ${result.label} at ${percentage}% confidence`}>
          <path d={arcPath(30, 100, 76, 35)} fill="none" stroke="var(--negative)" strokeWidth="12" strokeLinecap="round" />
          <path d={arcPath(76, 35, 124, 35)} fill="none" stroke="var(--neutral)" strokeWidth="12" strokeLinecap="round" />
          <path d={arcPath(124, 35, 170, 100)} fill="none" stroke="var(--positive)" strokeWidth="12" strokeLinecap="round" />
          <g
            transform={`rotate(${angle} 100 100)`}
            style={{ transition: "transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)" }}
          >
            <line
              x1="100"
              y1="100"
              x2="100"
              y2="36"
              stroke="var(--text-primary)"
              strokeWidth="4"
              strokeLinecap="round"
            />
          </g>
          <circle cx="100" cy="100" r="9" fill="var(--text-primary)" />
          <circle cx="100" cy="100" r="4" fill="var(--bg-primary)" />
        </svg>

        <div className="-mt-1 text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-[var(--text-muted)]">Dominant sentiment</p>
          <h3 className="mt-3 text-3xl font-bold uppercase tracking-[0.15em] text-[var(--text-primary)]">
            {result.label}
          </h3>
          <p className="mt-2 text-lg font-medium text-[var(--accent)]">{percentage}% confidence</p>
        </div>
      </div>
    </div>
  );
}
