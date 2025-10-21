"use client";

/**
 * Page 4 : Résultats
 * 
 * FR: Synthèse et téléchargement rapport Word
 * 
 * Éléments :
 * - Liste besoins validés
 * - Liste cas d'usage retenus
 * - Bouton "Télécharger" → appel /api/report
 */

import { useState } from "react";
// TODO (FR): Importer composants et store
// import { useStore } from "@/lib/store";
// import Spinner from "@/components/Spinner";

export default function ResultsPage() {
  // TODO (FR): Récupérer depuis state global
  // const { validatedNeeds, validatedUseCases } = useStore();

  // TODO (FR): États locaux
  // const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // TODO (FR): Fonction handleDownloadReport()
  // - Appeler GET /api/report avec validated_needs et validated_use_cases
  // - Télécharger le fichier .docx
  // - Afficher feedback (succès/erreur)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Résultats Finaux</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* TODO (FR): Section Besoins validés */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">
            Besoins Validés
          </h2>
          <div className="bg-white rounded-lg shadow p-6">
            {/* TODO (FR): Afficher la liste des besoins validés */}
            <p className="text-gray-600">TODO: Liste des besoins validés</p>
            {/* {validatedNeeds.map(need => (
              <div key={need.id} className="mb-4 pb-4 border-b last:border-0">
                <h3 className="font-semibold">{need.title}</h3>
                <ul className="mt-2 space-y-1">
                  {need.citations.map((citation, idx) => (
                    <li key={idx} className="text-sm text-gray-600">• {citation}</li>
                  ))}
                </ul>
              </div>
            ))} */}
          </div>
        </section>

        {/* TODO (FR): Section Cas d'usage retenus */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">
            Cas d'Usage Retenus
          </h2>
          
          {/* TODO (FR): Quick Wins */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-3">Quick Wins</h3>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600">TODO: Quick Wins validés</p>
            </div>
          </div>

          {/* TODO (FR): Structuration IA */}
          <div>
            <h3 className="text-xl font-semibold mb-3">Structuration IA</h3>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600">TODO: Structuration IA validés</p>
            </div>
          </div>
        </section>

        {/* TODO (FR): Bouton téléchargement */}
        <section className="mt-8">
          <button
            className="bg-green-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-green-700"
            // TODO (FR): Lier à handleDownloadReport
          >
            📥 Télécharger le Rapport Word
          </button>
        </section>

        {/* TODO (FR): Feedback téléchargement */}
        {/* {isDownloading && <Spinner />} */}
      </main>
    </div>
  );
}

