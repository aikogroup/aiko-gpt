"use client";

/**
 * Page 1 : Accueil (Upload)
 * 
 * FR: Page d'upload des fichiers et lancement de l'analyse
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { uploadFiles, generateNeeds, generateThreadId } from "@/lib/api-client";
import Image from "next/image";
import { LLMLogViewer } from "@/components/LLMLogViewer";

export default function Home() {
  const router = useRouter();
  const {
    setThreadId,
    setExcelFilePath,
    setPdfJsonFilePaths,
    setCompanyName: setStoreCompanyName,
    setNeeds,
    setLoading,
    setError,
    setCurrentStep,
  } = useStore();

  // FR: États locaux
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [pdfJsonFiles, setPdfJsonFiles] = useState<File[]>([]);
  const [companyName, setCompanyName] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setErrorMsg] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState(false);

  // FR: Gestion upload Excel
  const handleExcelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith('.xlsx')) {
      setExcelFile(file);
      setErrorMsg(null);
    } else {
      setErrorMsg("Le fichier Excel doit être au format .xlsx");
    }
  };

  // FR: Gestion upload PDF/JSON
  const handlePdfJsonChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(f => 
      f.name.endsWith('.pdf') || f.name.endsWith('.json')
    );
    
    if (validFiles.length !== files.length) {
      setErrorMsg("Seuls les fichiers .pdf et .json sont acceptés");
    } else {
      setPdfJsonFiles(validFiles);
      setErrorMsg(null);
    }
  };

  // FR: Lancement de l'analyse
  const handleAnalyze = async () => {
    // FR: Validation
    if (!excelFile) {
      setErrorMsg("Veuillez sélectionner un fichier Excel");
      return;
    }
    if (pdfJsonFiles.length === 0) {
      setErrorMsg("Veuillez sélectionner au moins un fichier PDF ou JSON");
      return;
    }
    if (!companyName.trim()) {
      setErrorMsg("Veuillez saisir le nom de l'entreprise");
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    setLoading(true);
    setError(null);

    try {
      // FR: 1. Upload des fichiers
      const uploadResponse = await uploadFiles(
        excelFile,
        pdfJsonFiles,
        companyName
      );

      // FR: 2. Stocker dans le store
      setExcelFilePath(uploadResponse.excel_file_path);
      setPdfJsonFilePaths(uploadResponse.pdf_json_file_paths);
      setStoreCompanyName(uploadResponse.company_name);
      setThreadId(uploadResponse.thread_id);

      // FR: 3. Afficher les logs LLM
      setShowLogs(true);

      // FR: 4. Générer les besoins
      const { needs } = await generateNeeds({
        excel_file_path: uploadResponse.excel_file_path,
        pdf_json_file_paths: uploadResponse.pdf_json_file_paths,
        company_name: uploadResponse.company_name,
        action: 'generate_needs',
      }, uploadResponse.thread_id);

      // FR: 5. Stocker les besoins
      setNeeds(needs);
      setCurrentStep('needs');

      // FR: 6. Fermer les logs et naviguer
      setShowLogs(false);
      router.push('/needs');
      
    } catch (err: any) {
      console.error('Erreur lors de l\'analyse:', err);
      setErrorMsg(err.message || "Erreur lors de l'analyse");
      setError(err.message || "Erreur lors de l'analyse");
    } finally {
      setIsLoading(false);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-6">
            📊 Étape 1 : Upload des données
          </h2>

          {/* FR: Erreur globale */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              ⚠️ {error}
            </div>
          )}

          {/* FR: Section Excel */}
          <section className="mb-6">
            <label className="block text-lg font-semibold mb-2">
              1. Fichier Excel (Ateliers)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition">
              <input
                type="file"
                accept=".xlsx"
                onChange={handleExcelChange}
                className="w-full"
              />
              {excelFile && (
                <p className="mt-2 text-sm text-green-600">
                  ✅ Fichier sélectionné : {excelFile.name}
                </p>
              )}
            </div>
          </section>

          {/* FR: Section PDF/JSON */}
          <section className="mb-6">
            <label className="block text-lg font-semibold mb-2">
              2. Fichiers PDF/JSON (Transcriptions)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition">
              <input
                type="file"
                accept=".pdf,.json"
                multiple
                onChange={handlePdfJsonChange}
                className="w-full"
              />
              {pdfJsonFiles.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-green-600 font-semibold">
                    ✅ {pdfJsonFiles.length} fichier(s) sélectionné(s) :
                  </p>
                  <ul className="text-sm text-gray-600 mt-1">
                    {pdfJsonFiles.map((f, idx) => (
                      <li key={idx}>• {f.name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>

          {/* FR: Nom d'entreprise */}
          <section className="mb-6">
            <label className="block text-lg font-semibold mb-2">
              3. Nom de l'entreprise
            </label>
            <input
              type="text"
              placeholder="Ex: Cousin Biotech"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </section>

          {/* FR: Bouton Analyser */}
          <section className="mt-8 flex items-center gap-4">
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !excelFile || pdfJsonFiles.length === 0 || !companyName.trim()}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyse en cours...
                </>
              ) : (
                <>
                  🚀 Analyser
                </>
              )}
            </button>

            {isLoading && (
              <p className="text-sm text-gray-600">
                ⏱️ Cela peut prendre 1-2 minutes...
              </p>
            )}
          </section>

          {/* FR: Informations */}
          <section className="mt-8 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">ℹ️ Processus d'analyse :</h3>
            <ol className="text-sm text-blue-800 space-y-1 ml-4">
              <li>1. Parsing du fichier Excel (ateliers)</li>
              <li>2. Analyse des transcriptions PDF/JSON</li>
              <li>3. Recherche contextuelle entreprise (Perplexity)</li>
              <li>4. Génération de 10 besoins métier avec citations</li>
            </ol>
          </section>
        </div>
      </main>

      {/* FR: Logs LLM en temps réel */}
      <LLMLogViewer 
        isVisible={showLogs} 
        onClose={() => setShowLogs(false)} 
      />
    </div>
  );
}
