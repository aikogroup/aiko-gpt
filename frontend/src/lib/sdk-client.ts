// Client utilisant le SDK LangGraph directement
// Nécessite d'installer @langchain/langgraph-sdk

import { getClient } from '@langchain/langgraph-sdk';

// Configuration
const LANGGRAPH_URL = 'http://127.0.0.1:2024';

// Client SDK
export class SDKClient {
  private client: any;

  constructor() {
    this.client = getClient({ url: LANGGRAPH_URL });
  }

  // Créer un thread et démarrer le workflow
  async createThreadAndDispatch(
    companyName: string,
    workshopFiles: string[],
    transcriptFiles: string[]
  ): Promise<{ thread_id: string; state: any }> {
    try {
      // Créer le thread
      const thread = await this.client.threads.create();
      const thread_id = thread.thread_id;

      // Démarrer le workflow
      const state = await this.client.runs.wait(
        thread_id,
        'need_analysis',
        {
          company_info: { company_name: companyName },
          workshop_files: workshopFiles,
          transcript_files: transcriptFiles
        }
      );

      return { thread_id, state };
    } catch (error) {
      console.error('Error creating thread and dispatching:', error);
      throw error;
    }
  }

  // Obtenir l'état du thread
  async getThreadState(threadId: string): Promise<any> {
    try {
      return await this.client.threads.getState(threadId);
    } catch (error) {
      console.error('Error getting thread state:', error);
      throw error;
    }
  }

  // Mettre à jour l'état du thread
  async updateThreadState(
    threadId: string, 
    values: Record<string, any>
  ): Promise<any> {
    try {
      return await this.client.threads.updateState(threadId, values);
    } catch (error) {
      console.error('Error updating thread state:', error);
      throw error;
    }
  }

  // Reprendre l'exécution
  async resumeWorkflow(threadId: string): Promise<any> {
    try {
      return await this.client.runs.wait(threadId, 'need_analysis', null);
    } catch (error) {
      console.error('Error resuming workflow:', error);
      throw error;
    }
  }
}

// Instance globale
export const sdkClient = new SDKClient();
