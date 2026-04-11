import client from "./client";
import type {
  SentimentResult,
  URLAnalysisResult,
} from "../types/sentiment";

export const analyzeText = async (text: string): Promise<SentimentResult> => {
  const { data } = await client.post("/sentiment/analyze", { text });
  return data;
};

export const analyzeURL = async (url: string): Promise<URLAnalysisResult> => {
  const { data } = await client.post("/url/analyze", { url });
  return data;
};
