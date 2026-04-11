import { render, screen } from "@testing-library/react";

import ErrorBoundary from "./ErrorBoundary";

function BrokenComponent(): never {
  throw new Error("boom");
}

describe("ErrorBoundary", () => {
  it("renders a recovery UI when a child crashes", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reload app" })).toBeInTheDocument();

    consoleError.mockRestore();
  });
});
