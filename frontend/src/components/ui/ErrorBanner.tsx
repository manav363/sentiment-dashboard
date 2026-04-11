import Button from "./Button";

type ErrorBannerProps = {
  message: string;
  onRetry?: () => void;
};

export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex items-center justify-between gap-4 rounded-2xl border border-[rgba(239,68,68,0.35)] border-l-4 border-l-[var(--negative)] bg-[rgba(127,29,29,0.18)] px-4 py-3 text-sm text-red-100"
    >
      <span>{message}</span>
      {onRetry ? (
        <Button size="sm" variant="danger" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
