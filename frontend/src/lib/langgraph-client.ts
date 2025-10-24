// Client LangGraph TypeScript simplifié
// Utilise fetch directement pour communiquer avec l'API LangGraph

const LANGGRAPH_API_URL = 'http://127.0.0.1:2024';

// Types pour les données
export interface CompanyInfo {
  company_name: string;
}

export interface WorkflowInput {
  company_info: CompanyInfo;
  workshop_files: string[];
  transcript_files: string[];
}

export interface IdentifiedNeed {
  id: string;
  theme: string;
  quotes: string[];
}

export interface ValidationRequest {
  validated_needs: IdentifiedNeed[];
  rejected_needs: IdentifiedNeed[];
  user_feedback: string[];
}

export interface UseCaseValidationRequest {
  validated_quick_wins: any[];
  validated_structuration_ia: any[];
  rejected_quick_wins: any[];
  rejected_structuration_ia: any[];
  user_feedback: string;
}

// Fonction pour créer un thread et démarrer le workflow
export async function createThreadAndDispatch(
  companyName: string,
  workshopFiles: string[],
  transcriptFiles: string[]
): Promise<{ threadId: string; state: any }> {
  try {
    // Créer un nouveau thread avec un nom
    const threadResponse = await fetch(`${LANGGRAPH_API_URL}/threads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: `Thread-${Date.now()}`
      })
    });
    
    if (!threadResponse.ok) {
      const errorText = await threadResponse.text();
      console.error('❌ Erreur création thread:', errorText);
      throw new Error(`Failed to create thread: ${threadResponse.status} - ${errorText}`);
    }
    
    const thread = await threadResponse.json();
    console.log('✅ Thread créé:', thread.thread_id);
    
    // Démarrer le workflow avec wait() directement
    const runResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${thread.thread_id}/runs/wait`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: {
          company_info: { company_name: companyName },
          workshop_files: workshopFiles,
          transcript_files: transcriptFiles
        }
      })
    });
    
    if (!runResponse.ok) {
      const errorText = await runResponse.text();
      console.error('❌ Erreur démarrage workflow:', errorText);
      throw new Error(`Failed to start workflow: ${runResponse.status} - ${errorText}`);
    }
    
    const state = await runResponse.json();
    console.log('✅ Workflow terminé avec', state.state?.values?.identified_needs?.length || 0, 'besoins identifiés');
    
    return {
      threadId: thread.thread_id,
      state: state
    };
  } catch (error) {
    console.error('Error in createThreadAndDispatch:', error);
    throw error;
  }
}

// Fonction pour obtenir l'état d'un thread
export async function getThreadState(threadId: string): Promise<any> {
  try {
    const response = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/state`);
    
    if (!response.ok) {
      throw new Error(`Failed to get thread state: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting thread state:', error);
    throw error;
  }
}

// Fonction pour valider les besoins
export async function humanValidation(
  threadId: string,
  validatedNeeds: IdentifiedNeed[],
  rejectedNeeds: IdentifiedNeed[],
  userFeedback: string[]
): Promise<any> {
  try {
    // Mettre à jour l'état du thread
    const updateResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/state`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        values: {
          validated_needs: validatedNeeds,
          rejected_needs: rejectedNeeds,
          user_feedback: userFeedback
        }
      })
    });
    
    if (!updateResponse.ok) {
      throw new Error(`Failed to update thread state: ${updateResponse.status}`);
    }
    
    // Reprendre l'exécution
    const runResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: null
      })
    });
    
    if (!runResponse.ok) {
      throw new Error(`Failed to resume workflow: ${runResponse.status}`);
    }
    
    return await runResponse.json();
  } catch (error) {
    console.error('Error in humanValidation:', error);
    throw error;
  }
}

// Fonction pour valider les cas d'usage
export async function useCaseValidation(
  threadId: string,
  validatedQuickWins: any[],
  validatedStructurationIa: any[],
  rejectedQuickWins: any[],
  rejectedStructurationIa: any[],
  userFeedback: string
): Promise<any> {
  try {
    // Mettre à jour l'état du thread
    const updateResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/state`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        values: {
          validated_quick_wins: validatedQuickWins,
          validated_structuration_ia: validatedStructurationIa,
          rejected_quick_wins: rejectedQuickWins,
          rejected_structuration_ia: rejectedStructurationIa,
          user_feedback: [userFeedback]
        }
      })
    });
    
    if (!updateResponse.ok) {
      throw new Error(`Failed to update thread state: ${updateResponse.status}`);
    }
    
    // Reprendre l'exécution
    const runResponse = await fetch(`${LANGGRAPH_API_URL}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: 'need_analysis',
        input: null
      })
    });
    
    if (!runResponse.ok) {
      throw new Error(`Failed to resume workflow: ${runResponse.status}`);
    }
    
    return await runResponse.json();
  } catch (error) {
    console.error('Error in useCaseValidation:', error);
    throw error;
  }
}

// Fonction pour tester la connexion
export async function testConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${LANGGRAPH_API_URL}/threads`);
    return response.ok;
  } catch (error) {
    console.error('❌ Erreur connexion LangGraph:', error);
    return false;
  }
}