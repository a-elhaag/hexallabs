import { Nav } from "~/components/nav/Nav";
import { Footer } from "~/components/sections/Footer";
import { ModelsHero } from "~/components/sections/models/ModelsHero";
import { ModelsGrid } from "~/components/sections/models/ModelsGrid";

export const metadata = {
  title: "Models — HexalLabs",
  description:
    "Eight specialized AI models. One council. Compare speed, context, and strengths to build your ideal panel.",
};

export default function ModelsPage() {
  return (
    <>
      <Nav />
      <main>
        <ModelsHero />
        <ModelsGrid />
      </main>
      <Footer />
    </>
  );
}
