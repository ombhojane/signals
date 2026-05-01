import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { SettingsProvider } from "@/lib/settings-context";
import { ApiStatusProvider } from "@/lib/contexts/ApiStatusContext";
import { UnifiedWalletProvider } from "@/lib/contexts/UnifiedWalletProvider";
import { WalletProvider } from "@/lib/contexts/WalletContext";
import { PageTransition } from "@/components/ui/PageTransition";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export const metadata: Metadata = {
  title: "Signals | Web3 Intelligence",
  description: "Quiet clarity in a noisy ecosystem. Distilling global on-chain complexity into actionable editorial intelligence for the discerning institution.",
  icons: {
    icon: "/signal_logo.png",
    apple: "/signal_logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} ${spaceGrotesk.variable} antialiased`}
        style={{ fontFamily: "var(--font-inter), ui-sans-serif, system-ui, sans-serif", backgroundColor: "#0e0e0e", color: "#e7e5e5" }}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <SettingsProvider>
            <ApiStatusProvider>
              <UnifiedWalletProvider>
                <WalletProvider>
                  <PageTransition delay={1500}>
                    {children}
                  </PageTransition>
                </WalletProvider>
              </UnifiedWalletProvider>
            </ApiStatusProvider>
          </SettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
