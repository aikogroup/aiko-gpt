import { generateWordReport, ReportData } from './document-generator';

export const LANGGRAPH_API_URL = 'http://127.0.0.1:2024';
const NEXT_API_URL = '/api';

// Interfaces pour les fichiers
interface WorkshopFile {
  name: string;
  path: string;
}

interface TranscriptFile {
  name: string;
  path: string;
}

interface ValidationRequest {
  validated_needs: any[];
  rejected_needs: any[];
  user_feedback: string[];
}

interface RegenerateRequest {
  validated_needs: any[];
  rejected_needs: any[];
  user_feedback: string;
}

interface UseCaseValidationRequest {
  validated_quick_wins: any[];
  validated_structuration_ia: any[];
  rejected_quick_wins: any[];
  rejected_structuration_ia: any[];
  user_feedback: string;
}

// Fonction pour uploader des fichiers via l'API Next.js
export async function uploadFiles(files: File[]): Promise<{workshop_files: string[], transcript_files: string[]}> {
  try {
    const formData = new FormData();
    
    // Ajouter tous les fichiers au FormData
    for (const file of files) {
      formData.append('files', file);
    }
    
    const response = await fetch(`${NEXT_API_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    
    const result = await response.json();
    return {
      workshop_files: result.file_types.workshop || [],
      transcript_files: result.file_types.transcript || []
    };
  } catch (error) {
    console.error('Error uploading files:', error);
    throw error;
  }
}

// Enregistrer le nom de l'entreprise
export async function setCompanyName(name: string): Promise<void> {
  console.log('Company name set:', name);
}

// Démarrer le workflow avec les fichiers via l'API LangGraph
export async function startWorkflowWithFiles(
  workshopFiles: File[], 
  transcriptFiles: File[], 
  companyName: string
): Promise<any> {
  try {
    // Uploader tous les fichiers vers l'API LangGraph
    const allFiles = [...workshopFiles, ...transcriptFiles];
    const { workshop_files, transcript_files } = await uploadFiles(allFiles);
    
    console.log('✅ Fichiers uploadés:', { workshop_files, transcript_files });
    
    // Créer un thread
    const threadResponse = await fetch(`${LANGGRAPH_API_URL}/threads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: `Thread-${companyName}-${Date.now()}`
      })
    });
    
    if (!threadResponse.ok) {
      throw new Error(`Failed to create thread: ${threadResponse.status}`);
    }
    
    const thread = await threadResponse.json();
    console.log('✅ Thread créé:', thread.thread_id);
    
    // Démarrer le workflow
    const workflowResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${thread.thread_id}/runs/wait`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          company_info: { company_name: companyName },
          workshop_files: workshop_files,
          transcript_files: transcript_files
        }
      })
    });
    
    if (!workflowResponse.ok) {
      throw new Error(`Failed to start workflow: ${workflowResponse.status}`);
    }
    
    const result = await workflowResponse.json();
    
    // Sauvegarder le thread_id
    localStorage.setItem('current_thread_id', thread.thread_id);
    console.log('✅ Thread ID sauvegardé:', thread.thread_id);
    
    return {
      success: true,
      thread_id: thread.thread_id,
      state: result
    };
  } catch (error) {
    console.error('Error starting workflow:', error);
    throw error;
  }
}

// Obtenir l'état du thread via l'API LangGraph
export async function getThreadState(threadId?: string): Promise<any> {
  try {
    const currentThreadId = threadId || localStorage.getItem('current_thread_id') || 'default';
    console.log("🔍 Thread ID utilisé:", currentThreadId);
    
    if (currentThreadId === 'default') {
      return { state: { values: {} }, status: 'no_thread' };
    }
    
    const response = await fetch(`${LANGGRAPH_API_URL}/threads/${currentThreadId}/state`);
    if (!response.ok) {
      throw new Error(`Failed to get thread state: ${response.status}`);
    }
    
    const state = await response.json();
    console.log("🔍 État reçu:", state);
    return state;
  } catch (error) {
    console.error('Error getting thread state:', error);
    throw error;
  }
}

// Envoyer la validation des besoins via l'API LangGraph
export async function sendNeedsValidation(validation: ValidationRequest): Promise<any> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    console.log('✅ Validation besoins via LangGraph API...');

    // D'abord, obtenir l'état du thread pour voir s'il y a un run en pause
    const stateResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/state`);
    if (!stateResponse.ok) {
      throw new Error(`Failed to get thread state: ${stateResponse.status}`);
    }
    
    const state = await stateResponse.json();
    console.log('🔍 État du thread:', state);
    
    // NOUVEAU: Toujours envoyer la validation, peu importe l'état du workflow
    console.log('🔄 Envoi de la validation des besoins...');
    
    // Envoyer la validation des besoins
    const response = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          validated_needs: validation.validated_needs,
          rejected_needs: validation.rejected_needs,
          user_feedback: Array.isArray(validation.user_feedback) ? validation.user_feedback.join(' ') : validation.user_feedback,
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to send human validation: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending needs validation:', error);
    throw error;
  }
}

// Envoyer la validation des cas d'usage via l'API LangGraph
export async function sendUseCaseValidation(validation: UseCaseValidationRequest): Promise<any> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    console.log('✅ Validation cas d\'usage via LangGraph API...');

    // Reprendre le workflow avec le feedback de validation
    const response = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          validated_quick_wins: validation.validated_quick_wins,
          validated_structuration_ia: validation.validated_structuration_ia,
          rejected_quick_wins: validation.rejected_quick_wins,
          rejected_structuration_ia: validation.rejected_structuration_ia,
          user_feedback: validation.user_feedback,
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to send use case validation: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending use case validation:', error);
    throw error;
  }
}

// Obtenir le statut du workflow
export async function getWorkflowStatus(threadId: string): Promise<string> {
  try {
    const state = await getThreadState(threadId);
    if (state?.next?.includes('human_validation')) {
      return 'needs_validation';
    }
    if (state?.next?.includes('use_case_validation')) {
      return 'use_case_validation';
    }
    if (!state?.next || state.next.length === 0) {
      return 'completed';
    }
    return 'running';
  } catch (error) {
    console.error('Error getting workflow status:', error);
    return 'error';
  }
}

// Obtenir les résultats du workflow
export async function getWorkflowResults(threadId: string): Promise<any> {
  try {
    const state = await getThreadState(threadId);
    return state?.state?.values;
  } catch (error) {
    console.error('Error getting workflow results:', error);
    throw error;
  }
}

// Télécharger le rapport
export async function downloadReport(threadId: string, reportData?: ReportData): Promise<Blob> {
  console.log(`Téléchargement du rapport pour le thread ${threadId}`);
  
  if (reportData) {
    // Générer le rapport avec les données fournies
    return await generateWordReport(reportData);
  }
  
  // Fallback: rapport simulé si pas de données
  const dummyContent = "Ceci est un rapport simulé pour le thread " + threadId;
  const blob = new Blob([dummyContent], { type: 'text/plain' });
  return blob;
}

// Fonction pour régénérer des besoins
export async function regenerateNeeds(regenerate: RegenerateRequest): Promise<any> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    console.log('🔄 Régénération des besoins via LangGraph API...');

    // D'abord, obtenir l'état du thread pour voir s'il y a un run en pause
    const stateResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/state`);
    if (!stateResponse.ok) {
      throw new Error(`Failed to get thread state: ${stateResponse.status}`);
    }
    
    const state = await stateResponse.json();
    console.log('🔍 État du thread:', state);
    
    // NOUVEAU: Toujours envoyer la régénération, peu importe l'état du workflow
    console.log('🔄 Envoi de la régénération des besoins...');
    
    // Envoyer la régénération des besoins
    const response = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          validated_needs: regenerate.validated_needs,
          rejected_needs: regenerate.rejected_needs,
          user_feedback: regenerate.user_feedback,
          regenerate: true // Flag pour indiquer la régénération
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to regenerate needs: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error regenerating needs:', error);
    throw error;
  }
}

// Fonction pour régénérer des cas d'usage
export async function regenerateUseCases(regenerate: UseCaseValidationRequest): Promise<any> {
  try {
    const threadId = localStorage.getItem('current_thread_id') || 'default';
    console.log('🔄 Régénération des cas d\'usage via LangGraph API...');

    // NOUVEAU: Toujours envoyer la régénération, peu importe l'état du workflow
    console.log('🔄 Envoi de la régénération des cas d\'usage...');
    
    // Envoyer la régénération des cas d'usage
    const response = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          validated_quick_wins: regenerate.validated_quick_wins,
          validated_structuration_ia: regenerate.validated_structuration_ia,
          rejected_quick_wins: regenerate.rejected_quick_wins,
          rejected_structuration_ia: regenerate.rejected_structuration_ia,
          user_feedback: regenerate.user_feedback,
          regenerate_use_cases: true // Flag pour indiquer la régénération des use cases
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to regenerate use cases: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error regenerating use cases:', error);
    throw error;
  }
}

// Fonction de test de connexion
export async function testLangGraphConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${LANGGRAPH_API_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('❌ Erreur connexion API LangGraph:', error);
    return false;
  }
}