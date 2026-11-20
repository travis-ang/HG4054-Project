import type { Metadata } from "next";
import { Barlow, Barlow_Condensed, Bebas_Neue } from "next/font/google";
import "./globals.css";

const bebas = Bebas_Neue({ weight: "400", subsets: ["latin"], variable: "--font-bebas" });
const barlow = Barlow({ weight: ["400", "500", "600", "700"], subsets: ["latin"], variable: "--font-barlow" });
const barlowCond = Barlow_Condensed({ weight: ["500", "600", "700"], subsets: ["latin"], variable: "--font-barlow-cond" });

export const metadata: Metadata = {
  title: "Are superstars more self-focused?",
  description: "HG4054 final project: 'I' and 'we' in NBA playoff press conferences",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${bebas.variable} ${barlow.variable} ${barlowCond.variable}`}>
      <body>{children}</body>
    </html>
  );
}
