"use client";

/**
 * Page 4 : Résultats
 * 
 * FR: Synthèse et téléchargement du rapport Word
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { downloadReport } from "@/lib/api-client";

export default function ResultsPage() {
  const router = useRouter();
  const {
    threadId,
    validatedNeeds,
    validatedQuickWins,
    validatedStructurationIA,
    reset,
  } = useStore();

  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // FR: Vérifier qu'on a bien des données
  useEffect(() => {
    if (validatedNeeds.length === 0) {
      router.push('/');
    }
  }, [validatedNeeds, router]);

  // FR: Télécharger le rapport
  const handleDownload = async () => {
    if (!threadId) return;

    setIsDownloading(true);
    setError(null);

    try {
      const blob = await downloadReport(
        validatedNeeds,
        validatedQuickWins,
        validatedStructurationIA,
        threadId
      );

      // FR: Créer un lien de téléchargement
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `rapport-besoins-${Date.now()}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Erreur téléchargement:', err);
      setError(err.message || "Erreur lors du téléchargement");
    } finally {
      setIsDownloading(false);
    }
  };

  // FR: Recommencer
  const handleReset = () => {
    reset();
    router.push('/');
  };

  if (validatedNeeds.length === 0) {
    return null; // Redirect en cours
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-8 py-8">
        {/* FR: Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            📄 Résultats
          </h1>
          <p className="text-lg text-gray-600">
            Synthèse de votre analyse et téléchargement du rapport
          </p>
        </div>
        {/* FR: Erreur */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            ⚠️ {error}
          </div>
        )}

        {/* FR: Synthèse */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-6">📊 Synthèse de votre analyse</h2>

          {/* FR: Besoins validés */}
          <section className="mb-6">
            <h3 className="text-lg font-semibold mb-3 text-blue-900">
              💡 Besoins sélectionnés ({validatedNeeds.length})
            </h3>
            <ul className="space-y-2">
              {validatedNeeds.map((need) => (
                <li key={need.id} className="pl-4 border-l-4 border-blue-500">
                  <p className="font-semibold">{need.title}</p>
                  <p className="text-sm text-gray-600">
                    {need.citations.length} citations
                  </p>
                </li>
              ))}
            </ul>
          </section>

          {/* FR: Quick Wins */}
          {validatedQuickWins.length > 0 && (
            <section className="mb-6">
              <h3 className="text-lg font-semibold mb-3 text-green-900">
                ⚡ Quick Wins ({validatedQuickWins.length})
              </h3>
              <ul className="space-y-2">
                {validatedQuickWins.map((uc) => (
                  <li key={uc.id} className="pl-4 border-l-4 border-green-500">
                    <p className="font-semibold">{uc.title}</p>
                    <p className="text-sm text-gray-600">{uc.description}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {uc.ai_technologies.map((tech, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* FR: Structuration IA */}
          {validatedStructurationIA.length > 0 && (
            <section className="mb-6">
              <h3 className="text-lg font-semibold mb-3 text-purple-900">
                🏗️ Structuration IA ({validatedStructurationIA.length})
              </h3>
              <ul className="space-y-2">
                {validatedStructurationIA.map((uc) => (
                  <li key={uc.id} className="pl-4 border-l-4 border-purple-500">
                    <p className="font-semibold">{uc.title}</p>
                    <p className="text-sm text-gray-600">{uc.description}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {uc.ai_technologies.map((tech, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* FR: Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">📥 Téléchargement du rapport</h3>
          <p className="text-gray-600 mb-6">
            Cliquez sur le bouton ci-dessous pour télécharger un rapport Word contenant
            tous les besoins et cas d'usage sélectionnés.
          </p>

          <div className="flex gap-4">
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-2"
            >
              {isDownloading ? (
                <>
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Téléchargement...
                </>
              ) : (
                <>
                  📥 Télécharger le rapport Word
                </>
              )}
            </button>

            <button
              onClick={handleReset}
              className="bg-gray-200 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
            >
              🔄 Nouvelle analyse
            </button>
          </div>
        </div>

        {/* FR: Retour */}
        <div className="mt-6">
          <button
            onClick={() => router.push('/usecases')}
            className="text-gray-600 hover:text-gray-800"
          >
            ← Retour aux cas d'usage
          </button>
        </div>
      </main>
    </div>
  );
}
