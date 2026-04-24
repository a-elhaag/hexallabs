import { Badge } from "~/components/ui/Badge";

export function ModelsHero() {
  return (
    <section className="pt-24 pb-16 px-14 flex flex-col items-center text-center">
      <Badge dot className="mb-6">The roster</Badge>
      <h1
        className="font-extrabold tracking-[-0.03em] leading-[1.06] text-[var(--color-surface)] mb-5"
        style={{ fontSize: "clamp(2.4rem, 4vw, 3.5rem)" }}
      >
        Eight minds. One council.
      </h1>
      <p
        className="text-[var(--color-muted)] font-medium leading-[1.72] max-w-[42rem]"
        style={{ fontSize: "clamp(0.85rem, 1.4vw, 1rem)" }}
      >
        Each model brings a different way of thinking. Together, they converge
        on answers no single model could reach alone.
      </p>
    </section>
  );
}
