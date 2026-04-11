import { useNavigate } from "react-router-dom";

import Button from "../components/ui/Button";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <section className="surface-card fade-in rounded-3xl p-10 text-center">
      <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-primary)] text-3xl">
        ?
      </div>
      <h2 className="text-2xl font-semibold">Page not found</h2>
      <p className="mt-3 text-[var(--text-muted)]">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button className="mt-6" onClick={() => navigate("/")}>
        Back to Home
      </Button>
    </section>
  );
}
