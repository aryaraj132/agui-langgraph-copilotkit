import "./globals.css";
import "@copilotkit/react-ui/styles.css";

export const metadata = {
  title: "AG-UI Demo",
  description: "Chat + Segment Generation via AG-UI protocol",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
