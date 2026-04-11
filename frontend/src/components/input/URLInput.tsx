import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAnalyzeURL } from "../../hooks/useSentiment";
import type { ResultsNavigationState } from "../../types/sentiment";
import Button from "../ui/Button";
import ErrorBanner from "../ui/ErrorBanner";
import Loader from "../ui/Loader";

function getDomain(value: string): string | null {
  try {
    const parsed = new URL(value);
    if (!/^https?:/.test(parsed.protocol)) {
      return null;
    }
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

export default function URLInput() {
  const [url, setUrl] = useState("");
  const navigate = useNavigate();
  const analyzeURLMutation = useAnalyzeURL();
  const domain = getDomain(url.trim());

  const handleSubmit = async () => {
    if (!domain) {
      return;
    }

    try {
      const trimmed = url.trim();
      const result = await analyzeURLMutation.mutateAsync(trimmed);
      const state: ResultsNavigationState = { result, mode: "url", input: trimmed };
      navigate("/results", { state });
    } catch {
      return;
    }
  };

  return (
    <section className="fade-in space-y-5">
      <div className="surface-card rounded-3xl p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold" id="url-input-heading">Analyze a news article URL</h3>
          <p className="text-sm text-[var(--text-muted)]">
            Scrapes article body text and analyzes sentiment.
          </p>
        </div>

        <label htmlFor="sentiment-url-input" className="space-y-2">
          <span className="text-sm font-medium text-[var(--text-muted)]">Article URL</span>
          <input
            id="sentiment-url-input"
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://example.com/news/story"
            aria-describedby="url-input-hint"
            className="w-full rounded-2xl border border-[var(--border)] bg-[var(--bg-primary)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none transition placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]"
          />
        </label>
        <p id="url-input-hint" className="sr-only">Enter a valid HTTP or HTTPS URL to scrape and analyze.</p>

        {domain ? (
          <div className="mt-3 inline-flex rounded-full border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1 text-xs text-[var(--text-muted)]">
            Domain preview: {domain}
          </div>
        ) : null}

        <div className="mt-5">
          <Button
            id="analyze-url-button"
            className="w-full"
            loading={analyzeURLMutation.isPending}
            disabled={!domain}
            onClick={handleSubmit}
          >
            Analyze Article
          </Button>
        </div>
      </div>

      {analyzeURLMutation.isError ? (
        <ErrorBanner
          message="URL analysis failed. Make sure the URL is valid and reachable."
          onRetry={handleSubmit}
        />
      ) : null}
      {analyzeURLMutation.isPending ? <Loader mode="skeleton" /> : null}
    </section>
  );
}
