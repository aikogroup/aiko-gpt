"use client";
import { useEffect, useState } from "react";
import { getWorkflowStatus, getWorkflowResults, downloadReport } from "@/lib/api-client";

export default function ResultsPage() {
  const [status, setStatus] = useState<string>("idle");
  const [results, setResults] = useState<any>(null);
  // Supporte à la fois les clés au niveau racine et sous values
  const needs = (results?.validated_needs
    ?? results?.final_needs
    ?? results?.values?.validated_needs
    ?? results?.values?.final_needs
    ?? []);
  const qw = (results?.validated_quick_wins
    ?? results?.final_quick_wins
    ?? results?.values?.validated_quick_wins
    ?? results?.values?.final_quick_wins
    ?? []);
  const sia = (results?.validated_structuration_ia
    ?? results?.final_structuration_ia
    ?? results?.values?.validated_structuration_ia
    ?? results?.values?.final_structuration_ia
    ?? []);

  useEffect(() => {
    let mounted = true;
    const loadAll = async () => {
      try {
        const [st, rs] = await Promise.all([getWorkflowStatus(), getWorkflowResults()]);
        if (st.ok) {
          const js = await st.json();
          if (mounted) setStatus(js.status || "unknown");
        }
        if (rs.ok) {
          const jr = await rs.json();
          if (mounted) setResults(jr);
        }
      } catch {}
    };
    loadAll();
    const iv = setInterval(loadAll, 5000);
    return () => { mounted = false; clearInterval(iv); };
  }, []);

  const loadResults = async () => {
    const res = await getWorkflowResults();
    if (res.ok) setResults(await res.json());
  };

  const onDownload = async () => {
    try {
      const blob = await downloadReport();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "rapport.docx";
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
        <h2 className="text-xl font-medium">Quick Wins validés</h2>
        {qw.length === 0 ? <p>Aucun Quick Win validé.</p> : (
          <ul className="list-disc pl-6">
            {qw.map((uc: any, i: number) => (
              <li key={i}>
                <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">Structuration IA validés</h2>
        {sia.length === 0 ? <p>Aucun cas structuration IA validé.</p> : (
          <ul className="list-disc pl-6">
            {sia.map((uc: any, i: number) => (
              <li key={i}>
                <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
              </li>
            ))}
          </ul>
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


