import { Nav } from "~/components/nav/Nav";
import { Footer } from "~/components/sections/Footer";
import { DocsLayout } from "~/components/sections/docs/DocsLayout";

export const metadata = {
  title: "Docs — HexalLabs",
  description:
    "Documentation for HexalLabs: modes, features, API reference, and SSE event schema.",
};

export default function DocsPage() {
  return (
    <>
      <Nav />
      <main>
        <DocsLayout />
      </main>
      <Footer />
    </>
  );
}
