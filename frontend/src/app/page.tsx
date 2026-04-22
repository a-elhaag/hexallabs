import { Header } from "~/components/landing/Header";
import { Hero } from "~/components/landing/Hero";
import { HowItWorks } from "~/components/landing/HowItWorks";
import { Modes } from "~/components/landing/Modes";
import { Models } from "~/components/landing/Models";
import { Faq } from "~/components/landing/Faq";
import { Footer } from "~/components/landing/Footer";

export default function HomePage() {
  return (
    <>
      <Header />
      <main className="relative">
        <Hero />
        <HowItWorks />
        <Modes />
        <Models />
        <Faq />
      </main>
      <Footer />
    </>
  );
}
