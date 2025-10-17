"use client";
import { useState } from "react";
import { UploadZone } from "@/components/UploadZone";
import { useUiStore } from "@/lib/store";
import { uploadFiles, setCompanyName, startWorkflowWithFiles } from "@/lib/api-client";
import { Spinner } from "@/components/Spinner";
import { LogViewer } from "@/components/LogViewer";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const { excelFile, transcriptFiles, companyName, setExcelFile, setTranscriptFiles, setCompanyName, isBusy, setIsBusy, setPhase } = useUiStore();
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string>("");
  const ready = !!excelFile && transcriptFiles.length > 0 && companyName.trim().length > 0;

  async function onStart() {
    if (!excelFile) return;
    setSubmitting(true);
    setIsBusy(true);
    try {
      // Upload Excel
      const upExcel = await uploadFiles([excelFile]);
      const workshopPaths = upExcel.file_types?.workshop || [];
      if (workshopPaths.length === 0) throw new Error("Aucun fichier Excel reconnu côté API");

      // Upload PDFs/JSONs
      const upTrans = await uploadFiles(transcriptFiles);
      const transcriptPaths = upTrans.file_types?.transcript || [];
      if (transcriptPaths.length === 0) throw new Error("Aucun PDF/JSON reconnu côté API");

      // Enregistrer l'entreprise (localStorage)
      await setCompanyName(companyName);

      // Démarrer le workflow avec chemins renvoyés par l'API
      const run = await startWorkflowWithFiles(workshopPaths, transcriptPaths, companyName);
      if (!run || !("ok" in run) || !run.ok) {
        const text = run ? await run.text() : "Réponse invalide";
        throw new Error(`Démarrage workflow échoué (${run && 'status' in run ? run.status : 'N/A'}): ${text}`);
      }

      setStatusMsg("Analyse démarrée. Passage à la validation des besoins...");
      // On active la phase "needs" pour autoriser la page suivante
      setPhase("needs");
      router.push("/validation/needs");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setStatusMsg(msg);
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
            <ul className="list-disc list-inside mt-1 space-y-1">
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
        
        <LogViewer isActive={submitting} context="workflow" />
      </section>
    </main>
  );
}
