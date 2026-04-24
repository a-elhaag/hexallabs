"use client";

import type { SpeedTier } from "./modelData";

export type RoleFilter =
  | "All"
  | "Chairman"
  | "Reasoning"
  | "Fast Organizer"
  | "Deep Analysis"
  | "Long Context"
  | "Utility"
  | "Open-Source";

export type SpeedFilter = "All" | SpeedTier;
export type ProviderFilter = "All" | "Anthropic" | "Azure";

export interface ActiveFilters {
  role: RoleFilter;
  speed: SpeedFilter;
  provider: ProviderFilter;
}

interface ModelFiltersProps {
  filters: ActiveFilters;
  onChange: (next: ActiveFilters) => void;
}

const roleOptions: RoleFilter[] = [
  "All",
  "Chairman",
  "Reasoning",
  "Fast Organizer",
  "Deep Analysis",
  "Long Context",
  "Utility",
  "Open-Source",
];
const speedOptions: SpeedFilter[] = ["All", "Fast", "Medium", "Thorough"];
const providerOptions: ProviderFilter[] = ["All", "Anthropic", "Azure"];

function FilterGroup<T extends string>({
  label,
  options,
  active,
  onSelect,
}: {
  label: string;
  options: T[];
  active: T;
  onSelect: (v: T) => void;
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-[0.67rem] font-bold uppercase tracking-[0.12em] text-[var(--color-muted)] mr-1 whitespace-nowrap">
        {label}
      </span>
      {options.map((opt) => {
        const isActive = opt === active;
        return (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className="inline-flex items-center rounded-pill px-[0.9rem] py-[0.3rem] text-[0.72rem] font-bold cursor-pointer transition-all duration-[180ms] whitespace-nowrap"
            style={
              isActive
                ? {
                    background: "var(--color-accent)",
                    color: "#fff",
                    border: "1.5px solid var(--color-accent)",
                  }
                : {
                    background: "transparent",
                    color: "var(--color-muted)",
                    border: "1.5px solid rgba(168,144,128,0.32)",
                  }
            }
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

export function ModelFilters({ filters, onChange }: ModelFiltersProps) {
  const isFiltered =
    filters.role !== "All" ||
    filters.speed !== "All" ||
    filters.provider !== "All";

  return (
    <div className="px-14 pb-8 flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
        <FilterGroup
          label="Role"
          options={roleOptions}
          active={filters.role}
          onSelect={(v) => onChange({ ...filters, role: v })}
        />
        <FilterGroup
          label="Speed"
          options={speedOptions}
          active={filters.speed}
          onSelect={(v) => onChange({ ...filters, speed: v })}
        />
        <FilterGroup
          label="Provider"
          options={providerOptions}
          active={filters.provider}
          onSelect={(v) => onChange({ ...filters, provider: v })}
        />
        {isFiltered && (
          <button
            onClick={() =>
              onChange({ role: "All", speed: "All", provider: "All" })
            }
            className="text-[0.72rem] font-semibold text-[var(--color-muted)] underline underline-offset-2 cursor-pointer hover:text-[var(--color-surface)] transition-colors duration-[180ms]"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
