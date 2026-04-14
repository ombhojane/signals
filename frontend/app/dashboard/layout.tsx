"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition } from "@/components/ui/PageTransition";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen w-full overflow-hidden" style={{ backgroundColor: '#0e0e0e' }}>
      <Sidebar />
      <main className="flex-1 flex flex-col relative overflow-hidden h-screen min-w-0">
        <Header />
        <div className="flex-1 overflow-y-auto px-4 md:px-8 pb-24 md:pb-12 pt-4 min-w-0" style={{ scrollbarWidth: 'none' }}>
          <div className="max-w-7xl mx-auto w-full">
            <PageTransition delay={800}>
              {children}
            </PageTransition>
          </div>
        </div>
      </main>
    </div>
  );
}
