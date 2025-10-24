"use client";
import { useEffect, useState } from "react";
import { getWorkflowStatus, getWorkflowResults, downloadReport } from "@/lib/api-client";
import { useUiStore } from "@/lib/store";
import { ReportData } from "@/lib/document-generator";

export default function ResultsPage() {
  const { selectedNeeds, selectedUseCases, companyName } = useUiStore();
  const [status, setStatus] = useState<string>("idle");
  const [results, setResults] = useState<any>(null);
  // Utiliser les données du store en priorité, sinon les données du workflow
  const needs = selectedNeeds.length > 0 ? selectedNeeds : (results?.validated_needs
    ?? results?.final_needs
    ?? results?.values?.validated_needs
    ?? results?.values?.final_needs
    ?? []);
  
  const useCases = selectedUseCases.length > 0 ? selectedUseCases : [];
  
  // Séparer les Quick Wins et Structuration IA des use cases sélectionnés
  // On utilise l'ordre : les premiers sont des Quick Wins, les derniers des Structuration IA
  const qw = useCases.slice(0, Math.ceil(useCases.length / 2));
  const sia = useCases.slice(Math.ceil(useCases.length / 2));
  
  // Fallback pour les données du workflow si pas de sélections
  const workflowQw = (results?.validated_quick_wins
    ?? results?.final_quick_wins
    ?? results?.values?.validated_quick_wins
    ?? results?.values?.final_quick_wins
    ?? []);
  const workflowSia = (results?.validated_structuration_ia
    ?? results?.final_structuration_ia
    ?? results?.values?.validated_structuration_ia
    ?? results?.values?.final_structuration_ia
    ?? []);
  
  const finalQw = qw.length > 0 ? qw : workflowQw;
  const finalSia = sia.length > 0 ? sia : workflowSia;

  useEffect(() => {
    let mounted = true;
    const loadAll = async () => {
      try {
        const threadId = localStorage.getItem('current_thread_id') || 'default';
        const [st, rs] = await Promise.all([getWorkflowStatus(threadId), getWorkflowResults(threadId)]);
        if (mounted) setStatus(st);
        if (rs) {
          if (mounted) setResults(rs);
        }
      } catch {}
    };
    loadAll();
    const iv = setInterval(loadAll, 5000);
    return () => { mounted = false; clearInterval(iv); };
  }, []);

  const loadResults = async () => {
    try {
      const threadId = localStorage.getItem('current_thread_id') || 'default';
      const results = await getWorkflowResults(threadId);
      if (results) setResults(results);
    } catch (error) {
      console.error('Erreur lors du chargement des résultats:', error);
    }
  };

  const onDownload = async () => {
    try {
      const threadId = localStorage.getItem('current_thread_id') || 'default';
      
      // Préparer les données du rapport
      const reportData: ReportData = {
        companyName: companyName || "Entreprise",
        needs: needs.map((need: any) => ({
          theme: need.theme || "Thème",
          quotes: Array.isArray(need.quotes) ? need.quotes : []
        })),
        quickWins: finalQw.map((uc: any) => ({
          titre: uc.titre || uc.title,
          description: uc.description,
          ia_utilisee: uc.ia_utilisee
        })),
        structurationIa: finalSia.map((uc: any) => ({
          titre: uc.titre || uc.title,
          description: uc.description,
          ia_utilisee: uc.ia_utilisee
        })),
        date: new Date().toLocaleDateString('fr-FR')
      };
      
      const blob = await downloadReport(threadId, reportData);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Rapport_IA_${reportData.companyName}_${new Date().toISOString().split('T')[0]}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      console.error("Erreur téléchargement:", message);
      alert(`Erreur lors du téléchargement: ${message}`);
    }
  };

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-6 text-black">
      <h1 className="text-2xl font-semibold">Résultats & suivi</h1>
      <p className="text-sm">Statut: {status}</p>
      <div className="flex gap-3">
        <button onClick={loadResults} className="rounded-md px-4 py-2 text-white" style={{ backgroundColor: '#670ffc' }}>Charger les résultats</button>
        <button onClick={onDownload} className="rounded-md px-4 py-2 text-white" style={{ backgroundColor: '#670ffc' }}>Télécharger le rapport Word</button>
      </div>
      <section className="space-y-4">
        <h2 className="text-xl font-medium">Besoins validés</h2>
        {needs.length === 0 ? <p>Aucun besoin validé.</p> : (
          <ul className="list-disc pl-6">
            {needs.map((n: any, i: number) => (
              <li key={i}>
                <div className="font-medium">{n.theme || "Thème"}</div>
                {Array.isArray(n.quotes) && n.quotes.length > 0 && (
                  <ul className="list-disc pl-6 text-sm">
                    {n.quotes.map((q: string, qi: number) => <li key={qi}>{q}</li>)}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
      
      <section className="space-y-4">
        <h2 className="text-xl font-medium">Cas d'usage validés</h2>
        {finalQw.length === 0 && finalSia.length === 0 ? (
          <p>Aucun cas d'usage validé.</p>
        ) : (
          <div className="space-y-4">
            {finalQw.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-blue-600">Quick Wins</h3>
                <ul className="list-disc pl-6">
                  {finalQw.map((uc: any, i: number) => (
                    <li key={i}>
                      <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                      {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                      {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {finalSia.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-green-600">Structuration IA</h3>
                <ul className="list-disc pl-6">
                  {finalSia.map((uc: any, i: number) => (
                    <li key={i}>
                      <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                      {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                      {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

      {results && (
        <details>
          <summary className="cursor-pointer">Voir l'état brut</summary>
          <pre className="text-xs bg-gray-50 p-3 rounded-md overflow-auto text-black">{JSON.stringify(results, null, 2)}</pre>
        </details>
      )}
    </main>
  );
}


