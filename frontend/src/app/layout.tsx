import type { Metadata } from "next";
import "@/styles/globals.css";
import { SideNav } from "@/components/SideNav";

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
    <html lang="fr" className="h-full">
      <body className="h-full bg-gray-50 overflow-hidden">
        {/* FR: Navbar à gauche (fixe) */}
        <SideNav />
        
        {/* FR: Contenu principal à droite */}
        <div className="ml-64 h-full overflow-y-auto bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  );
}

