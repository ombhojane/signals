import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { SettingsProvider } from "@/lib/settings-context";
import { ApiStatusProvider } from "@/lib/contexts/ApiStatusContext";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Signals | AI Trading Arena",
  description: "Watch AI agents compete in simulated trading markets",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} antialiased font-sans bg-background text-foreground`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <SettingsProvider>
            <ApiStatusProvider>
              <div className="flex h-screen overflow-hidden">
                <Sidebar />
                <div className="flex flex-1 flex-col overflow-hidden">
                  <Header />
                  <main className="flex-1 overflow-y-auto bg-background p-6">
                    {children}
                  </main>
                </div>
              </div>
            </ApiStatusProvider>
          </SettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
