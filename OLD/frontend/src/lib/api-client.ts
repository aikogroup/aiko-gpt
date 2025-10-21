// Client HTTP côté frontend pour parler au serveur LangGraph (8123) et à l'app HTTP (upload/report)

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123";

function makeThreadId() {
  let id = typeof window !== "undefined" ? localStorage.getItem("thread_id") : null;
  if (!id && typeof crypto !== "undefined" && "randomUUID" in crypto) {
    id = crypto.randomUUID();
    if (typeof window !== "undefined") localStorage.setItem("thread_id", id);
  }
  return id || "default-thread";
}

export async function uploadFiles(files: File[]): Promise<{ file_paths: string[]; file_types: { workshop: string[]; transcript: string[] }; count: number }>{
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(`${API_BASE}/files/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload échoué (${res.status})`);
  return res.json();
}

export async function setCompanyName(companyName: string): Promise<Response> {
  // Rien à faire côté API pour l’instant; on stocke côté front
  if (typeof window !== "undefined") localStorage.setItem("company_name", companyName);
  return new Response(null, { status: 200 });
}

async function getAssistantId(graphId: string): Promise<string> {
  // Cache local pour éviter de requêter à chaque fois
  const cacheKey = `assistant_id_${graphId}`;
  const cached = typeof window !== "undefined" ? localStorage.getItem(cacheKey) : null;
  if (cached) return cached;

  // Rechercher un assistant pour ce graph
  const res = await fetch(`${API_BASE}/assistants/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ graph_id: graphId, limit: 1 }),
  });
  if (!res.ok) throw new Error(`Assistant search error (${res.status})`);
  const items = await res.json();
  const assistant = Array.isArray(items) && items.length > 0 ? items[0] : null;
  if (!assistant || !assistant.assistant_id) throw new Error("Assistant introuvable pour le graph");
  if (typeof window !== "undefined") localStorage.setItem(cacheKey, assistant.assistant_id);
  return assistant.assistant_id as string;
}

async function ensureThreadExists(threadId: string): Promise<string> {
  // Essaie de créer le thread s'il n'existe pas côté serveur
  // API LangGraph: POST /threads avec un body optionnel (id)
  const res = await fetch(`${API_BASE}/threads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId }),
  });
  if (!res.ok && res.status !== 409) {
    // 409 si déjà existant; sinon, c'est une vraie erreur
    throw new Error(`Création du thread échouée (${res.status})`);
  }
  const data = res.ok ? await res.json().catch(() => ({})) : {};
  return (data.thread_id as string) || threadId;
}

export async function startWorkflow(): Promise<Response> {
  const threadId = makeThreadId();
  await ensureThreadExists(threadId);
  const company = typeof window !== "undefined" ? localStorage.getItem("company_name") : null;
  const input = { workshop_files: [], transcript_files: [], company_name: company || undefined };
  const assistantId = await getAssistantId("need_analysis");
  return fetch(`${API_BASE}/threads/${threadId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assistant_id: assistantId, input }),
  });
}

export async function startWorkflowWithFiles(workshopFiles: string[], transcriptFiles: string[], companyName?: string): Promise<{ success: boolean; run_id?: string; error?: string }> {
  try {
    const threadId = makeThreadId();
    await ensureThreadExists(threadId);
    const assistantId = await getAssistantId("need_analysis");
    const input = { workshop_files: workshopFiles, transcript_files: transcriptFiles, company_name: companyName || undefined };
    
    const res = await fetch(`${API_BASE}/threads/${threadId}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assistant_id: assistantId, input }),
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      return { success: false, error: errorData.detail || `HTTP ${res.status}` };
    }
    
    const data = await res.json();
    return { success: true, run_id: data.run_id };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export async function getWorkflowStatus(): Promise<Response> {
  const threadId = makeThreadId();
  return fetch(`${API_BASE}/threads/${threadId}/state`, { method: "GET" });
}

export async function getWorkflowResults(): Promise<Response> {
  const threadId = makeThreadId();
  return fetch(`${API_BASE}/threads/${threadId}/state`, { method: "GET" });
}

export async function downloadReport(): Promise<Blob> {
  const res = await fetch(`${API_BASE}/report?thread_id=${makeThreadId()}`, { method: "GET" });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to download report (${res.status}): ${errorText}`);
  }
  return res.blob();
}

// Validation endpoints
export async function getThreadState(): Promise<any> {
  const res = await getWorkflowResults();
  if (!res.ok) throw new Error(`State error (${res.status})`);
  return res.json();
}

export async function sendNeedsValidation(payload: {
  validated_needs: any[];
  rejected_needs: any[];
  user_feedback?: string;
}): Promise<Response> {
  const threadId = makeThreadId();
  return fetch(`${API_BASE}/threads/${threadId}/validation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      validated_needs: payload.validated_needs,
      rejected_needs: payload.rejected_needs,
      user_feedback: payload.user_feedback || "",
    }),
  });
}

export async function sendUseCaseValidation(payload: {
  validated_quick_wins: any[];
  validated_structuration_ia: any[];
  rejected_quick_wins: any[];
  rejected_structuration_ia: any[];
  user_feedback?: string;
}): Promise<Response> {
  const threadId = makeThreadId();
  return fetch(`${API_BASE}/threads/${threadId}/use-case-validation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      validated_quick_wins: payload.validated_quick_wins,
      validated_structuration_ia: payload.validated_structuration_ia,
      rejected_quick_wins: payload.rejected_quick_wins,
      rejected_structuration_ia: payload.rejected_structuration_ia,
      user_feedback: payload.user_feedback || "",
    }),
  });
}

/**
 * Attends que le workflow atteigne l'interruption avec identified_needs prêts
 * @param runId - ID du run à surveiller
 * @param timeout - Timeout en ms (défaut: 120s)
 * @param interval - Intervalle de polling en ms (défaut: 3s)
 * @returns Les besoins identifiés ou lance une erreur
 */
export async function waitForIdentifiedNeeds(runId: string, timeout = 120000, interval = 3000): Promise<any[]> {
  const startTime = Date.now();
  const threadId = makeThreadId();
  
  console.log(`[waitForIdentifiedNeeds] Début du polling pour run_id=${runId}, thread_id=${threadId}`);
  
  while (Date.now() - startTime < timeout) {
    try {
      // 1. Vérifier le status du run
      const runRes = await fetch(`${API_BASE}/threads/${threadId}/runs/${runId}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      
      if (runRes.ok) {
        const runData = await runRes.json();
        console.log(`[waitForIdentifiedNeeds] Run status: ${runData.status}`);
        
        // Si le run est en erreur, on arrête
        if (runData.status === "error") {
          throw new Error(`Workflow en erreur: ${runData.error || "Erreur inconnue"}`);
        }
        
        // 2. Récupérer l'état du thread
        const stateRes = await fetch(`${API_BASE}/threads/${threadId}/state`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });
        
        if (stateRes.ok) {
          const stateData = await stateRes.json();
          const identifiedNeeds = stateData?.values?.identified_needs;
          
          console.log(`[waitForIdentifiedNeeds] identified_needs présents: ${Array.isArray(identifiedNeeds) ? identifiedNeeds.length : 0}`);
          
          // Si identified_needs est présent et non vide, on retourne
          if (Array.isArray(identifiedNeeds) && identifiedNeeds.length > 0) {
            console.log(`[waitForIdentifiedNeeds] ✅ Besoins trouvés: ${identifiedNeeds.length}`);
            return identifiedNeeds;
          }
          
          // Si le workflow est interrompu mais pas encore de needs, on continue à attendre
          if (runData.status === "interrupted") {
            console.log(`[waitForIdentifiedNeeds] Workflow interrompu, mais needs pas encore disponibles. Attente...`);
          }
        }
      }
      
      // Attendre avant la prochaine tentative
      await new Promise(resolve => setTimeout(resolve, interval));
      
    } catch (err) {
      console.error(`[waitForIdentifiedNeeds] Erreur lors du polling:`, err);
      throw err;
    }
  }
  
  throw new Error(`Timeout (${timeout}ms) en attendant identified_needs. Le workflow n'a pas atteint le nœud d'analyse des besoins.`);
}


