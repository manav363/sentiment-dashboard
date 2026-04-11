import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import App from "./App";
import NotFound from "./pages/NotFound";

function renderApp(initialEntry: string) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App navigation", () => {
  it("marks only the root Analyze link as active on the home route", () => {
    renderApp("/");

    expect(screen.getByRole("link", { name: "Analyze" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "History" })).not.toHaveAttribute("aria-current");
  });

  it("marks only the History link as active on the history route", () => {
    renderApp("/history");

    expect(screen.getByRole("link", { name: "History" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Analyze" })).not.toHaveAttribute("aria-current");
  });
});

describe("NotFound", () => {
  it("navigates back home without a full page reload", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/missing"]}>
        <Routes>
          <Route path="/" element={<div>Home page</div>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: "Back to Home" }));

    expect(screen.getByText("Home page")).toBeInTheDocument();
  });
});
