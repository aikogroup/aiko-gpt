"use client";

/**
 * Page 1 : Accueil (Upload)
 * 
 * FR: Page d'upload des fichiers et lancement de l'analyse
 * 
 * Éléments :
 * - Logo entreprise (en haut à gauche)
 * - Navbar (pages du site)
 * - Zone d'upload fichier Excel
 * - Zone d'upload fichiers PDF/JSON (multi-fichiers)
 * - Champ texte : nom de l'entreprise
 * - Bouton "Analyser" → lance /api/run
 */

import { useState } from "react";
// TODO (FR): Importer les composants nécessaires
// import SideNav from "@/components/SideNav";
// import UploadZone from "@/components/UploadZone";
// import Spinner from "@/components/Spinner";

export default function Home() {
  // TODO (FR): États locaux
  // const [excelFile, setExcelFile] = useState<File | null>(null);
  // const [pdfJsonFiles, setPdfJsonFiles] = useState<File[]>([]);
  // const [companyName, setCompanyName] = useState<string>("");
  // const [isLoading, setIsLoading] = useState<boolean>(false);

  // TODO (FR): Fonction handleAnalyze()
  // - Valider que tous les fichiers sont présents
  // - Valider le nom d'entreprise
  // - Appeler /api/upload pour uploader les fichiers
  // - Appeler /api/run avec action "generate_needs"
  // - Stocker les résultats dans le state global (Zustand)
  // - Naviguer vers /needs

  // TODO (FR): Fonction handleFileChange()
  // - Gérer l'upload de fichiers
  // - Valider les formats (.xlsx, .pdf, .json)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* TODO (FR): Logo + Navbar */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <img
            src="/logoAiko.jpeg"
            alt="Aiko Logo"
            className="h-12"
          />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">
          Analyse de Besoins & Génération de Cas d'Usage IA
        </h1>

        {/* TODO (FR): Zone d'upload fichier Excel */}
        <section className="mb-6">
          <h2 className="text-xl font-semibold mb-4">1. Fichier Excel (Ateliers)</h2>
          {/* TODO (FR): Implémenter UploadZone pour Excel */}
          <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg">
            <p className="text-gray-600">TODO: Zone d'upload Excel</p>
          </div>
        </section>

        {/* TODO (FR): Zone d'upload fichiers PDF/JSON */}
        <section className="mb-6">
          <h2 className="text-xl font-semibold mb-4">2. Fichiers PDF/JSON (Transcriptions)</h2>
          {/* TODO (FR): Implémenter UploadZone multi-fichiers */}
          <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg">
            <p className="text-gray-600">TODO: Zone d'upload multi-fichiers PDF/JSON</p>
          </div>
        </section>

        {/* TODO (FR): Champ nom d'entreprise */}
        <section className="mb-6">
          <h2 className="text-xl font-semibold mb-4">3. Nom de l'entreprise</h2>
          <input
            type="text"
            placeholder="Ex: Aiko Technologies"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            // TODO (FR): Lier à l'état companyName
          />
        </section>

        {/* TODO (FR): Bouton Analyser */}
        <section className="mt-8">
          <button
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700"
            // TODO (FR): Lier à handleAnalyze
          >
            Analyser
          </button>
        </section>

        {/* TODO (FR): Loader pendant l'analyse */}
        {/* {isLoading && <Spinner />} */}
      </main>
    </div>
  );
}

