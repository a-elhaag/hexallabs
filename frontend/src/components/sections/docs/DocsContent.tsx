import { Badge } from "~/components/ui/Badge";
import { Card } from "~/components/ui/Card";
import { CodeBlock } from "~/components/sections/docs/CodeBlock";

// ── Helpers ───────────────────────────────────────────────────────────────────

function SectionBadge({
  children,
  color,
}: {
  children: React.ReactNode;
  color?: string;
}) {
  if (!color) return <Badge>{children}</Badge>;
  return (
    <span
      className="inline-flex items-center rounded-pill px-[0.85rem] py-[0.28rem] text-[0.67rem] font-bold uppercase tracking-[0.08em] border"
      style={{
        background: `${color}18`,
        borderColor: `${color}40`,
        color: color,
      }}
    >
      {children}
    </span>
  );
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2
      className="text-[1.75rem] font-extrabold tracking-[-0.02em] mt-4 mb-4"
      style={{ color: "var(--color-surface)" }}
    >
      {children}
    </h2>
  );
}

function Prose({ children }: { children: React.ReactNode }) {
  return (
    <p
      className="text-[0.9rem] font-medium leading-[1.75] mb-4"
      style={{ color: "var(--color-muted)" }}
    >
      {children}
    </p>
  );
}

function Divider() {
  return (
    <hr
      className="my-0 border-0 border-t"
      style={{ borderColor: "var(--color-border)" }}
    />
  );
}

// ── Sections ─────────────────────────────────────────────────────────────────

export function DocsContent() {
  return (
    <div className="flex-1 min-w-0">

      {/* ── What is HexalLabs ── */}
      <section
        id="what-is-hexallabs"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>Overview</SectionBadge>
        <SectionHeading>What is HexalLabs?</SectionHeading>
        <Prose>
          HexalLabs is a horizontal LLM council platform. You submit a query
          and multiple frontier models run in parallel — each responding
          independently. Once all models have responded, an anonymous
          peer-review round begins: models critique each other&apos;s answers
          and adjust their confidence scores. Apex — the chairman model —
          then synthesizes the final answer, weighting each response by its
          final confidence score.
        </Prose>
        <Prose>
          Unlike chatting with a single model, HexalLabs surfaces the
          disagreements and convergences between models. You get a more
          complete, reviewed answer — along with visibility into where models
          agreed, where they diverged, and how confident each was. It&apos;s
          collective intelligence, not just autocomplete.
        </Prose>
      </section>

      <Divider />

      {/* ── Quick Start ── */}
      <section
        id="quick-start"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>Getting Started</SectionBadge>
        <SectionHeading>Quick Start</SectionHeading>
        <Prose>Get up and running in five steps.</Prose>

        <ol className="list-none m-0 p-0 flex flex-col gap-3 mb-8">
          {[
            "Open the app.",
            "Type your question.",
            "Select models or let auto-selection choose.",
            "Watch responses stream in real time.",
            "Review the synthesis.",
          ].map((step, i) => (
            <li key={i} className="flex items-start gap-4">
              <span
                className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-[0.7rem] font-bold"
                style={{
                  background: "rgba(98,144,195,0.12)",
                  border: "1px solid rgba(98,144,195,0.3)",
                  color: "#6290c3",
                }}
              >
                {i + 1}
              </span>
              <span
                className="text-[0.88rem] font-medium pt-1"
                style={{ color: "var(--color-surface)", opacity: 0.85 }}
              >
                {step}
              </span>
            </li>
          ))}
        </ol>

        <CodeBlock
          language="http"
          code={`# Example: run a council query
POST /api/query
{
  "query": "Explain transformer attention",
  "mode": "council",
  "models": ["apex", "prism", "depth"]
}`}
        />
      </section>

      <Divider />

      {/* ── The Council ── */}
      <section
        id="the-council"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge color="#6290c3">Modes</SectionBadge>
        <SectionHeading>The Council</SectionHeading>
        <Prose>
          The flagship mode. Between 2 and 7 models run in parallel, each
          responding to your query independently. After all models have
          responded, a peer-review round begins — models see anonymized
          versions of each other&apos;s responses and critique them,
          adjusting their confidence scores in the process. Apex synthesizes
          the final answer weighted by those final confidence scores.
        </Prose>

        <Card className="p-6 mt-6">
          <h3
            className="text-[0.8rem] font-bold uppercase tracking-[0.08em] mb-4"
            style={{ color: "var(--color-muted)" }}
          >
            Execution flow
          </h3>
          <ol className="list-none m-0 p-0 flex flex-col gap-3">
            {[
              "Query submitted → Prompt Forge refines it.",
              "Selected models respond in parallel.",
              "Each model self-rates confidence (1–10).",
              "Peer review: anonymous critique round.",
              "Confidence scores adjust based on critiques.",
              "Apex synthesizes the final weighted answer.",
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-4">
                <span
                  className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[0.65rem] font-bold"
                  style={{
                    background: "rgba(98,144,195,0.12)",
                    border: "1px solid rgba(98,144,195,0.25)",
                    color: "#6290c3",
                  }}
                >
                  {i + 1}
                </span>
                <span
                  className="text-[0.85rem] font-medium pt-0.5"
                  style={{ color: "#2c2c2c", opacity: 0.8 }}
                >
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </Card>
      </section>

      <Divider />

      {/* ── Oracle ── */}
      <section
        id="oracle"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge color="#9b72cf">Modes</SectionBadge>
        <SectionHeading>Oracle</SectionHeading>
        <Prose>
          Single-model mode. Choose one model and get a direct, streamed
          response. No parallel execution, no peer review. Best for simple
          queries, quick lookups, or when you already know which model
          handles your domain best.
        </Prose>
      </section>

      <Divider />

      {/* ── The Relay ── */}
      <section
        id="the-relay"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge color="#5ba08a">Modes</SectionBadge>
        <SectionHeading>The Relay</SectionHeading>
        <Prose>
          Mid-generation model handoff. The first model starts responding;
          when it reaches a predefined handoff trigger — a threshold token,
          a signal, or a confidence drop — it passes its partial output and
          full context to the next model. The second model continues the
          response seamlessly from where the first left off.
        </Prose>
        <Card className="p-5 mt-4">
          <p
            className="text-[0.84rem] font-semibold leading-[1.65]"
            style={{ color: "#2c2c2c", opacity: 0.75 }}
          >
            <span
              className="font-bold"
              style={{ color: "#5ba08a" }}
            >
              Use case:
            </span>{" "}
            Great for tasks where one model is fast for outline and structure
            but a deeper model is better suited for final synthesis. For
            example, Swift handles the scaffold, Depth handles the analysis.
          </p>
        </Card>
      </section>

      <Divider />

      {/* ── Workflow ── */}
      <section
        id="workflow"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge color="#c09050">Modes</SectionBadge>
        <SectionHeading>Workflow</SectionHeading>
        <Prose>
          Node-based pipeline builder. Each node is a model or a tool; the
          output of one node feeds into the next. Build pipelines by
          dragging and dropping edges between nodes. Council and Oracle are
          presets within this system — Workflow is the general engine
          underneath them.
        </Prose>
        <Prose>
          Supports three node types: <strong>model nodes</strong> (any
          council model), <strong>passthrough nodes</strong> (route without
          transformation), and <strong>prompt_template nodes</strong> (inject
          structured prompts into the pipeline).
        </Prose>
      </section>

      <Divider />

      {/* ── Scout ── */}
      <section
        id="scout"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge color="#5b9062">Features</SectionBadge>
        <SectionHeading>Scout</SectionHeading>
        <Prose>
          Web search injection. Before models respond, Scout runs a Tavily
          web search and injects the most relevant results into the model
          context. Models then respond with up-to-date information rather
          than relying on training data alone.
        </Prose>
        <div className="grid grid-cols-3 gap-3 mt-4">
          {[
            { label: "Force", desc: "Always search before responding." },
            { label: "Auto", desc: "Model decides whether to search." },
            { label: "Off", desc: "No web search — training data only." },
          ].map(({ label, desc }) => (
            <div
              key={label}
              className="rounded-[14px] p-4 border"
              style={{
                background: "rgba(91,144,98,0.06)",
                borderColor: "rgba(91,144,98,0.2)",
              }}
            >
              <div
                className="text-[0.75rem] font-bold mb-1"
                style={{ color: "#5b9062" }}
              >
                {label}
              </div>
              <div
                className="text-[0.78rem] font-medium leading-[1.5]"
                style={{ color: "var(--color-muted)" }}
              >
                {desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* ── Prompt Forge ── */}
      <section
        id="prompt-forge"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>Features</SectionBadge>
        <SectionHeading>Prompt Forge</SectionHeading>
        <Prose>
          Pre-send prompt improvement, powered by Spark. Before your query
          reaches the council, Prompt Forge rewrites and improves it —
          adding clarity, structure, and specificity where your original
          phrasing was vague or underspecified. You review the rewrite, then
          accept it, modify it, or override it entirely.
        </Prose>
      </section>

      <Divider />

      {/* ── Prompt Lens ── */}
      <section
        id="prompt-lens"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>Features</SectionBadge>
        <SectionHeading>Prompt Lens</SectionHeading>
        <Prose>
          Post-run interpretation analysis, powered by Spark. After the
          council finishes, Prompt Lens shows a breakdown of how each model
          interpreted your original prompt — surfacing differences in
          framing, focus, and assumptions. Useful for understanding why
          models diverged and for refining your prompting approach.
        </Prose>
      </section>

      <Divider />

      {/* ── Primal Protocol ── */}
      <section
        id="primal-protocol"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>Features</SectionBadge>
        <SectionHeading>Primal Protocol</SectionHeading>
        <Prose>
          A toggle available on any mode. When enabled, Apex rewrites its
          final synthesis in brutally compressed caveman-style — stripping
          out hedging, filler, and verbosity. What remains is the essence.
        </Prose>
        <div
          className="rounded-[14px] border px-6 py-5 mt-4 flex items-center gap-4"
          style={{
            background: "rgba(168,144,128,0.05)",
            borderColor: "var(--color-border)",
          }}
        >
          <span className="text-2xl" aria-hidden>&#x1F9B7;</span>
          <p
            className="text-[0.88rem] font-semibold leading-[1.65] m-0"
            style={{ color: "var(--color-muted)" }}
          >
            &ldquo;Multiple minds. One answer. No fluff.&rdquo; — Use when you
            want the conclusion without the padding.
          </p>
        </div>
      </section>

      <Divider />

      {/* ── Endpoints ── */}
      <section
        id="endpoints"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>API Reference</SectionBadge>
        <SectionHeading>Endpoints</SectionHeading>
        <Prose>
          All endpoints are JSON over HTTP. Streaming endpoints use
          Server-Sent Events (SSE) and require an{" "}
          <code
            className="px-1.5 py-0.5 rounded-[6px] text-[0.8em] font-mono"
            style={{
              background: "rgba(168,144,128,0.1)",
              color: "var(--color-surface)",
            }}
          >
            Authorization: Bearer &lt;token&gt;
          </code>{" "}
          header.
        </Prose>

        <Card className="overflow-hidden mt-4">
          <table className="w-full border-collapse text-[0.84rem]">
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(168,144,128,0.14)" }}>
                {["Method", "Path", "Description"].map((h) => (
                  <th
                    key={h}
                    className="text-left px-5 py-3 text-[0.68rem] font-bold uppercase tracking-[0.08em]"
                    style={{ color: "var(--color-muted)" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                {
                  method: "POST",
                  path: "/api/query",
                  desc: "Start a query (Oracle, Council, Relay)",
                },
                {
                  method: "POST",
                  path: "/api/workflow",
                  desc: "Execute a workflow pipeline",
                },
                {
                  method: "GET",
                  path: "/api/health",
                  desc: "Health check",
                },
              ].map((row, i) => (
                <tr
                  key={i}
                  style={{
                    borderBottom:
                      i < 2 ? "1px solid rgba(168,144,128,0.1)" : "none",
                  }}
                >
                  <td className="px-5 py-3">
                    <span
                      className="inline-flex px-2.5 py-0.5 rounded-[6px] text-[0.72rem] font-bold"
                      style={{
                        background:
                          row.method === "POST"
                            ? "rgba(98,144,195,0.12)"
                            : "rgba(91,160,138,0.12)",
                        color:
                          row.method === "POST" ? "#6290c3" : "#5ba08a",
                      }}
                    >
                      {row.method}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <code
                      className="font-mono text-[0.82rem]"
                      style={{ color: "#2c2c2c", opacity: 0.85 }}
                    >
                      {row.path}
                    </code>
                  </td>
                  <td
                    className="px-5 py-3 font-medium"
                    style={{ color: "#2c2c2c", opacity: 0.7 }}
                  >
                    {row.desc}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>

      <Divider />

      {/* ── SSE Events ── */}
      <section
        id="sse-events"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>API Reference</SectionBadge>
        <SectionHeading>SSE Events</SectionHeading>
        <Prose>
          All streaming endpoints emit Server-Sent Events. The schema is
          identical across Oracle, Council, Relay, and Workflow — so the
          frontend has a single consumer for all modes.
        </Prose>

        <CodeBlock
          language="sse"
          code={`event: model_start
data: {"model": "prism", "session_id": "abc123"}

event: token
data: {"model": "prism", "token": "The ", "index": 0}

event: confidence
data: {"model": "prism", "score": 8}

event: peer_review
data: {"reviewer": "swift", "target": "prism", "critique": "...", "adjusted_score": 7}

event: synthesis_start
data: {"session_id": "abc123"}

event: synthesis_token
data: {"token": "Based on "}

event: done
data: {"session_id": "abc123"}`}
        />
      </section>

      <Divider />

      {/* ── Authentication ── */}
      <section
        id="authentication"
        className="py-14 px-10"
        style={{ maxWidth: 860 }}
      >
        <SectionBadge>API Reference</SectionBadge>
        <SectionHeading>Authentication</SectionHeading>
        <Prose>
          HexalLabs uses Supabase Auth. The frontend handles login and session
          management via{" "}
          <code
            className="px-1.5 py-0.5 rounded-[6px] text-[0.8em] font-mono"
            style={{
              background: "rgba(168,144,128,0.1)",
              color: "var(--color-surface)",
            }}
          >
            @supabase/ssr
          </code>
          . The backend verifies Supabase JWTs using RS256 via JWKS — no
          shared secrets.
        </Prose>

        <CodeBlock
          language="http"
          code={`Authorization: Bearer <supabase_jwt>`}
        />

        <div
          className="mt-5 rounded-[12px] border px-5 py-4 flex gap-3 items-start"
          style={{
            background: "rgba(98,144,195,0.06)",
            borderColor: "rgba(98,144,195,0.2)",
          }}
        >
          <svg
            className="shrink-0 mt-0.5"
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#6290c3"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p
            className="text-[0.84rem] font-medium leading-[1.6] m-0"
            style={{ color: "var(--color-muted)" }}
          >
            Include your Supabase JWT as a Bearer token in the{" "}
            <code
              className="font-mono text-[0.85em]"
              style={{ color: "var(--color-surface)" }}
            >
              Authorization
            </code>{" "}
            header on all API requests. Tokens are obtained after signing in
            through the HexalLabs app.
          </p>
        </div>

        {/* Bottom spacer */}
        <div className="h-16" />
      </section>
    </div>
  );
}
