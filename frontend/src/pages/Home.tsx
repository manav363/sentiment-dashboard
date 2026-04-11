import { useState } from "react";

import TextInput from "../components/input/TextInput";
import URLInput from "../components/input/URLInput";
import Tabs from "../components/ui/Tabs";

export default function Home() {
  const [activeTab, setActiveTab] = useState("text");

  return (
    <section className="space-y-8">
      <div className="fade-in max-w-3xl space-y-4">
        <span className="inline-flex rounded-full border border-[var(--accent-dim)] bg-[rgba(0,212,170,0.08)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
          Sentiment intelligence
        </span>
        <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
          Understand the sentiment behind any text
        </h1>
        <p className="max-w-2xl text-base leading-7 text-[var(--text-muted)] md:text-lg">
          Compare emotion signals across pasted text and article URLs with fast model-backed visual summaries.
        </p>
      </div>

      <div className="surface-card rounded-[28px] p-4">
        <Tabs
          tabs={[
            { id: "text", label: "Text" },
            { id: "url", label: "URL" },
          ]}
          active={activeTab}
          onChange={setActiveTab}
        />

        <div className="mt-6">
          {activeTab === "text" ? <TextInput /> : null}
          {activeTab === "url" ? <URLInput /> : null}
        </div>
      </div>
    </section>
  );
}
