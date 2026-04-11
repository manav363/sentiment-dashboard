type LoaderProps = {
  mode?: "spinner" | "skeleton";
};

export default function Loader({ mode = "spinner" }: LoaderProps) {
  if (mode === "skeleton") {
    return (
      <div className="fade-in surface-card space-y-4 rounded-3xl p-6">
        <div className="h-6 w-2/5 animate-pulse rounded-full bg-[var(--bg-elevated)]" />
        <div className="h-40 animate-pulse rounded-2xl bg-[var(--bg-elevated)]" />
        <div className="grid gap-3 md:grid-cols-3">
          <div className="h-12 animate-pulse rounded-2xl bg-[var(--bg-elevated)]" />
          <div className="h-12 animate-pulse rounded-2xl bg-[var(--bg-elevated)]" />
          <div className="h-12 animate-pulse rounded-2xl bg-[var(--bg-elevated)]" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3 text-sm text-[var(--text-muted)]">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
      <span>Loading sentiment model...</span>
    </div>
  );
}
