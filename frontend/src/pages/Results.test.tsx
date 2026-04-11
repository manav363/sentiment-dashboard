import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import Results from "./Results";
import type { ResultsNavigationState } from "../types/sentiment";

const urlResultState: ResultsNavigationState = {
  mode: "url",
  input: "https://example.com/story",
  result: {
    url: "https://example.com/story",
    title: "Example story",
    chunk_count: 2,
    result: {
      label: "positive",
      score: 0.91,
      text_preview: "Example story text",
      breakdown: [
        { label: "positive", score: 0.91 },
        { label: "neutral", score: 0.06 },
        { label: "negative", score: 0.03 },
      ],
    },
  },
};

describe("Results", () => {
  beforeEach(() => {
    window.localStorage.removeItem("sentiment_history");
    window.sessionStorage.removeItem("sentiscope_latest_result");
  });

  it("restores the latest result from session storage on refresh", () => {
    window.sessionStorage.setItem("sentiscope_latest_result", JSON.stringify(urlResultState));

    render(
      <MemoryRouter initialEntries={["/results"]}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "Example story", level: 2 }),
    ).toBeInTheDocument();
    expect(screen.getByText("2 chunks analyzed")).toBeInTheDocument();
  });

  it("does not duplicate saved history entries on rerender", () => {
    const view = render(
      <MemoryRouter initialEntries={[{ pathname: "/results", state: urlResultState }]}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(JSON.parse(window.localStorage.getItem("sentiment_history") ?? "[]")).toHaveLength(1);

    view.rerender(
      <MemoryRouter initialEntries={[{ pathname: "/results", state: urlResultState }]}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(JSON.parse(window.localStorage.getItem("sentiment_history") ?? "[]")).toHaveLength(1);
  });
});
