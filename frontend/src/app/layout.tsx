import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FTex - Decision Intelligence Platform',
  description: 'Financial Crime Detection & Decision Intelligence for Tier 1 Banking',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-surface-950 text-surface-100 antialiased">
        {children}
      </body>
    </html>
  );
}

