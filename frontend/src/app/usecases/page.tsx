"use client";

/**
 * Page 3 : Cas d'usage
 * 
 * FR: Afficher et sélectionner les Quick Wins + Structuration IA
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStore, getSelectedUseCases } from "@/lib/store";
import { generateUseCases, regenerateUseCases } from "@/lib/api-client";
import { LLMLogViewer } from "@/components/LLMLogViewer";

export default function UseCasesPage() {
  const router = useRouter();
  const {
    threadId,
    validatedNeeds,
    quickWins,
    structurationIA,
    setQuickWins,
    setStructurationIA,
    toggleUseCaseSelection,
    setValidatedQuickWins,
    setValidatedStructurationIA,
    setCurrentStep,
    setLoading,
    setError,
  } = useStore();

  const [comment, setComment] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);
  const [showLogs, setShowLogs] = useState<boolean>(false);

  // FR: Générer les cas d'usage au chargement
  useEffect(() => {
    if (validatedNeeds.length < 5) {
      router.push('/needs');
      return;
    }

    if (quickWins.length === 0 && structurationIA.length === 0 && !isLoading) {
      generateInitialUseCases();
    }
  }, [validatedNeeds]);

  const generateInitialUseCases = async () => {
    if (!threadId) return;

    setIsLoading(true);
    setShowLogs(true); // FR: Afficher les logs
    setError(null);

    try {
      const { quick_wins, structuration_ia } = await generateUseCases(
        {
          validated_needs: validatedNeeds,
          action: 'generate_use_cases',
        },
        threadId
      );

      setQuickWins(quick_wins);
      setStructurationIA(structuration_ia);
    } catch (err: any) {
      console.error('Erreur génération:', err);
      setError(err.message || "Erreur lors de la génération");
    } finally {
      setIsLoading(false);
      setShowLogs(false); // FR: Masquer les logs
    }
  };

  // FR: Compter les sélectionnés
  const selectedQW = quickWins.filter(uc => uc.selected).length;
  const selectedSIA = structurationIA.filter(uc => uc.selected).length;

  // FR: Tri par sélection (sélectionnés en haut)
  const sortedQuickWins = [...quickWins].sort((a, b) => {
    if (a.selected && !b.selected) return -1;
    if (!a.selected && b.selected) return 1;
    return 0;
  });

  const sortedStructurationIA = [...structurationIA].sort((a, b) => {
    if (a.selected && !b.selected) return -1;
    if (!a.selected && b.selected) return 1;
    return 0;
  });

  // FR: Régénérer
  const handleRegenerate = async () => {
    if (!threadId) return;

    setIsRegenerating(true);
    setShowLogs(true); // FR: Afficher les logs
    setError(null);

    try {
      const { quick_wins, structuration_ia } = await regenerateUseCases(
        {
          validated_quick_wins: quickWins.filter(uc => uc.selected),
          validated_structuration_ia: structurationIA.filter(uc => uc.selected),
          user_comment: comment || undefined,
          action: 'regenerate_use_cases',
        },
        threadId
      );

      // FR: Logique intelligente : si >= 5 validés, ne pas régénérer cette catégorie
      if (selectedQW < 5) {
        setQuickWins(quick_wins);
      }
      if (selectedSIA < 5) {
        setStructurationIA(structuration_ia);
      }

      setComment("");
    } catch (err: any) {
      console.error('Erreur régénération:', err);
      setError(err.message || "Erreur lors de la régénération");
    } finally {
      setIsRegenerating(false);
      setShowLogs(false); // FR: Masquer les logs
    }
  };

  // FR: Valider et passer aux résultats
  const handleValidate = () => {
    const validatedQW = quickWins.filter(uc => uc.selected);
    const validatedSIA = structurationIA.filter(uc => uc.selected);

    setValidatedQuickWins(validatedQW);
    setValidatedStructurationIA(validatedSIA);
    setCurrentStep('results');
    router.push('/results');
  };

  // FR: Fonctions de modification des cas d'usage
  const updateUseCaseTitle = (id: string, category: 'quick_win' | 'structuration_ia', newTitle: string) => {
    if (category === 'quick_win') {
      setQuickWins(quickWins.map(uc => uc.id === id ? { ...uc, title: newTitle } : uc));
    } else {
      setStructurationIA(structurationIA.map(uc => uc.id === id ? { ...uc, title: newTitle } : uc));
    }
  };

  const updateUseCaseDescription = (id: string, category: 'quick_win' | 'structuration_ia', newDescription: string) => {
    if (category === 'quick_win') {
      setQuickWins(quickWins.map(uc => uc.id === id ? { ...uc, description: newDescription } : uc));
    } else {
      setStructurationIA(structurationIA.map(uc => uc.id === id ? { ...uc, description: newDescription } : uc));
    }
  };

  const updateUseCaseTechnologies = (id: string, category: 'quick_win' | 'structuration_ia', newTechnologies: string) => {
    const techArray = newTechnologies.split(',').map(t => t.trim()).filter(t => t.length > 0);
    if (category === 'quick_win') {
      setQuickWins(quickWins.map(uc => uc.id === id ? { ...uc, ai_technologies: techArray } : uc));
    } else {
      setStructurationIA(structurationIA.map(uc => uc.id === id ? { ...uc, ai_technologies: techArray } : uc));
    }
  };

  if (validatedNeeds.length < 5) {
    return null; // Redirect en cours
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-8 py-8">
        {/* FR: Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🎯 Sélection des cas d'usage
          </h1>
          <p className="text-lg text-gray-600">
            {selectedQW + selectedSIA} cas d'usage sélectionnés
          </p>
        </div>

        {/* FR: Loader initial */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Génération des cas d'usage en cours...</p>
          </div>
        )}

        {!isLoading && (
          <>
            {/* FR: Section Quick Wins */}
            <section className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">⚡ Quick Wins ({selectedQW}/8)</h2>
                <span className="text-sm text-gray-600">ROI &lt; 3 mois</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '32px' }}>
                {sortedQuickWins.map((uc) => (
                  <div
                    key={uc.id}
                    style={{
                      backgroundColor: uc.selected ? '#f0fdf4' : 'white',
                      borderRadius: '16px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      border: `2px solid ${uc.selected ? '#22c55e' : '#e5e7eb'}`,
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
                          checked={uc.selected}
                          onChange={() => toggleUseCaseSelection(uc.id, 'quick_win')}
                          style={{
                            width: '20px',
                            height: '20px',
                            cursor: 'pointer',
                            accentColor: '#22c55e'
                          }}
                        />
                      </div>
                      
                      {/* FR: Contenu flexible à droite */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        {/* FR: Titre */}
                        <input
                          type="text"
                          value={uc.title}
                          onChange={(e) => updateUseCaseTitle(uc.id, 'quick_win', e.target.value)}
                          placeholder="Titre du cas d'usage..."
                          style={{
                            width: '100%',
                            padding: '16px',
                            fontSize: '18px',
                            fontWeight: '700',
                            border: '1px solid #d1d5db',
                            borderRadius: '8px',
                            fontFamily: 'inherit',
                            marginBottom: '16px'
                          }}
                        />

                        {/* FR: Description */}
                        <div style={{ marginBottom: '16px' }}>
                          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#374151' }}>
                            Description :
                          </label>
                          <textarea
                            value={uc.description}
                            onChange={(e) => updateUseCaseDescription(uc.id, 'quick_win', e.target.value)}
                            placeholder="Description détaillée du cas d'usage..."
                            style={{
                              width: '100%',
                              minHeight: '120px',
                              padding: '12px',
                              fontSize: '14px',
                              border: '1px solid #d1d5db',
                              borderRadius: '8px',
                              resize: 'vertical',
                              fontFamily: 'inherit',
                              lineHeight: '1.5'
                            }}
                            rows={4}
                          />
                        </div>

                        {/* FR: Technologies */}
                        <div>
                          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#374151' }}>
                            Technologies IA :
                          </label>
                          <input
                            type="text"
                            value={uc.ai_technologies.join(', ')}
                            onChange={(e) => updateUseCaseTechnologies(uc.id, 'quick_win', e.target.value)}
                            placeholder="LLM, RAG, OCR, ML..."
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              fontSize: '14px',
                              border: '1px solid #d1d5db',
                              borderRadius: '8px',
                              fontFamily: 'inherit',
                              marginBottom: '12px'
                            }}
                          />
                          {/* FR: Affichage des technologies */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {uc.ai_technologies.map((tech, idx) => (
                              <span
                                key={idx}
                                style={{
                                  padding: '4px 12px',
                                  backgroundColor: '#dcfce7',
                                  color: '#166534',
                                  borderRadius: '16px',
                                  fontSize: '12px',
                                  fontWeight: '600'
                                }}
                              >
                                {tech}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* FR: Section Structuration IA */}
            <section className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">🏗️ Structuration IA ({selectedSIA}/10)</h2>
                <span className="text-sm text-gray-600">ROI 3-12 mois</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '32px' }}>
                {sortedStructurationIA.map((uc) => (
                  <div
                    key={uc.id}
                    style={{
                      backgroundColor: uc.selected ? '#faf5ff' : 'white',
                      borderRadius: '16px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      border: `2px solid ${uc.selected ? '#a855f7' : '#e5e7eb'}`,
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
                          checked={uc.selected}
                          onChange={() => toggleUseCaseSelection(uc.id, 'structuration_ia')}
                          style={{
                            width: '20px',
                            height: '20px',
                            cursor: 'pointer',
                            accentColor: '#a855f7'
                          }}
                        />
                      </div>
                      
                      {/* FR: Contenu flexible à droite */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        {/* FR: Titre */}
                        <input
                          type="text"
                          value={uc.title}
                          onChange={(e) => updateUseCaseTitle(uc.id, 'structuration_ia', e.target.value)}
                          placeholder="Titre du cas d'usage..."
                          style={{
                            width: '100%',
                            padding: '16px',
                            fontSize: '18px',
                            fontWeight: '700',
                            border: '1px solid #d1d5db',
                            borderRadius: '8px',
                            fontFamily: 'inherit',
                            marginBottom: '16px'
                          }}
                        />

                        {/* FR: Description */}
                        <div style={{ marginBottom: '16px' }}>
                          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#374151' }}>
                            Description :
                          </label>
                          <textarea
                            value={uc.description}
                            onChange={(e) => updateUseCaseDescription(uc.id, 'structuration_ia', e.target.value)}
                            placeholder="Description détaillée du cas d'usage..."
                            style={{
                              width: '100%',
                              minHeight: '120px',
                              padding: '12px',
                              fontSize: '14px',
                              border: '1px solid #d1d5db',
                              borderRadius: '8px',
                              resize: 'vertical',
                              fontFamily: 'inherit',
                              lineHeight: '1.5'
                            }}
                            rows={4}
                          />
                        </div>

                        {/* FR: Technologies */}
                        <div>
                          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#374151' }}>
                            Technologies IA :
                          </label>
                          <input
                            type="text"
                            value={uc.ai_technologies.join(', ')}
                            onChange={(e) => updateUseCaseTechnologies(uc.id, 'structuration_ia', e.target.value)}
                            placeholder="LLM, RAG, OCR, ML..."
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              fontSize: '14px',
                              border: '1px solid #d1d5db',
                              borderRadius: '8px',
                              fontFamily: 'inherit',
                              marginBottom: '12px'
                            }}
                          />
                          {/* FR: Affichage des technologies */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {uc.ai_technologies.map((tech, idx) => (
                              <span
                                key={idx}
                                style={{
                                  padding: '4px 12px',
                                  backgroundColor: '#f3e8ff',
                                  color: '#7e22ce',
                                  borderRadius: '16px',
                                  fontSize: '12px',
                                  fontWeight: '600'
                                }}
                              >
                                {tech}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* FR: Régénération */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-3">🔄 Régénérer des cas d'usage</h3>
              <p className="text-sm text-gray-600 mb-4">
                Si ≥ 5 cas sont sélectionnés dans une catégorie, elle ne sera pas régénérée.
              </p>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Commentaire optionnel..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4"
                rows={3}
              />
              <button
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 disabled:bg-gray-300 transition"
              >
                {isRegenerating ? 'Régénération...' : '🔄 Régénérer'}
              </button>
            </div>

            {/* FR: Actions */}
            <div className="flex justify-between items-center">
              <button
                onClick={() => router.push('/needs')}
                className="text-gray-600 hover:text-gray-800"
              >
                ← Retour
              </button>
              <button
                onClick={handleValidate}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Générer le rapport →
              </button>
            </div>
          </>
        )}
      </main>

      {/* FR: Popup de logs LLM */}
      <LLMLogViewer 
        isVisible={showLogs} 
        onClose={() => setShowLogs(false)}
        type="usecases"
      />
    </div>
  );
}
