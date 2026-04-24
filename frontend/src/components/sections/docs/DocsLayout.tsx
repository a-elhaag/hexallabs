"use client";

import { useEffect, useRef, useState } from "react";
import { DocsSidebar } from "~/components/sections/docs/DocsSidebar";
import { DocsContent } from "~/components/sections/docs/DocsContent";

const SECTION_IDS = [
  "what-is-hexallabs",
  "quick-start",
  "the-council",
  "oracle",
  "the-relay",
  "workflow",
  "scout",
  "prompt-forge",
  "prompt-lens",
  "primal-protocol",
  "endpoints",
  "sse-events",
  "authentication",
];

export function DocsLayout() {
  const [activeSection, setActiveSection] = useState<string>(SECTION_IDS[0] ?? "");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const handleIntersect: IntersectionObserverCallback = (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setActiveSection(entry.target.id);
          break;
        }
      }
    };

    observerRef.current = new IntersectionObserver(handleIntersect, {
      rootMargin: "-20% 0px -70% 0px",
      threshold: 0,
    });

    const observer = observerRef.current;

    for (const id of SECTION_IDS) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div className="flex" style={{ minHeight: "calc(100vh - 64px)" }}>
      <DocsSidebar activeSection={activeSection} />
      <DocsContent />
    </div>
  );
}
