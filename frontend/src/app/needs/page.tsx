"use client";

/**
 * Page 2 : Besoins
 * 
 * FR: Afficher, éditer et sélectionner les 10 besoins générés
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStore, getSelectedNeeds } from "@/lib/store";
import { regenerateNeeds } from "@/lib/api-client";

export default function NeedsPage() {
  const router = useRouter();
  const {
    threadId,
    needs,
    error,
    setNeeds,
    toggleNeedSelection,
    updateNeedTitle,
    setValidatedNeeds,
    setCurrentStep,
    setLoading,
    setError,
  } = useStore();

  const [comment, setComment] = useState<string>("");
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // FR: Vérifier qu'on a bien des besoins
  useEffect(() => {
    if (needs.length === 0) {
      router.push('/');
    }
  }, [needs, router]);

  // FR: Compter les besoins sélectionnés
  const selectedCount = needs.filter(n => n.selected).length;

  // FR: Tri par sélection (sélectionnés en haut)
  const sortedNeeds = [...needs].sort((a, b) => {
    if (a.selected && !b.selected) return -1;
    if (!a.selected && b.selected) return 1;
    return 0;
  });

  // FR: Régénérer les besoins
  const handleRegenerate = async () => {
    if (!threadId) return;

    setIsRegenerating(true);
    setError(null);

    try {
      // FR: Exclure les besoins non sélectionnés
      const excludedTitles = needs
        .filter(n => !n.selected)
        .map(n => n.title);

      const { needs: newNeeds } = await regenerateNeeds(
        {
          excluded_needs: excludedTitles,
          user_comment: comment || undefined,
          action: 'regenerate_needs',
        },
        threadId
      );

      setNeeds(newNeeds);
      setComment("");
      // FR: S'assurer qu'on reste sur la page des besoins
      setCurrentStep('needs');
      // FR: Message de confirmation
      setError(null);
      setSuccessMessage("✅ Besoins régénérés avec succès !");
      // FR: Effacer le message après 3 secondes
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      console.error('Erreur régénération:', err);
      setError(err.message || "Erreur lors de la régénération");
    } finally {
      setIsRegenerating(false);
    }
  };

  // FR: Valider et passer aux cas d'usage
  const handleValidate = () => {
    if (selectedCount < 5) {
      setError("Veuillez sélectionner au moins 5 besoins");
      return;
    }

    const validated = needs.filter(n => n.selected);
    setValidatedNeeds(validated);
    setCurrentStep('usecases');
    router.push('/usecases');
  };


  if (needs.length === 0) {
    return null; // Redirect en cours
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-8 py-8">
        {/* FR: Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            💡 Sélection des besoins
          </h1>
          <p className="text-lg text-gray-600">
            {selectedCount}/10 besoins sélectionnés
          </p>
        </div>

        {/* FR: Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-blue-900">
            ✅ <strong>Sélectionnez au moins 5 besoins</strong> parmi les 10 proposés. Vous pouvez modifier les titres si nécessaire.
          </p>
        </div>

        {/* FR: Messages de feedback */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            ⚠️ {error}
          </div>
        )}
        
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMessage}
          </div>
        )}

        {/* FR: Liste des besoins */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', marginBottom: '32px' }}>
          {sortedNeeds.map((need) => (
            <div
              key={need.id}
              style={{
                backgroundColor: need.selected ? '#eff6ff' : 'white',
                borderRadius: '16px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                border: `2px solid ${need.selected ? '#3b82f6' : '#e5e7eb'}`,
                padding: '24px',
                transition: 'all 0.2s',
              }}
            >
              {/* FR: Flex container : Checkbox + Contenu */}
              <div style={{ display: 'flex', gap: '16px' }}>
                {/* FR: Checkbox fixe à gauche */}
                <div style={{ flexShrink: 0, paddingTop: '8px' }}>
                  <input
                    type="checkbox"
                    checked={need.selected}
                    onChange={() => toggleNeedSelection(need.id)}
                    style={{
                      width: '20px',
                      height: '20px',
                      cursor: 'pointer',
                      accentColor: '#3b82f6'
                    }}
                  />
                </div>
                
                {/* FR: Contenu flexible à droite */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* FR: Titre - GRANDE ZONE MODIFIABLE */}
                  <textarea
                    value={need.title}
                    onChange={(e) => updateNeedTitle(need.id, e.target.value)}
                    placeholder="Décrivez le besoin métier de manière détaillée..."
                    style={{
                      width: '100%',
                      minHeight: '150px',
                      padding: '16px',
                      fontSize: '18px',
                      fontWeight: '600',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      resize: 'vertical',
                      fontFamily: 'inherit',
                      lineHeight: '1.6',
                      marginBottom: '16px'
                    }}
                    rows={5}
                  />
                  
                  {need.edited && (
                    <div style={{ fontSize: '12px', color: '#ea580c', marginBottom: '16px' }}>
                      ✏️ Modifié
                    </div>
                  )}

                  {/* FR: Citations */}
                  <div>
                    <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#374151' }}>
                      Citations sources ({need.citations.length}) :
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {need.citations.map((citation, idx) => (
                        <div
                          key={idx}
                          style={{
                            fontSize: '14px',
                            color: '#4b5563',
                            backgroundColor: '#f9fafb',
                            padding: '16px',
                            borderRadius: '8px',
                            borderLeft: '4px solid #93c5fd',
                          }}
                        >
                          {citation}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* FR: Régénération */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-3">
            🔄 Régénérer des besoins
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Décochez les besoins que vous ne souhaitez pas conserver, puis cliquez sur "Régénérer".
          </p>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Commentaire optionnel pour guider la régénération..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4"
            rows={3}
          />
          <button
            onClick={handleRegenerate}
            disabled={isRegenerating || selectedCount === 10}
            className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            {isRegenerating ? 'Régénération...' : '🔄 Régénérer'}
          </button>
        </div>

        {/* FR: Actions */}
        <div className="flex justify-between items-center">
          <button
            onClick={() => router.push('/')}
            className="text-gray-600 hover:text-gray-800"
          >
            ← Retour
          </button>
          <button
            onClick={handleValidate}
            disabled={selectedCount < 5}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            Valider ({selectedCount} sélectionnés) →
          </button>
        </div>
      </main>
    </div>
  );
}
