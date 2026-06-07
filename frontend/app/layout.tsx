import "./globals.css";

export const metadata = {
  title: "Enterprise Agentic Knowledge Intelligence Platform",
  description: "Local enterprise AI knowledge intelligence platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

