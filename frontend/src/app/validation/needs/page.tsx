"use client";
import { useEffect, useState } from "react";
import { getThreadState, sendNeedsValidation, regenerateNeeds, LANGGRAPH_API_URL } from "@/lib/api-client";
import { Spinner } from "@/components/Spinner";
import { useRouter } from "next/navigation";
import { useUiStore } from "@/lib/store";
import { LoadingModal } from "@/components/LoadingModal";
import { useLoadingModal } from "@/hooks/useLoadingModal";

export default function NeedsValidationPage() {
  const router = useRouter();
  const { isBusy, setIsBusy, setPhase, selectedNeeds, setSelectedNeeds } = useUiStore();
  const { loadingState, showLoading, addLog, hideLoading, elapsedTime, formatElapsedTime } = useLoadingModal();
  const [needs, setNeeds] = useState<any[]>([]);
  const [selected, setSelected] = useState<Record<number, boolean>>({});
  const [persistedSelected, setPersistedSelected] = useState<any[]>([]);
  const [comment, setComment] = useState("");
  const [statusMsg, setStatusMsg] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [validatedCount, setValidatedCount] = useState<number>(0); // cumul: backend + sélection locale
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  useEffect(() => {
    (async () => {
      // Attendre que les besoins soient disponibles
      let attempts = 0;
      const maxAttempts = 60; // 60 secondes max
      
      while (attempts < maxAttempts) {
        try {
          console.log(`🔍 [DEBUG] Tentative ${attempts + 1}/${maxAttempts} - Récupération de l'état...`);
          const state = await getThreadState();
          console.log("🔍 [DEBUG] État reçu:", state);
          
          // Vérifier plusieurs structures possibles
          const identified = state?.state?.values?.identified_needs || 
                           state?.values?.identified_needs || 
                           state?.identified_needs || 
                           [];
          
          console.log("🔍 [DEBUG] Besoins identifiés:", identified.length);
          
          if (identified.length > 0) {
            console.log("✅ Besoins identifiés disponibles:", identified.length);
            const validatedList = state?.state?.values?.validated_needs ?? [];
            const backendCount = Array.isArray(validatedList) ? validatedList.length : 0;
            
            setNeeds(identified);
            setValidatedCount(backendCount + persistedSelected.length);
            console.debug("[Needs] initial state", { backendCount, persistedLocal: persistedSelected.length, total: backendCount + persistedSelected.length, identifiedCount: identified.length, state });
            return;
          }
          
          attempts++;
          await new Promise(resolve => setTimeout(resolve, 2000)); // Attendre 2 secondes
        } catch (error) {
          console.error("❌ [DEBUG] Erreur lors de la vérification:", error);
          attempts++;
          await new Promise(resolve => setTimeout(resolve, 2000)); // Attendre 2 secondes
        }
      }
      
      console.error("❌ [DEBUG] Timeout: Aucun besoin identifié après", maxAttempts, "tentatives");
    })();
  }, []);

  const toggle = (idx: number) => setSelected((s) => ({ ...s, [idx]: !s[idx] }));

  // Fonction pour régénérer des besoins
  // Fonctions pour la réorganisation automatique
  const handleNeedToggle = (index: number) => {
    const isSelected = !!selected[index];
    const need = needs[index];
    
    if (!isSelected) {
      // Sélectionner : ajouter en haut de persistedSelected
      setPersistedSelected(prev => [need, ...prev]);
      setSelected(prev => ({ ...prev, [index]: true }));
    } else {
      // Désélectionner : retirer de persistedSelected
      setPersistedSelected(prev => prev.filter(n => n !== need));
      setSelected(prev => ({ ...prev, [index]: false }));
    }
  };

  const handlePersistedDeselect = (index: number) => {
    const need = persistedSelected[index];
    
    // Retirer de persistedSelected
    setPersistedSelected(prev => prev.filter((_, idx) => idx !== index));
    
    // Décocher dans la liste normale
    const needIndex = needs.findIndex(n => n === need);
    if (needIndex !== -1) {
      setSelected(prev => ({ ...prev, [needIndex]: false }));
    }
  };

  const handleRegenerate = async () => {
    // Afficher la popup de chargement
    showLoading("Régénération des besoins", [
      "Préparation de la régénération...",
      "Envoi des besoins sélectionnés...",
      "Génération de nouveaux besoins..."
    ]);
    
    setIsRegenerating(true);
    setIsBusy(true);
    setStatusMsg("Régénération des besoins...");
    
    try {
      addLog("Sélection des besoins à conserver...");
      // Garder les besoins sélectionnés (éviter les doublons)
      const selectedNeeds = needs.filter((_, i) => selected[i]);
      setPersistedSelected(prev => {
        const existingTitles = new Set(prev.map(p => p.theme));
        const newNeeds = selectedNeeds.filter(n => !existingTitles.has(n.theme));
        return [...prev, ...newNeeds];
      });
      
      addLog("Envoi de la demande de régénération...");
      // Appeler l'API pour régénérer
      const result = await regenerateNeeds({
        validated_needs: selectedNeeds,
        rejected_needs: needs.filter((_, i) => !selected[i]),
        user_feedback: comment,
      });
      
      console.log('✅ [DEBUG] Résultat régénération:', result);
      addLog("Régénération envoyée avec succès");
      addLog("Attente des nouveaux besoins...");
      setStatusMsg("Nouveaux besoins générés.");
      
      // Attendre un peu pour que le workflow se termine
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Recharger les besoins avec polling
      let attempts = 0;
      const maxAttempts = 30; // 30 secondes max
      
      while (attempts < maxAttempts) {
        try {
          console.log(`🔄 [DEBUG] Tentative ${attempts + 1}/${maxAttempts} - Récupération des nouveaux besoins...`);
          const state = await getThreadState();
          console.log("🔄 [DEBUG] État reçu:", state);
          
          const newNeeds = state?.state?.values?.identified_needs || 
                          state?.values?.identified_needs || 
                          state?.identified_needs || [];
          
          console.log("🔄 [DEBUG] Nouveaux besoins:", newNeeds.length);
          
          if (newNeeds.length > 0) {
            console.log("✅ Nouveaux besoins disponibles:", newNeeds.length);
            addLog(`Nouveaux besoins générés: ${newNeeds.length}`);
            setNeeds(newNeeds);
            setSelected({}); // Reset selection
            setComment("");
            hideLoading();
            return;
          }
          
          attempts++;
          await new Promise(resolve => setTimeout(resolve, 1000)); // Attendre 1 seconde
        } catch (error) {
          console.error("❌ [DEBUG] Erreur lors de la vérification:", error);
          attempts++;
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      console.error("❌ [DEBUG] Timeout: Aucun nouveau besoin après", maxAttempts, "tentatives");
      addLog("Timeout: Aucun nouveau besoin généré");
      
    } catch (error) {
      console.error('❌ Erreur régénération:', error);
      addLog(`Erreur: ${error instanceof Error ? error.message : String(error)}`);
      setStatusMsg("Erreur lors de la régénération.");
    } finally {
      setIsRegenerating(false);
      setIsBusy(false);
      hideLoading();
    }
  };

    // Fonction pour valider et passer aux cas d'usage
    const handleValidate = async () => {
      // Afficher la popup de chargement
      showLoading("Validation des besoins", [
        "Préparation de la validation...",
        "Envoi des besoins sélectionnés...",
        "Génération des cas d'usage...",
        "🤖 Modèle IA utilisé: gpt-4o-mini"
      ]);
    
    setIsValidating(true);
    setIsBusy(true);
    setStatusMsg("Validation des besoins sélectionnés...");
    
    try {
      const validated = needs.filter((_, i) => selected[i]);
      const rejected = needs.filter((_, i) => !selected[i]);
      
      if (validated.length === 0) {
        addLog("Erreur: Aucun besoin sélectionné");
        setStatusMsg("Veuillez sélectionner au moins un besoin.");
        hideLoading();
        return;
      }
      
          addLog(`Validation de ${validated.length} besoins...`);
          console.log('🔍 [DEBUG] Validation finale:', {
            validated: validated.length,
            rejected: rejected.length,
            comment: comment
          });
          
          // Sauvegarder les besoins sélectionnés dans le store
          setSelectedNeeds(validated);
          
          addLog("Envoi de la validation...");
      const res = await sendNeedsValidation({
        validated_needs: validated,
        rejected_needs: rejected,
        user_feedback: [comment],
      });
      
      console.log('✅ [DEBUG] Résultat validation finale:', res);
      addLog("Validation envoyée avec succès");
      addLog("Attente de la génération des cas d'usage...");
      setStatusMsg("Validation envoyée. Attente de la génération des cas d'usage...");
      
      // Attendre que le workflow génère les use cases
      let attempts = 0;
      let redirected = false;
      const maxAttempts = 120; // 2 minutes max
      
        addLog("Démarrage de l'analyse des cas d'usage...");
        addLog("🤖 Modèle IA utilisé: gpt-4o-mini");
      
      while (attempts < maxAttempts && !redirected) {
        try {
          const state = await getThreadState();
          console.log('🔍 [DEBUG] État après validation:', state);

          // Vérifier l'état du workflow
          const workflowStatus = state?.status;
          const nextNodes = state?.next || [];
          
               // Traduire les états techniques en messages utilisateur
               let userMessage = "";
               if (state.next && state.next.includes('analyze_use_cases')) {
                 userMessage = "🤖 Génération des cas d'usage IA en cours...";
               } else if (state.next && state.next.includes('collect_data')) {
                 userMessage = "📊 Collecte des données d'ateliers et transcriptions...";
               } else if (state.next && state.next.includes('web_search')) {
                 userMessage = "🌐 Recherche d'informations sur l'entreprise avec Sonar...";
               } else if (state.next && state.next.includes('need_analysis')) {
                 userMessage = "🔍 Analyse des besoins métier...";
               } else if (state.status === 'running') {
                 userMessage = "⚙️ Traitement en cours...";
               } else if (state.status === 'pending') {
                 userMessage = "⏳ Initialisation du système...";
               } else if (workflowStatus === 'completed') {
                 userMessage = "✅ Traitement terminé";
               } else {
                 userMessage = "🔄 Vérification de l'avancement...";
               }
          
          // Afficher des logs informatifs toutes les 10 secondes
          if (attempts % 10 === 0) {
            addLog(userMessage);
            
            // Ajouter des détails techniques en mode debug si nécessaire
            if (nextNodes.length > 0) {
              const technicalDetails = nextNodes.map((node: any) => {
                switch(node) {
                  case 'analyze_use_cases': return 'Génération cas d\'usage';
                  case 'collect_data': return 'Collecte données';
                  case 'web_search': return 'Recherche web avec Sonar';
                  case 'need_analysis': return 'Analyse besoins';
                  case 'human_validation': return 'Préparation interface';
                  case 'validate_use_cases': return 'Validation cas d\'usage';
                  case 'workshop_agent': return 'Traitement Excel';
                  case 'transcript_agent': return 'Traitement PDF/JSON';
                  default: return node;
                }
              }).join(' → ');
              addLog(`📋 Étapes: ${technicalDetails}`);
            }
          }
          const quickWins = state?.values?.proposed_quick_wins || [];
          const structIa = state?.values?.proposed_structuration_ia || [];
          
          if (quickWins.length > 0 || structIa.length > 0) {
            console.log('✅ [DEBUG] Use cases générés:', { quickWins: quickWins.length, structIa: structIa.length });
            addLog(`✅ Cas d'usage générés: ${quickWins.length} Quick Wins, ${structIa.length} Structuration IA`);
            setStatusMsg("Cas d'usage générés. Redirection...");
            setPhase("usecases");
            hideLoading();
            router.push("/validation/use-cases");
            redirected = true;
            break;
          }
          
          // Vérifier aussi si le workflow est en pause pour les use cases
          if (state.next && state.next.includes('validate_use_cases')) {
            console.log('✅ [DEBUG] Workflow en pause pour validation des use cases');
            addLog("✅ Workflow en pause - Prêt pour validation des cas d'usage");
            setStatusMsg("Cas d'usage générés. Redirection...");
            setPhase("usecases");
            hideLoading();
            router.push("/validation/use-cases");
            redirected = true;
            break;
          }

          // NOUVEAU: Vérifier si le workflow est bloqué et forcer la génération des use cases
          if (attempts === 30) { // Après 30 secondes
            console.log('⚠️ [DEBUG] Workflow semble bloqué - Tentative de forcer la génération des use cases');
            addLog("⚠️ Workflow bloqué - Tentative de récupération...");
            
            // Essayer de déclencher manuellement la génération des use cases
            try {
              const forceResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${localStorage.getItem('current_thread_id') || 'default'}/runs`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  assistant_id: 'need_analysis',
                  input: {
                    force_use_case_generation: true,
                    validated_needs: validated,
                    rejected_needs: rejected,
                    user_feedback: comment
                  }
                })
              });
              
              if (forceResponse.ok) {
                addLog("🔄 Génération forcée des cas d'usage déclenchée...");
                await new Promise(resolve => setTimeout(resolve, 5000)); // Attendre 5 secondes
              }
            } catch (error) {
              console.error('❌ [DEBUG] Erreur lors de la génération forcée:', error);
              addLog("❌ Erreur lors de la récupération");
            }
          }
          
          attempts++;
          await new Promise((r) => setTimeout(r, 1000)); // Attendre 1 seconde
        } catch (error) {
        console.error('❌ [DEBUG] Erreur lors du polling:', error);
        addLog(`❌ Erreur de connexion: ${error instanceof Error ? error.message : String(error)}`);
        attempts++;
        await new Promise((r) => setTimeout(r, 1000));
        }
      }
      
      if (!redirected) {
        console.error(`❌ [DEBUG] Timeout: Aucun cas d'usage généré après ${maxAttempts} secondes`);
        addLog(`❌ Timeout après ${maxAttempts} secondes - Aucun cas d'usage généré`);
        setStatusMsg("Erreur: Aucun cas d'usage généré. Veuillez réessayer.");
      }
      
    } catch (error) {
      console.error('❌ Erreur validation:', error);
      addLog(`Erreur: ${error instanceof Error ? error.message : String(error)}`);
      setStatusMsg("Erreur lors de la validation.");
    } finally {
      setIsValidating(false);
      setIsBusy(false);
      hideLoading();
    }
  };

  const submit = async () => {
    setSubmitting(true);
    setIsBusy(true);
    const validated = needs.filter((_, i) => selected[i]);
    const rejected = needs.filter((_, i) => !selected[i]);
    // Mettre à jour l’affichage en haut: on cumule les validés
    setPersistedSelected((prev) => {
      // éviter doublons par theme
      const byTheme = new Set(prev.map((n) => n.theme));
      const unique = validated.filter((n) => !byTheme.has(n.theme));
      return [...prev, ...unique];
    });
    console.log('🔍 [DEBUG] Envoi validation:', {
      validated: validated.length,
      rejected: rejected.length,
      comment: comment
    });
    
    const res = await sendNeedsValidation({
      validated_needs: validated,
      rejected_needs: rejected,
      user_feedback: [comment],
    });
    
    console.log('✅ [DEBUG] Résultat validation:', res);
    setStatusMsg("Validation envoyée.");
    // Poll court: récupérer l'état à jour (jusqu'à 10s) pour éviter une latence backend
    try {
      let attempts = 0;
      let redirected = false;
      while (attempts < 10 && !redirected) {
        const state = await getThreadState();
        const identified = state?.values?.identified_needs || [];
        const validatedList = state?.validated_needs ?? state?.values?.validated_needs ?? [];
        const backendCount = Array.isArray(validatedList) ? validatedList.length : 0;
        const vCount = backendCount + persistedSelected.length;
        setNeeds(identified);
        setValidatedCount(vCount);
        console.debug("[Needs] poll state", { backendCount, persistedLocal: persistedSelected.length, total: vCount, identifiedCount: identified.length, attempts, state });
        if (vCount >= 5) {
          setStatusMsg("Validation terminée. Redirection vers les cas d'usage...");
          setPhase("usecases");
          router.push("/validation/use-cases");
          redirected = true;
          break;
        }
        // Attente 1s avant nouvelle tentative
        await new Promise((r) => setTimeout(r, 1000));
        attempts++;
      }
    } catch {}
    setSubmitting(false);
    setIsBusy(false);
  };

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-6 text-black">
      <h1 className="text-2xl font-semibold">Validation des besoins (5 minimum)</h1>
      <p className="text-sm text-gray-700">Besoins validés actuellement: <span className="font-semibold">{validatedCount}</span></p>
      {/* Bloc des besoins déjà sélectionnés en haut, avec option de désélection */}
      {persistedSelected.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-lg font-medium">Besoins sélectionnés</h2>
          <ul className="space-y-2">
            {persistedSelected.map((n, i) => (
              <li key={i} className="border rounded-md p-3 flex items-start gap-3">
                <input 
                  type="checkbox" 
                  checked={true} 
                  onChange={() => handlePersistedDeselect(i)}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium">{n.theme || "Thème"}</div>
                  {Array.isArray(n.quotes) && n.quotes.length > 0 && (
                    <ul className="list-disc pl-6 text-sm">
                      {n.quotes.map((q: string, qi: number) => <li key={qi}>{q}</li>)}
                    </ul>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      {needs.length === 0 ? (
        <p>Aucun besoin pour le moment. Revenez plus tard.</p>
      ) : (
        <div className="space-y-4">
          {needs.map((n, i) => {
            // Ne pas afficher les éléments déjà sélectionnés (ils sont dans persistedSelected)
            const isInPersisted = persistedSelected.some(p => p === n);
            if (isInPersisted) return null;
            
            return (
              <div key={i} className="border rounded-md p-4">
                <div className="flex items-center gap-3">
                  <input type="checkbox" disabled={submitting} checked={!!selected[i]} onChange={() => handleNeedToggle(i)} />
                  <h2 className="font-medium">{n.theme || "Thème"}</h2>
                </div>
                {Array.isArray(n.quotes) && n.quotes.length > 0 && (
                  <ul className="list-disc pl-6 mt-2">
                    {n.quotes.map((q: string, qi: number) => (
                      <li key={qi} className="text-sm">{q}</li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="space-y-2">
        <h3 className="font-medium">Commentaires (optionnel)</h3>
        <textarea disabled={submitting} value={comment} onChange={(e) => setComment(e.target.value)} className="w-full border rounded-md p-2 disabled:bg-gray-100" rows={4} />
      </div>

      <div className="flex gap-4">
        <button 
          disabled={isRegenerating || isValidating} 
          onClick={handleRegenerate} 
          className="rounded-md px-4 py-2 text-white disabled:opacity-50 bg-orange-500 hover:bg-orange-600"
        >
          {isRegenerating ? (
            <span className="inline-flex items-center gap-2">
              <Spinner /> Régénération...
            </span>
          ) : (
            "🔄 Régénérer"
          )}
        </button>
        
        <button 
          disabled={isRegenerating || isValidating} 
          onClick={handleValidate} 
          className="rounded-md px-4 py-2 text-white disabled:opacity-50 bg-green-500 hover:bg-green-600"
        >
          {isValidating ? (
            <span className="inline-flex items-center gap-2">
              <Spinner /> Validation...
            </span>
          ) : (
            "✅ Valider et continuer"
          )}
        </button>
      </div>
      {statusMsg && <p className="text-sm mt-2">{statusMsg}</p>}
      
      {/* Popup de chargement */}
      <LoadingModal
        isVisible={loadingState.isVisible}
        title={loadingState.title}
        logs={loadingState.logs}
        elapsedTime={elapsedTime}
        formatElapsedTime={formatElapsedTime}
      />
    </main>
  );
}


