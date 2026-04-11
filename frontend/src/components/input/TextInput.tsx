import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAnalyzeText } from "../../hooks/useSentiment";
import type { ResultsNavigationState } from "../../types/sentiment";
import Button from "../ui/Button";
import ErrorBanner from "../ui/ErrorBanner";
import Loader from "../ui/Loader";

export default function TextInput() {
  const [text, setText] = useState("");
  const [clipboardError, setClipboardError] = useState<string | null>(null);
  const navigate = useNavigate();
  const analyzeTextMutation = useAnalyzeText();

  const handlePaste = async () => {
    try {
      const clipboardText = await navigator.clipboard.readText();
      setText((current) => `${current}${clipboardText}`.trim());
      setClipboardError(null);
    } catch {
      setClipboardError("Clipboard access is unavailable in this browser.");
    }
  };

  const handleSubmit = async () => {
    const trimmed = text.trim();
    if (trimmed.length < 3) {
      return;
    }

    try {
      const result = await analyzeTextMutation.mutateAsync(trimmed);
      const state: ResultsNavigationState = { result, mode: "text", input: trimmed };
      navigate("/results", { state });
    } catch {
      return;
    }
  };

  return (
    <section className="fade-in space-y-5">
      <div className="surface-card rounded-3xl p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold" id="text-input-heading">Paste text</h3>
            <p className="text-sm text-[var(--text-muted)]">
              Analyze articles, reviews, transcripts, or any long-form copy.
            </p>
          </div>
          <span className="rounded-full border border-[var(--border)] px-3 py-1 text-xs text-[var(--text-muted)]" aria-live="polite">
            {text.length}/5000
          </span>
        </div>

        <textarea
          id="sentiment-text-input"
          rows={9}
          value={text}
          onChange={(event) => setText(event.target.value.slice(0, 5000))}
          placeholder="Paste text to analyze..."
          aria-labelledby="text-input-heading"
          aria-describedby="text-input-hint"
          className="min-h-56 w-full rounded-2xl border border-[var(--border)] bg-[var(--bg-primary)] px-4 py-4 text-sm text-[var(--text-primary)] outline-none transition placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]"
        />
        <p id="text-input-hint" className="sr-only">Enter between 3 and 5000 characters of text to analyze its sentiment.</p>

        <div className="mt-4 flex flex-wrap gap-3">
          <Button variant="secondary" onClick={handlePaste}>
            Paste
          </Button>
          <Button variant="secondary" onClick={() => setText("")}>
            Clear
          </Button>
        </div>

        <div className="mt-5">
          <Button
            id="analyze-text-button"
            className="w-full"
            loading={analyzeTextMutation.isPending}
            disabled={text.trim().length < 3}
            onClick={handleSubmit}
          >
            Analyze Sentiment
          </Button>
        </div>
      </div>

      {clipboardError ? <ErrorBanner message={clipboardError} /> : null}
      {analyzeTextMutation.isError ? (
        <ErrorBanner
          message="Text analysis failed. Please try again."
          onRetry={handleSubmit}
        />
      ) : null}
      {analyzeTextMutation.isPending ? <Loader mode="skeleton" /> : null}
    </section>
  );
}
