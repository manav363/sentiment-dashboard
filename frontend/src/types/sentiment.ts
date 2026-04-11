export type SentimentLabel = "positive" | "negative" | "neutral";

export interface ScoreBreakdown {
  label: SentimentLabel;
  score: number;
}

export interface SentimentResult {
  label: SentimentLabel;
  score: number;
  breakdown: ScoreBreakdown[];
  text_preview: string;
}

export interface URLAnalysisResult {
  url: string;
  title: string;
  result: SentimentResult;
  chunk_count: number;
}

export type AnalysisMode = "text" | "url";

export interface HistoryEntry {
  id: string;
  mode: AnalysisMode;
  input: string;
  result: SentimentResult | URLAnalysisResult;
  timestamp: number;
}

export interface ResultsNavigationState {
  mode: AnalysisMode;
  input: string;
  result: SentimentResult | URLAnalysisResult;
}
