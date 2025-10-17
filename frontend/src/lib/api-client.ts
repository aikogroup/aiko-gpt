// Minimal client using fetch to call existing FastAPI on port 2025

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:2025";

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

export async function startWorkflow(): Promise<Response> {
  const threadId = makeThreadId();
  const company = typeof window !== "undefined" ? localStorage.getItem("company_name") : null;
  const payload = { workshop_files: [], transcript_files: [], company_name: company || undefined };
  return fetch(`${API_BASE}/threads/${threadId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function startWorkflowWithFiles(workshopFiles: string[], transcriptFiles: string[], companyName?: string): Promise<Response> {
  const threadId = makeThreadId();
  const payload = { workshop_files: workshopFiles, transcript_files: transcriptFiles, company_name: companyName || undefined };
  return fetch(`${API_BASE}/threads/${threadId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
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
  const res = await fetch(`${API_BASE}/threads/${makeThreadId()}/report`, { method: "GET" });
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


