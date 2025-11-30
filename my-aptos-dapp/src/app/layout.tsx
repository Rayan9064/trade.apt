import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ReactQueryProvider } from "@/components/ReactQueryProvider";
import { WalletProvider } from "@/components/WalletProvider";
import { Toaster } from "@/components/ui/toaster";
import { WrongNetworkAlert } from "@/components/WrongNetworkAlert";
import { PriceProvider } from "@/context/PriceContext";

import "./globals.css";

export const metadata: Metadata = {
  applicationName: "Trade.apt - AI Trading Platform",
  title: "Trade.apt - AI Trading Platform",
  description: "DeFi-style trading assistant with AI-powered analysis and real-time prices",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <WalletProvider>
          <ReactQueryProvider>
            <PriceProvider>
              <div id="root">{children}</div>
              <WrongNetworkAlert />
              <Toaster />
            </PriceProvider>
          </ReactQueryProvider>
        </WalletProvider>
      </body>
    </html>
  );
}
