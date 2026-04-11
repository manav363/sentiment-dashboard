import { Component, type ReactNode } from "react";

import Button from "./Button";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  override state: ErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(error: Error) {
    console.error("App rendering failed", error);
  }

  override render() {
    if (this.state.hasError) {
      return (
        <section className="surface-card fade-in mx-auto mt-10 max-w-2xl rounded-3xl p-10 text-center">
          <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full border border-[rgba(239,68,68,0.3)] bg-[rgba(239,68,68,0.08)] text-3xl text-[var(--negative)]">
            !
          </div>
          <h2 className="text-2xl font-semibold">Something went wrong</h2>
          <p className="mt-3 text-[var(--text-muted)]">
            The app hit an unexpected error. Reloading the page will usually recover it.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button onClick={() => window.location.reload()}>Reload app</Button>
            <Button variant="secondary" onClick={() => window.location.assign("/")}>
              Go home
            </Button>
          </div>
        </section>
      );
    }

    return this.props.children;
  }
}
