import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { SettingsProvider } from "@/lib/settings-context";
import { ApiStatusProvider } from "@/lib/contexts/ApiStatusContext";
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

export const metadata: Metadata = {
  title: "Signals Zen | Web3 Intelligence",
  description: "Quiet clarity in a noisy ecosystem. Distilling global on-chain complexity into actionable editorial intelligence for the discerning institution.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}
        style={{ fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif", backgroundColor: "#0e0e0e", color: "#e7e5e5" }}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <SettingsProvider>
            <ApiStatusProvider>
              {children}
            </ApiStatusProvider>
          </SettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
