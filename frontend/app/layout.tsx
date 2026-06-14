import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bastion Protocol — Live Threat Dashboard",
  description: "Autonomous Exploit Detection Agent for Robinhood Chain. Live threat monitoring, on-chain attestation, real-time alerts.",
  openGraph: {
    title: "Bastion Protocol — Live Threat Dashboard",
    description: "Autonomous Exploit Detection Agent for Robinhood Chain",
    images: ["/logo.svg"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
