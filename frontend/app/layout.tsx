import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { QueryProvider } from "@/components/providers/QueryProvider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { AlertFeed } from "@/components/layout/AlertFeed";

export const metadata: Metadata = {
  title: "NEXUS Command Center",
  description: "Tactical Intelligence Dashboard for Karnataka State Police",
};

import { IncidentProvider } from "@/hooks/useLiveIncident";
import { DemoProvider } from "@/contexts/DemoContext";
import { DrawerProvider } from "@/components/investigation/InvestigationDrawer";
import { AddToCaseProvider } from "@/components/investigation/AddToCaseProvider";
import { GlobalDemoOverlay } from "@/components/demo/GlobalDemoOverlay";
import { ErrorBoundary } from "@/components/layout/ErrorBoundary";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="h-full flex overflow-hidden bg-background text-foreground">
        <QueryProvider>
          <IncidentProvider>
            <DemoProvider>
              <AddToCaseProvider>
                <DrawerProvider>
                <Sidebar />
                <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                  <TopBar />
                  <main className="flex-1 overflow-auto bg-background/50 relative">
                    <ErrorBoundary fallbackMessage="The main application module failed to load.">
                      {children}
                    </ErrorBoundary>
                  </main>
                  <AlertFeed />
                </div>
                <GlobalDemoOverlay />
              </DrawerProvider>
              </AddToCaseProvider>
            </DemoProvider>
          </IncidentProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
