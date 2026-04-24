"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { MODELS } from "./modelData";
import { ModelCard } from "./ModelCard";
import { ModelFilters } from "./ModelFilters";
import { ComparePanel } from "./ComparePanel";
import type { ActiveFilters } from "./ModelFilters";

gsap.registerPlugin(ScrollTrigger);

const DEFAULT_FILTERS: ActiveFilters = {
  role: "All",
  speed: "All",
  provider: "All",
};

function isVisible(model: (typeof MODELS)[number], filters: ActiveFilters) {
  if (filters.role !== "All" && model.role !== filters.role) return false;
  if (filters.speed !== "All" && model.speedTier !== filters.speed) return false;
  if (filters.provider !== "All") {
    if (filters.provider === "Anthropic" && model.provider !== "Anthropic")
      return false;
    if (filters.provider === "Azure" && model.provider !== "Azure AI Foundry")
      return false;
  }
  return true;
}

export function ModelsGrid() {
  const [filters, setFilters] = useState<ActiveFilters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<string[]>([]);
  const [shakeId, setShakeId] = useState<string | null>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const gridRef = useRef<HTMLDivElement>(null);

  // GSAP staggered entrance
  useEffect(() => {
    const cards = cardRefs.current.filter(Boolean) as HTMLDivElement[];
    if (!cards.length) return;

    gsap.fromTo(
      cards,
      { y: 24, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.6,
        stagger: 0.07,
        ease: "power3.out",
        scrollTrigger: {
          trigger: gridRef.current,
          start: "top 85%",
          once: true,
        },
      }
    );

    return () => {
      ScrollTrigger.getAll().forEach((t) => t.kill());
    };
  }, []);

  const handleToggleCompare = useCallback(
    (id: string) => {
      setSelected((prev) => {
        if (prev.includes(id)) {
          return prev.filter((s) => s !== id);
        }
        if (prev.length >= 3) {
          // Shake the card being rejected
          setShakeId(id);
          setTimeout(() => setShakeId(null), 500);
          return prev;
        }
        return [...prev, id];
      });
    },
    []
  );

  const selectedModels = MODELS.filter((m) => selected.includes(m.id));

  return (
    <section className="pb-32">
      <ModelFilters filters={filters} onChange={setFilters} />

      <div
        ref={gridRef}
        className="px-14 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
      >
        {MODELS.map((model, idx) => (
          <ModelCard
            key={model.id}
            ref={(el) => {
              cardRefs.current[idx] = el;
            }}
            model={model}
            visible={isVisible(model, filters)}
            isSelected={selected.includes(model.id)}
            onToggleCompare={handleToggleCompare}
            shakeCompare={shakeId === model.id}
          />
        ))}
      </div>

      {/* Spacer so content doesn't get hidden behind compare panel */}
      {selected.length >= 2 && <div className="h-[280px]" aria-hidden />}

      <ComparePanel
        models={selectedModels}
        onClear={() => setSelected([])}
      />
    </section>
  );
}
