import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Thinkubator RAG Explorer",
  description: "Explore circular economy knowledge with AI-powered search and analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} font-sans antialiased bg-gradient-to-br from-blue-50 via-white to-green-50 min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
