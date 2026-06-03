import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Easy Parsing',
  description: 'AI Research Command Center for academic paper discovery',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
