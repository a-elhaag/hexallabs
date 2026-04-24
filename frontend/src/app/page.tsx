import { redirect } from "next/navigation";
import { createClient } from "~/lib/supabase/server";
import { Nav } from "~/components/nav/Nav";
import { Hero } from "~/components/sections/Hero";
import { Features } from "~/components/sections/Features";
import { HowItWorks } from "~/components/sections/HowItWorks";
import { Faq } from "~/components/sections/Faq";
import { Cta } from "~/components/sections/Cta";
import { Footer } from "~/components/sections/Footer";

export default async function HomePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (user) redirect("/chat");

  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
