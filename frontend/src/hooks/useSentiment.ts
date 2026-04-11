import { useMutation } from "@tanstack/react-query";

import { analyzeText, analyzeURL } from "../api/sentiment";

export function useAnalyzeText() {
  return useMutation({
    mutationFn: analyzeText,
  });
}

export function useAnalyzeURL() {
  return useMutation({
    mutationFn: analyzeURL,
  });
}
