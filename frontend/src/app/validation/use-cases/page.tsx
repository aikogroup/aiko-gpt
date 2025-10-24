"use client";
import { useEffect, useState } from "react";
import { getThreadState, sendUseCaseValidation, regenerateUseCases } from "@/lib/api-client";
import { Spinner } from "@/components/Spinner";
import { useRouter } from "next/navigation";
import { useUiStore } from "@/lib/store";
import { LoadingModal } from "@/components/LoadingModal";
import { useLoadingModal } from "@/hooks/useLoadingModal";

export default function UseCasesValidationPage() {
  const router = useRouter();
  const { isBusy, setIsBusy, setPhase, selectedUseCases, setSelectedUseCases } = useUiStore();
  const { loadingState, showLoading, addLog, hideLoading, elapsedTime, formatElapsedTime } = useLoadingModal();
  const [quickWins, setQuickWins] = useState<any[]>([]);
  const [structIa, setStructIa] = useState<any[]>([]);
  const [selQw, setSelQw] = useState<Record<number, boolean>>({});
  const [selSia, setSelSia] = useState<Record<number, boolean>>({});
  const [comment, setComment] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [persistedSelected, setPersistedSelected] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const state = await getThreadState();
        setQuickWins(state?.values?.proposed_quick_wins || []);
        setStructIa(state?.values?.proposed_structuration_ia || []);
      } catch {}
    })();
  }, []);

  // Fonction pour régénérer des use cases
  // Fonctions pour la réorganisation automatique
  const handleQuickWinToggle = (index: number) => {
    const isSelected = !!selQw[index];
    const useCase = quickWins[index];
    
    if (!isSelected) {
      // Sélectionner : ajouter en haut de persistedSelected
      setPersistedSelected(prev => [useCase, ...prev]);
      setSelQw(prev => ({ ...prev, [index]: true }));
    } else {
      // Désélectionner : retirer de persistedSelected
      setPersistedSelected(prev => prev.filter(uc => uc !== useCase));
      setSelQw(prev => ({ ...prev, [index]: false }));
    }
  };

  const handleStructIaToggle = (index: number) => {
    const isSelected = !!selSia[index];
    const useCase = structIa[index];
    
    if (!isSelected) {
      // Sélectionner : ajouter en haut de persistedSelected
      setPersistedSelected(prev => [useCase, ...prev]);
      setSelSia(prev => ({ ...prev, [index]: true }));
    } else {
      // Désélectionner : retirer de persistedSelected
      setPersistedSelected(prev => prev.filter(uc => uc !== useCase));
      setSelSia(prev => ({ ...prev, [index]: false }));
    }
  };

  const handlePersistedDeselect = (index: number) => {
    const useCase = persistedSelected[index];
    
    // Retirer de persistedSelected
    setPersistedSelected(prev => prev.filter((_, idx) => idx !== index));
    
    // Décocher dans la liste normale
    const qwIndex = quickWins.findIndex(uc => uc === useCase);
    const siaIndex = structIa.findIndex(uc => uc === useCase);
    
    if (qwIndex !== -1) {
      setSelQw(prev => ({ ...prev, [qwIndex]: false }));
    }
    if (siaIndex !== -1) {
      setSelSia(prev => ({ ...prev, [siaIndex]: false }));
    }
  };

  const handleRegenerate = async () => {
    // Afficher la popup de chargement
    showLoading("Régénération des cas d'usage", [
      "Préparation de la régénération...",
      "Envoi des cas d'usage sélectionnés...",
      "Génération de nouveaux cas d'usage..."
    ]);
    
    setIsRegenerating(true);
    setIsBusy(true);
    setStatusMsg("Régénération des cas d'usage...");
    
    try {
      addLog("Sélection des cas d'usage à conserver...");
      // Garder les cas d'usage sélectionnés (éviter les doublons)
      const selectedQw = quickWins.filter((_, i) => selQw[i]);
      const selectedSia = structIa.filter((_, i) => selSia[i]);
      const selectedUseCases = [...selectedQw, ...selectedSia];
      
      // NE PAS ajouter à persistedSelected ici car ils sont déjà sélectionnés
      // setPersistedSelected(prev => {
      //   const existingTitles = new Set(prev.map(p => p.titre || p.title));
      //   const newUseCases = selectedUseCases.filter(uc => !existingTitles.has(uc.titre || uc.title));
      //   return [...prev, ...newUseCases];
      // });
      
      addLog("Envoi de la demande de régénération...");
      addLog("🤖 Modèle IA utilisé: gpt-4o-mini");
      // Appeler l'API pour régénérer
      const result = await regenerateUseCases({
        validated_quick_wins: selectedQw,
        validated_structuration_ia: selectedSia,
        rejected_quick_wins: quickWins.filter((_, i) => !selQw[i]),
        rejected_structuration_ia: structIa.filter((_, i) => !selSia[i]),
        user_feedback: comment,
      });
      
      console.log('✅ [DEBUG] Résultat régénération:', result);
      addLog("Régénération envoyée avec succès");
      addLog("Attente des nouveaux cas d'usage...");
      setStatusMsg("Nouveaux cas d'usage générés.");
      
      // Attendre un peu pour que le workflow se termine
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Recharger les cas d'usage avec polling
      let attempts = 0;
      const maxAttempts = 30; // 30 secondes max
      
      while (attempts < maxAttempts) {
        try {
          console.log(`🔄 [DEBUG] Tentative ${attempts + 1}/${maxAttempts} - Récupération des nouveaux cas d'usage...`);
          const state = await getThreadState();
          console.log("🔄 [DEBUG] État reçu:", state);
          
          // Traduire l'état technique en message utilisateur
          const workflowStatus = state?.status;
          const nextNodes = state?.next || [];
          
          if (attempts % 10 === 0) {
            let userMessage = "";
            if (state.next && state.next.includes('analyze_use_cases')) {
              userMessage = "🤖 Génération de nouveaux cas d'usage IA...";
            } else if (state.status === 'running') {
              userMessage = "⚙️ Traitement en cours...";
            } else if (state.status === 'pending') {
              userMessage = "⏳ Initialisation...";
            } else {
              userMessage = "🔄 Vérification de l'avancement...";
            }
            addLog(userMessage);
          }
          
          const newQuickWins = state?.values?.proposed_quick_wins || [];
          const newStructIa = state?.values?.proposed_structuration_ia || [];
          
          console.log("🔄 [DEBUG] Nouveaux cas d'usage:", { quickWins: newQuickWins.length, structIa: newStructIa.length });
          
          if (newQuickWins.length > 0 || newStructIa.length > 0) {
            console.log("✅ Nouveaux cas d'usage disponibles:", { quickWins: newQuickWins.length, structIa: newStructIa.length });
            addLog(`Nouveaux cas d'usage générés: ${newQuickWins.length + newStructIa.length}`);
            setQuickWins(newQuickWins);
            setStructIa(newStructIa);
            // NE PAS reset les sélections - elles sont préservées dans persistedSelected
            // setSelQw({}); // Reset selection
            // setSelSia({}); // Reset selection
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
      
      console.error("❌ [DEBUG] Timeout: Aucun nouveau cas d'usage après", maxAttempts, "tentatives");
      addLog("Timeout: Aucun nouveau cas d'usage généré");
      
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

  // Fonction pour valider et passer aux résultats
  const handleValidate = async () => {
    // Afficher la popup de chargement
    showLoading("Validation des cas d'usage", [
      "Préparation de la validation...",
      "Envoi des cas d'usage sélectionnés...",
      "Finalisation du rapport..."
    ]);
    
    setIsValidating(true);
    setIsBusy(true);
    setStatusMsg("Validation des cas d'usage sélectionnés...");
    
    let validated_qw: any[] = [];
    let validated_sia: any[] = [];
    
    try {
      validated_qw = quickWins.filter((_, i) => selQw[i]);
      const rejected_qw = quickWins.filter((_, i) => !selQw[i]);
      validated_sia = structIa.filter((_, i) => selSia[i]);
      const rejected_sia = structIa.filter((_, i) => !selSia[i]);

      if (validated_qw.length === 0 && validated_sia.length === 0) {
        addLog("Erreur: Aucun cas d'usage sélectionné");
        setStatusMsg("Veuillez sélectionner au moins un cas d'usage.");
        hideLoading();
        return;
      }

      addLog(`Validation de ${validated_qw.length + validated_sia.length} cas d'usage...`);

      // Sauvegarder les use cases sélectionnés dans le store
      setSelectedUseCases([...validated_qw, ...validated_sia]);

      // Empiler les sélectionnés en haut avec déduplication par titre
      setPersistedSelected((prev) => {
        const byTitle = new Set(prev.map((u) => u.titre || u.title));
        const all = [...validated_qw, ...validated_sia].filter((u) => !(byTitle.has(u.titre || u.title)));
        return [...prev, ...all];
      });

      addLog("Envoi de la validation...");
      addLog("🤖 Modèle IA utilisé: gpt-4o-mini");
      const res = await sendUseCaseValidation({
        validated_quick_wins: validated_qw,
        validated_structuration_ia: validated_sia,
        rejected_quick_wins: rejected_qw,
        rejected_structuration_ia: rejected_sia,
        user_feedback: comment,
      });
      
      console.log('✅ [DEBUG] Résultat validation:', res);
      addLog("Validation envoyée avec succès");
      addLog("Attente de la finalisation...");
      setStatusMsg("Validation envoyée.");
      
      // Vérifier si on a au moins 5 cas d'usage sélectionnés
      const totalSelected = validated_qw.length + validated_sia.length;
      if (totalSelected >= 5) {
        addLog("Validation terminée - Passage aux résultats");
        setPhase("results");
        hideLoading();
        // Redirection directe
        setTimeout(() => {
          router.push("/results");
        }, 100);
        return;
      }
      
      // Sinon, continuer avec le polling pour vérifier l'état du workflow
      addLog("Vérification de l'état du workflow...");
      try {
        let attempts = 0;
        const maxAttempts = 30; // 30 secondes max
        
        while (attempts < maxAttempts) {
          const state = await getThreadState();
          const vqw = state?.values?.validated_quick_wins || [];
          const vsia = state?.values?.validated_structuration_ia || [];
          const total = vqw.length + vsia.length;
          
          addLog(`Vérification... (${total}/5 cas d'usage validés)`);
          
          if (total >= 5) {
            addLog("Validation terminée - Passage aux résultats");
            setPhase("results");
            hideLoading();
            // S'assurer que la redirection se fait
            setTimeout(() => {
              router.push("/results");
            }, 100);
            return;
          }
          
          // Si on a atteint 5 cas d'usage au total (sélectionnés + validés), rediriger
          const totalValidated = totalSelected + total;
          if (totalValidated >= 5) {
            addLog("Validation terminée - Passage aux résultats");
            setPhase("results");
            hideLoading();
            setTimeout(() => {
              router.push("/results");
            }, 100);
            return;
          }
          
          // Sinon, recharger de nouvelles propositions et réinitialiser les sélections
          const newQuickWins = state?.values?.proposed_quick_wins || [];
          const newStructIa = state?.values?.proposed_structuration_ia || [];
          
          if (newQuickWins.length > 0 || newStructIa.length > 0) {
            addLog(`Nouveaux cas d'usage disponibles: ${newQuickWins.length + newStructIa.length}`);
            setQuickWins(newQuickWins);
            setStructIa(newStructIa);
            setSelQw({});
            setSelSia({});
            setComment("");
            hideLoading();
            return;
          }
          
          attempts++;
          await new Promise((r) => setTimeout(r, 1000));
        }
        
        addLog("Timeout: Aucun nouveau cas d'usage généré");
      } catch (error) {
        console.error('❌ Erreur lors de la vérification:', error);
        addLog(`Erreur: ${error instanceof Error ? error.message : String(error)}`);
      }
      
    } catch (error) {
      console.error('❌ Erreur validation:', error);
      addLog(`Erreur: ${error instanceof Error ? error.message : String(error)}`);
      setStatusMsg("Erreur lors de la validation.");
      
      // Fallback: si on a au moins 5 cas d'usage sélectionnés, rediriger quand même
      const totalSelected = validated_qw.length + validated_sia.length;
      if (totalSelected >= 5) {
        addLog("Validation terminée - Passage aux résultats (fallback après erreur)");
        setPhase("results");
        setTimeout(() => {
          router.push("/results");
        }, 100);
        return;
      }
    } finally {
      setIsValidating(false);
      setIsBusy(false);
      hideLoading();
    }
  };

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-6 text-black">
      <h1 className="text-2xl font-semibold">Validation des cas d'usage (5 minimum)</h1>

      {persistedSelected.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-medium">Sélection en cours (cumulée)</h2>
          
          {/* Quick Wins sélectionnés */}
          {persistedSelected.filter(uc => quickWins.includes(uc)).length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-blue-600">Quick Wins sélectionnés</h3>
              <ul className="space-y-2">
                {persistedSelected.filter(uc => quickWins.includes(uc)).map((uc, i) => (
                  <li key={`qw-${i}`} className="border rounded-md p-3 flex items-start gap-3">
                    <input 
                      type="checkbox" 
                      checked={true} 
                      onChange={() => handlePersistedDeselect(persistedSelected.indexOf(uc))}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                      {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                      {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Structuration IA sélectionnées */}
          {persistedSelected.filter(uc => structIa.includes(uc)).length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-green-600">Structuration IA sélectionnées</h3>
              <ul className="space-y-2">
                {persistedSelected.filter(uc => structIa.includes(uc)).map((uc, i) => (
                  <li key={`sia-${i}`} className="border rounded-md p-3 flex items-start gap-3">
                    <input 
                      type="checkbox" 
                      checked={true} 
                      onChange={() => handlePersistedDeselect(persistedSelected.indexOf(uc))}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                      {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                      {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <section className="space-y-3">
        <h2 className="font-medium">Quick Wins</h2>
        {quickWins.length === 0 ? (
          <p>Aucun Quick Win</p>
        ) : (
          <div className="space-y-2">
            {quickWins.map((uc, i) => {
              // Ne pas afficher les éléments déjà sélectionnés (ils sont dans persistedSelected)
              const isInPersisted = persistedSelected.some(p => p === uc);
              if (isInPersisted) return null;
              
              return (
                <label key={i} className="flex items-start gap-3 border rounded-md p-3 cursor-pointer">
                  <input type="checkbox" disabled={isRegenerating || isValidating} checked={!!selQw[i]} onChange={() => handleQuickWinToggle(i)} />
                  <div>
                    <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                    {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                    {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                  </div>
                </label>
              );
            })}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-medium">Structuration IA</h2>
        {structIa.length === 0 ? (
          <p>Aucune proposition</p>
        ) : (
          <div className="space-y-2">
            {structIa.map((uc, i) => {
              // Ne pas afficher les éléments déjà sélectionnés (ils sont dans persistedSelected)
              const isInPersisted = persistedSelected.some(p => p === uc);
              if (isInPersisted) return null;
              
              return (
                <label key={i} className="flex items-start gap-3 border rounded-md p-3 cursor-pointer">
                  <input type="checkbox" disabled={isRegenerating || isValidating} checked={!!selSia[i]} onChange={() => handleStructIaToggle(i)} />
                  <div>
                    <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                    {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                    {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                  </div>
                </label>
              );
            })}
          </div>
        )}
      </section>

      <div className="space-y-2">
        <h3 className="font-medium">Commentaires (optionnel)</h3>
        <textarea disabled={isRegenerating || isValidating} value={comment} onChange={(e) => setComment(e.target.value)} className="w-full border rounded-md p-2 disabled:bg-gray-100" rows={4} />
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


