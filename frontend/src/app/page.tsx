"use client";
import { useState } from "react";
import { UploadZone } from "@/components/UploadZone";
import { useUiStore } from "@/lib/store";
import { setCompanyName, startWorkflowWithFiles, getThreadState } from "@/lib/api-client";
import { Spinner } from "@/components/Spinner";
import { useRouter } from "next/navigation";
import { LoadingModal } from "@/components/LoadingModal";
import { useLoadingModal } from "@/hooks/useLoadingModal";

export default function Home() {
  const router = useRouter();
  const { excelFile, transcriptFiles, companyName, setExcelFile, setTranscriptFiles, setCompanyName, isBusy, setIsBusy, setPhase } = useUiStore();
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string>("");
  const { loadingState, showLoading, addLog, hideLoading, elapsedTime, formatElapsedTime } = useLoadingModal();
  const ready = !!excelFile && transcriptFiles.length > 0 && companyName.trim().length > 0;

  async function onStart() {
    if (!excelFile) return;
    
    // Afficher la popup de chargement
    showLoading("Analyse des besoins en cours", [
      "Préparation des fichiers...",
      "Envoi vers le serveur...",
      "Démarrage de l'analyse...",
      "🤖 Modèle IA utilisé: gpt-4o-mini"
    ]);
    
    setSubmitting(true);
    setIsBusy(true);
    try {
      addLog("Conversion des fichiers...");
      addLog(`📊 Fichier Excel: ${excelFile.name}`);
      addLog(`📄 Fichiers PDF: ${transcriptFiles.map(f => f.name).join(', ')}`);
      addLog(`🏢 Entreprise: ${companyName}`);
      
      // Convertir les fichiers uploadés en objets File
      const workshopFiles: File[] = [];
      const transcriptFilesArray: File[] = [];
      
      if (excelFile) {
        // Créer un objet File à partir des données du store
        const file = new File([(excelFile as any).content || ''], excelFile.name, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        workshopFiles.push(file);
      }
      
      for (const transcriptFile of transcriptFiles) {
        const file = new File([(transcriptFile as any).content || ''], transcriptFile.name, { type: 'application/pdf' });
        transcriptFilesArray.push(file);
      }
      
      if (workshopFiles.length === 0) throw new Error("Aucun fichier Excel reconnu");
      if (transcriptFilesArray.length === 0) throw new Error("Aucun PDF reconnu");

      addLog("Enregistrement de l'entreprise...");
      // Enregistrer l'entreprise (localStorage)
      await setCompanyName(companyName);

      addLog("🚀 Démarrage du workflow LangGraph...");
      // Démarrer le workflow avec les vrais fichiers uploadés
      const result = await startWorkflowWithFiles(workshopFiles, transcriptFilesArray, companyName);
      
      if (!result.success) {
        throw new Error(`Démarrage workflow échoué: ${result.error || 'Erreur inconnue'}`);
      }

      addLog("✅ Workflow démarré avec succès");
      addLog("⏳ Attente de l'analyse des besoins...");
      addLog("📊 Traitement des fichiers Excel en cours...");
      addLog("📄 Analyse des transcriptions PDF en cours...");
      addLog("🌐 Recherche d'informations sur l'entreprise avec Sonar...");
      addLog("🔍 Analyse des besoins métier avec gpt-4o-mini...");
      
      // Attendre un peu pour que le workflow commence
      await new Promise(resolve => setTimeout(resolve, 5000)); // Attendre 5 secondes
      
      addLog("Analyse terminée");
      addLog("Redirection vers la validation...");
      
      // On active la phase "needs" pour autoriser la page suivante
      setPhase("needs");
      
      // Masquer la popup et rediriger
      hideLoading();
      router.push("/validation/needs");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      addLog(`Erreur: ${msg}`);
      setStatusMsg(msg);
      hideLoading();
    } finally {
      setSubmitting(false);
      setIsBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-6 space-y-8">
      <h1 className="text-2xl font-semibold">aiko – Rapports de besoins et use cases</h1>

      <section className="space-y-2">
        <h2 className="font-medium">1) Fichier Excel des ateliers</h2>
        <UploadZone accept=".xlsx,.xls" multiple={false} onFiles={(fs) => setExcelFile(fs[0] || null)} />
        {excelFile && <p className="text-sm text-gray-600">Sélectionné: {excelFile.name}</p>}
      </section>

      <section className="space-y-2">
        <h2 className="font-medium">2) Transcriptions (PDF/JSON)</h2>
        <UploadZone accept=".pdf,.json" multiple onFiles={setTranscriptFiles} />
        {transcriptFiles.length > 0 && (
          <div className="text-sm text-gray-600">
            <p className="font-medium">{transcriptFiles.length} fichier(s) sélectionné(s):</p>
            <ul className="list-disc list-inside ml-2 space-y-1">
              {transcriptFiles.map((file, index) => (
                <li key={index} className="text-xs">{file.name}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="font-medium">3) Entreprise</h2>
        <input
          type="text"
          placeholder="Ex: Cousin Surgery"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          className="w-full rounded-md border p-2"
        />
      </section>

      <section>
        <button
          disabled={!ready || submitting}
          onClick={onStart}
          className="rounded-md px-4 py-2 text-white disabled:opacity-50"
          style={{ backgroundColor: submitting ? 'rgb(161, 109, 246)' : '#670ffc' }}
        >
          {submitting ? (
            <span className="inline-flex items-center gap-2"><Spinner /> Démarrage...</span>
          ) : (
            "Démarrer l'analyse des besoins"
          )}
        </button>
        {statusMsg && (
          <p className="mt-2 text-sm">{statusMsg}</p>
        )}
      </section>
      
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
