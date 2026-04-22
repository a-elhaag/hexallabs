import "~/styles/globals.css";

import { type Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

export const metadata: Metadata = {
  title: "Hexal — a council of AI models for every question",
  description:
    "Hexal runs your question through a council of AI models that debate, critique, and agree — so you get the answer instead of a best-guess.",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
