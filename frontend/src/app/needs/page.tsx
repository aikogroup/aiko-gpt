"use client";

/**
 * Page 2 : Besoins
 * 
 * FR: Afficher, éditer et sélectionner les 10 besoins générés
 * 
 * Éléments :
 * - Liste de 10 besoins (cartes)
 * - Chaque besoin :
 *   - Checkbox (sélection)
 *   - Titre éditable
 *   - 5 citations (Excel + PDF/JSON)
 * - Besoins sélectionnés remontent en haut
 * - Champ commentaire (consignes pour régénération)
 * - Bouton "Générer" → génère de nouveaux besoins différents
 * - Bouton "Valider" → passe à page 3 (cas d'usage)
 */

import { useState } from "react";
// TODO (FR): Importer les composants nécessaires
// import NeedCard from "@/components/NeedCard";
// import Spinner from "@/components/Spinner";
// import { useStore } from "@/lib/store";

export default function NeedsPage() {
  // TODO (FR): Récupérer les besoins depuis le state global (Zustand)
  // const { needs, setNeeds } = useStore();

  // TODO (FR): États locaux
  // const [comment, setComment] = useState<string>("");
  // const [isLoading, setIsLoading] = useState<boolean>(false);

  // TODO (FR): Fonction handleNeedSelect(needId: string)
  // - Marquer le besoin comme sélectionné/déselectionné
  // - Mettre à jour le state global

  // TODO (FR): Fonction handleNeedEdit(needId: string, newTitle: string)
  // - Mettre à jour le titre du besoin
  // - Marquer comme édité
  // - Mettre à jour le state global

  // TODO (FR): Fonction handleGenerate()
  // - Récupérer les besoins non sélectionnés (excluded_needs)
  // - Appeler POST /api/run avec action "regenerate_needs"
  // - Inclure le commentaire utilisateur
  // - Mettre à jour le state global avec les nouveaux besoins

  // TODO (FR): Fonction handleValidate()
  // - Vérifier qu'au moins 5 besoins sont sélectionnés
  // - Sauvegarder les besoins validés dans le state global
  // - Naviguer vers /usecases

  // TODO (FR): Trier les besoins (sélectionnés en premier)
  // const sortedNeeds = [...needs].sort((a, b) => {
  //   if (a.selected && !b.selected) return -1;
  //   if (!a.selected && b.selected) return 1;
  //   return 0;
  // });

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Besoins Identifiés</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* TODO (FR): Liste des besoins */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">
            Sélectionnez les besoins pertinents (minimum 5)
          </h2>
          
          {/* TODO (FR): Mapper les besoins triés */}
          <div className="space-y-4">
            {/* {sortedNeeds.map(need => (
              <NeedCard
                key={need.id}
                need={need}
                onSelect={handleNeedSelect}
                onEdit={handleNeedEdit}
              />
            ))} */}
            <p className="text-gray-600">TODO: Afficher les cartes de besoins</p>
          </div>
        </section>

        {/* TODO (FR): Champ commentaire */}
        <section className="mb-6">
          <h3 className="text-lg font-semibold mb-2">
            Commentaire pour la régénération (optionnel)
          </h3>
          <textarea
            placeholder="Ex: Je souhaite des besoins plus axés sur la productivité..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            rows={3}
            // TODO (FR): Lier à l'état comment
          />
        </section>

        {/* TODO (FR): Boutons d'action */}
        <section className="flex gap-4">
          <button
            className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700"
            // TODO (FR): Lier à handleGenerate
          >
            Générer de nouveaux besoins
          </button>
          
          <button
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
            // TODO (FR): Lier à handleValidate
          >
            Valider et passer aux cas d'usage
          </button>
        </section>

        {/* TODO (FR): Loader */}
        {/* {isLoading && <Spinner />} */}
      </main>
    </div>
  );
}

