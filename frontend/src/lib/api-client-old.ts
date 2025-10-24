// API client pour communiquer avec le backend LangGraph
// Ce module adapte les fonctions de client.py pour le frontend

interface WorkshopFile {
  name: string;
  path: string;
}

interface TranscriptFile {
  name: string;
  path: string;
}

interface CompanyInfo {
  company_name: string;
}

interface IdentifiedNeed {
  id: string;
  theme: string;
  quotes: string[];
}

interface ValidationRequest {
  validated_needs: IdentifiedNeed[];
  rejected_needs: IdentifiedNeed[];
  user_feedback: string[];
}

interface UseCaseValidationRequest {
  validated_quick_wins: any[];
  validated_structuration_ia: any[];
  rejected_quick_wins: any[];
  rejected_structuration_ia: any[];
  user_feedback: string;
}

// Configuration de l'API
const API_BASE_URL = 'http://127.0.0.1:2024';

// Fonction pour créer un client LangGraph
async function getLangGraphClient() {
  // Pour le frontend, nous allons utiliser fetch directement
  // car nous ne pouvons pas importer le SDK LangGraph côté client
  return {
    baseUrl: API_BASE_URL
  };
}

// Upload de fichiers (simulation - à adapter selon votre API)
export async function uploadFiles(files: File[]): Promise<{ file_types: { workshop?: string[], transcript?: string[] } }> {
  // Simulation de l'upload - à remplacer par votre logique d'upload réelle
  const workshopPaths: string[] = [];
  const transcriptPaths: string[] = [];
  
  for (const file of files) {
    if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      workshopPaths.push(`/uploads/${file.name}`);
    } else if (file.name.endsWith('.pdf') || file.name.endsWith('.json')) {
      transcriptPaths.push(`/uploads/${file.name}`);
    }
  }
  
  return {
    file_types: {
      workshop: workshopPaths,
      transcript: transcriptPaths
    }
  };
}

// Enregistrer le nom de l'entreprise
export async function setCompanyName(name: string): Promise<void> {
  // Stockage local - déjà géré par le store Zustand
  console.log('Company name set:', name);
}

// Démarrer le workflow avec les fichiers
export async function startWorkflowWithFiles(
  workshopPaths: string[], 
  transcriptPaths: string[], 
  companyName: string
): Promise<Response> {
  try {
    const response = await fetch(`${API_BASE_URL}/threads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          company_info: { company_name: companyName },
          workshop_files: workshopPaths,
          transcript_files: transcriptPaths
        }
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      // Stocker le thread_id pour les requêtes suivantes
      localStorage.setItem('current_thread_id', result.thread_id);
    }
    
    return response;
  } catch (error) {
    console.error('Error starting workflow:', error);
    throw error;
  }
}

// Obtenir l'état du thread
export async function getThreadState(threadId?: string): Promise<any> {
  try {
    // Si pas de threadId, on essaie de récupérer depuis le localStorage ou on utilise un ID par défaut
    const currentThreadId = threadId || localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${currentThreadId}/state`);
    
    if (!response.ok) {
      throw new Error(`Failed to get thread state: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting thread state:', error);
    throw error;
  }
}

// Envoyer la validation des besoins
export async function sendNeedsValidation(validation: ValidationRequest): Promise<Response> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/validate-needs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        validated_needs: validation.validated_needs,
        rejected_needs: validation.rejected_needs,
        user_feedback: validation.user_feedback.join(' ')
      })
    });
    
    return response;
  } catch (error) {
    console.error('Error sending needs validation:', error);
    throw error;
  }
}

// Envoyer la validation des cas d'usage
export async function sendUseCaseValidation(validation: UseCaseValidationRequest): Promise<Response> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/validate-use-cases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        validated_quick_wins: validation.validated_quick_wins,
        validated_structuration_ia: validation.validated_structuration_ia,
        rejected_quick_wins: validation.rejected_quick_wins,
        rejected_structuration_ia: validation.rejected_structuration_ia,
        user_feedback: validation.user_feedback
      })
    });
    
    return response;
  } catch (error) {
    console.error('Error sending use case validation:', error);
    throw error;
  }
}

// Obtenir le rapport final
export async function getFinalReport(threadId?: string): Promise<any> {
  try {
    const currentThreadId = threadId || localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${currentThreadId}/state`);
    
    if (!response.ok) {
      throw new Error(`Failed to get final report: ${response.status}`);
    }
    
    const state = await response.json();
    return state;
  } catch (error) {
    console.error('Error getting final report:', error);
    throw error;
  }
}

// Obtenir le statut du workflow
export async function getWorkflowStatus(): Promise<Response> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/state`);
    
    if (!response.ok) {
      throw new Error(`Failed to get workflow status: ${response.status}`);
    }
    
    return response;
  } catch (error) {
    console.error('Error getting workflow status:', error);
    throw error;
  }
}

// Obtenir les résultats du workflow
export async function getWorkflowResults(): Promise<Response> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/state`);
    
    if (!response.ok) {
      throw new Error(`Failed to get workflow results: ${response.status}`);
    }
    
    return response;
  } catch (error) {
    console.error('Error getting workflow results:', error);
    throw error;
  }
}

// Télécharger le rapport
export async function downloadReport(): Promise<Blob> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/threads/${threadId}/download`);
    
    if (!response.ok) {
      throw new Error(`Failed to download report: ${response.status}`);
    }
    
    return await response.blob();
  } catch (error) {
    console.error('Error downloading report:', error);
    throw error;
  }
}
