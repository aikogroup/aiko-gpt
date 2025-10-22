/**
 * API Client - Communication avec LangGraph Server
 * 
 * FR: Fonctions pour communiquer avec l'API LangGraph sur le port 2024
 */

import type {
  Need,
  UseCase,
  WorkflowInput,
  WorkflowOutput,
  UploadFilesResponse,
  GenerateNeedsRequest,
  GenerateNeedsResponse,
  RegenerateNeedsRequest,
  GenerateUseCasesRequest,
  GenerateUseCasesResponse,
  RegenerateUseCasesRequest,
  ApiError,
} from './schemas';

// FR: URL de l'API LangGraph (depuis variables d'environnement)
const LANGGRAPH_URL = process.env.NEXT_PUBLIC_LANGGRAPH_URL || 'http://localhost:2024';

// ==================================
// Helpers
// ==================================

/**
 * FR: Génère un ID de thread unique
 */
export function generateThreadId(): string {
  return `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * FR: Gère les erreurs API
 */
async function handleApiError(response: Response): Promise<never> {
  const error: ApiError = {
    message: `Erreur API: ${response.statusText}`,
    status: response.status,
  };
  
  try {
    const data = await response.json();
    error.details = data;
    error.message = data.message || error.message;
  } catch {
    // FR: Impossible de parser la réponse
  }
  
  throw error;
}

// ==================================
// Upload de fichiers
// ==================================

/**
 * FR: Upload les fichiers sur le serveur
 */
export async function uploadFiles(
  excelFile: File,
  pdfJsonFiles: File[],
  companyName: string
): Promise<UploadFilesResponse> {
  // FR: Créer un FormData avec tous les fichiers
  const formData = new FormData();
  formData.append('excel', excelFile);
  formData.append('company_name', companyName);
  
  // FR: Ajouter les fichiers PDF/JSON (max 5)
  pdfJsonFiles.forEach((file, index) => {
    formData.append(`pdf_json_${index}`, file);
  });
  
  // FR: Appeler l'endpoint d'upload
  const response = await fetch(`${LANGGRAPH_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    await handleApiError(response);
  }
  
  return await response.json();
}

// ==================================
// Exécution du workflow LangGraph
// ==================================

/**
 * FR: Exécute le workflow LangGraph avec un input donné
 * Utilise l'API stateless /runs/wait (recommandée)
 */
async function runWorkflow(
  threadId: string,
  input: WorkflowInput
): Promise<WorkflowOutput> {
  // FR: POST /runs/wait (API stateless recommandée)
  const url = `${LANGGRAPH_URL}/runs/wait`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      assistant_id: 'need_analysis',  // FR: Nom du graphe dans langgraph.json
      input,
    }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Erreur API:', response.status, errorText);
    await handleApiError(response);
  }
  
  // FR: Parser la réponse directe (pas d'array d'événements)
  const data = await response.json();
  
  return data as WorkflowOutput;
}

// ==================================
// Génération de besoins
// ==================================

/**
 * FR: Génère les 10 besoins initiaux
 */
export async function generateNeeds(
  request: GenerateNeedsRequest,
  threadId?: string
): Promise<{ needs: Need[]; threadId: string }> {
  const tid = threadId || generateThreadId();
  
  const input: WorkflowInput = {
    excel_file_path: request.excel_file_path,
    pdf_json_file_paths: request.pdf_json_file_paths,
    company_name: request.company_name,
    action: 'generate_needs',
  };
  
  const output = await runWorkflow(tid, input);
  
  return {
    needs: output.needs || [],
    threadId: tid,
  };
}

/**
 * FR: Régénère des besoins (en excluant certains)
 */
export async function regenerateNeeds(
  request: RegenerateNeedsRequest,
  threadId: string
): Promise<{ needs: Need[] }> {
  const input: WorkflowInput = {
    action: 'regenerate_needs',
    excluded_needs: request.excluded_needs,
    user_comment: request.user_comment,
  };
  
  const output = await runWorkflow(threadId, input);
  
  return {
    needs: output.needs || [],
  };
}

// ==================================
// Génération de cas d'usage
// ==================================

/**
 * FR: Génère les cas d'usage (Quick Wins + Structuration IA)
 */
export async function generateUseCases(
  request: GenerateUseCasesRequest,
  threadId: string
): Promise<GenerateUseCasesResponse> {
  const input: WorkflowInput = {
    action: 'generate_use_cases',
    validated_needs: request.validated_needs,
  };
  
  const output = await runWorkflow(threadId, input);
  
  return {
    quick_wins: output.quick_wins || [],
    structuration_ia: output.structuration_ia || [],
  };
}

/**
 * FR: Régénère des cas d'usage
 */
export async function regenerateUseCases(
  request: RegenerateUseCasesRequest,
  threadId: string
): Promise<GenerateUseCasesResponse> {
  const input: WorkflowInput = {
    action: 'regenerate_use_cases',
    validated_quick_wins: request.validated_quick_wins,
    validated_structuration_ia: request.validated_structuration_ia,
    user_comment: request.user_comment,
  };
  
  const output = await runWorkflow(threadId, input);
  
  return {
    quick_wins: output.quick_wins || [],
    structuration_ia: output.structuration_ia || [],
  };
}

// ==================================
// Génération du rapport
// ==================================

/**
 * FR: Télécharge le rapport Word
 */
export async function downloadReport(
  validatedNeeds: Need[],
  validatedQuickWins: UseCase[],
  validatedStructurationIA: UseCase[],
  threadId: string
): Promise<Blob> {
  const input: WorkflowInput = {
    action: 'generate_report',
    validated_needs: validatedNeeds,
    validated_quick_wins: validatedQuickWins,
    validated_structuration_ia: validatedStructurationIA,
  };
  
  const output = await runWorkflow(threadId, input);
  
  // FR: Télécharger le fichier depuis le chemin retourné
  if (!output.report_path) {
    throw new Error('Aucun rapport généré');
  }
  
  // TODO: Implémenter le téléchargement réel du fichier
  // Pour l'instant, retourne un blob vide
  return new Blob([], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
}

// ==================================
// Helpers pour UI
// ==================================

/**
 * FR: Vérifie la santé du serveur LangGraph
 */
export async function checkServerHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${LANGGRAPH_URL}/ok`);
    return response.ok;
  } catch {
    return false;
  }
}
