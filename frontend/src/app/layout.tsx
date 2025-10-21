import type { Metadata } from "next";
import "@/styles/globals.css";

/**
 * FR: Métadonnées de l'application
 */
export const metadata: Metadata = {
  title: "aikoGPT - Analyse Besoins & Cas d'Usage IA",
  description: "Plateforme d'analyse de besoins et génération de cas d'usage IA",
};

/**
 * FR: Layout principal de l'application
 * 
 * Ce layout est partagé par toutes les pages de l'application.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body>
        {children}
      </body>
    </html>
  );
}

