import { Button } from "~/components/ui/Button";

export function Cta() {
  return (
    <section className="max-w-[1140px] mx-auto px-14 pb-24">
      <div className="bg-[#faf7f4] rounded-[24px] border border-[1.5px] border-[rgba(168,144,128,0.18)] shadow-[0_4px_32px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.8)] p-12 flex items-center justify-between gap-8">
        <div>
          <h2 className="text-[1.6rem] font-extrabold text-[var(--color-bg)] tracking-[-0.02em] mb-[0.35rem]">
            Run the council.
          </h2>
          <p className="text-[0.8rem] font-medium text-[#7a6a62]">
            No setup. Pick your models and ask anything.
          </p>
        </div>
        <Button variant="blue">Start now</Button>
      </div>
    </section>
  );
}
