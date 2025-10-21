"use client";

/**
 * Page 3 : Cas d'usage
 * 
 * FR: Générer et sélectionner les cas d'usage
 * 
 * Éléments :
 * - Section Quick Wins (8 cas d'usage)
 * - Section Structuration IA (10 cas d'usage)
 * - Chaque cas d'usage :
 *   - Bouton sélection
 *   - Titre
 *   - Description
 *   - Technologies IA (LLM, RAG, OCR, etc.)
 * - Champ commentaire
 * - Bouton "Générer" → complète catégories manquantes
 * - Bouton "Valider" → passe à page 4 (résultats)
 * 
 * ⚠️ Règle intelligente : Si ≥ 5 validés dans une catégorie → ne régénère rien
 */

import { useState } from "react";
// TODO (FR): Importer composants
// import UseCaseCard from "@/components/UseCaseCard";
// import Spinner from "@/components/Spinner";
// import { useStore } from "@/lib/store";

export default function UseCasesPage() {
  // TODO (FR): Récupérer depuis state global
  // const { quickWins, structurationIA, setQuickWins, setStructurationIA } = useStore();

  // TODO (FR): États locaux
  // const [comment, setComment] = useState<string>("");
  // const [isLoading, setIsLoading] = useState<boolean>(false);

  // TODO (FR): Fonction handleUseCaseSelect()
  // TODO (FR): Fonction handleGenerate()
  // - Vérifier si QW validés >= 5 et SIA validés >= 5
  // - Si oui, ne rien faire
  // - Sinon, appeler /api/run avec action "regenerate_use_cases"

  // TODO (FR): Fonction handleValidate()
  // - Naviguer vers /results

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Cas d'Usage IA</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* TODO (FR): Section Quick Wins */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">
            Quick Wins (ROI {'<'} 3 mois)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* TODO (FR): Mapper quickWins */}
            <p className="text-gray-600">TODO: Afficher Quick Wins</p>
          </div>
        </section>

        {/* TODO (FR): Section Structuration IA */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">
            Structuration IA (ROI 3-12 mois)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* TODO (FR): Mapper structurationIA */}
            <p className="text-gray-600">TODO: Afficher Structuration IA</p>
          </div>
        </section>

        {/* TODO (FR): Champ commentaire */}
        <section className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Commentaire (optionnel)</h3>
          <textarea
            placeholder="Ex: Plus de cas d'usage sur l'automatisation..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            rows={3}
          />
        </section>

        {/* TODO (FR): Boutons */}
        <section className="flex gap-4">
          <button className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700">
            Compléter les catégories
          </button>
          <button className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700">
            Valider et voir les résultats
          </button>
        </section>
      </main>
    </div>
  );
}

