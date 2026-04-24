"use client";

interface SidebarItem {
  id: string;
  label: string;
}

interface SidebarGroup {
  heading: string;
  items: SidebarItem[];
}

const groups: SidebarGroup[] = [
  {
    heading: "Getting Started",
    items: [
      { id: "what-is-hexallabs", label: "What is HexalLabs" },
      { id: "quick-start", label: "Quick Start" },
    ],
  },
  {
    heading: "Modes",
    items: [
      { id: "the-council", label: "The Council" },
      { id: "oracle", label: "Oracle" },
      { id: "the-relay", label: "The Relay" },
      { id: "workflow", label: "Workflow" },
      { id: "scout", label: "Scout" },
    ],
  },
  {
    heading: "Features",
    items: [
      { id: "prompt-forge", label: "Prompt Forge" },
      { id: "prompt-lens", label: "Prompt Lens" },
      { id: "primal-protocol", label: "Primal Protocol" },
    ],
  },
  {
    heading: "API Reference",
    items: [
      { id: "endpoints", label: "Endpoints" },
      { id: "sse-events", label: "SSE Events" },
      { id: "authentication", label: "Authentication" },
    ],
  },
];

interface DocsSidebarProps {
  activeSection: string;
}

export function DocsSidebar({ activeSection }: DocsSidebarProps) {
  function scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  return (
    <aside
      className="shrink-0 overflow-y-auto"
      style={{
        width: 240,
        position: "sticky",
        top: 64,
        height: "calc(100vh - 64px)",
        background: "var(--color-panel)",
        borderRight: "1px solid var(--color-border)",
      }}
    >
      {/* Title */}
      <div
        className="px-5 pt-7 pb-5"
        style={{ borderBottom: "1px solid var(--color-border)" }}
      >
        <span
          className="text-[0.67rem] font-bold uppercase tracking-[0.14em]"
          style={{ color: "var(--color-muted)" }}
        >
          Documentation
        </span>
      </div>

      {/* Nav groups */}
      <nav className="px-3 py-4 flex flex-col gap-5">
        {groups.map((group) => (
          <div key={group.heading}>
            {/* Group heading */}
            <div
              className="px-2 mb-1 text-[0.62rem] font-bold uppercase tracking-[0.13em]"
              style={{ color: "var(--color-muted)", opacity: 0.6 }}
            >
              {group.heading}
            </div>

            {/* Items */}
            <ul className="list-none m-0 p-0 flex flex-col gap-0.5">
              {group.items.map((item) => {
                const isActive = activeSection === item.id;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => scrollTo(item.id)}
                      className="w-full text-left rounded-[8px] py-[0.32rem] px-3 text-[0.8rem] font-medium transition-all duration-[180ms] cursor-pointer"
                      style={{
                        background: isActive ? "rgba(98,144,195,0.08)" : "transparent",
                        color: isActive ? "#6290c3" : "var(--color-surface)",
                        opacity: isActive ? 1 : 0.7,
                        borderLeft: isActive
                          ? "3px solid #6290c3"
                          : "3px solid transparent",
                        paddingLeft: "0.6rem",
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          (e.currentTarget as HTMLButtonElement).style.opacity = "1";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                          (e.currentTarget as HTMLButtonElement).style.opacity = "0.7";
                        }
                      }}
                    >
                      {item.label}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
