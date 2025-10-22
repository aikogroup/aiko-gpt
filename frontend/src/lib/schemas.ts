/**
 * Schemas - Types TypeScript
 * 
 * FR: Définitions de tous les types utilisés dans l'application
 * ⚠️ Correspond aux modèles Pydantic du backend
 */

// ==================================
// Types de base
// ==================================

/**
 * FR: Représente un besoin métier
 */
export interface Need {
  id: string;
  title: string;
  citations: string[];  // Exactement 5 citations
  selected: boolean;
  edited: boolean;
}

/**
 * FR: Catégorie de cas d'usage
 */
export type UseCaseCategory = 'quick_win' | 'structuration_ia';

/**
 * FR: Représente un cas d'usage IA
 */
export interface UseCase {
  id: string;
  category: UseCaseCategory;
  title: string;
  description: string;
  ai_technologies: string[];
  selected: boolean;
}

// ==================================
// LangGraph API Types
// ==================================

/**
 * FR: Configuration pour un run LangGraph
 */
export interface LangGraphConfig {
  configurable: {
    thread_id: string;
  };
}

/**
 * FR: Input state pour le workflow LangGraph
 */
export interface WorkflowInput {
  excel_file_path?: string;
  pdf_json_file_paths?: string[];
  company_name?: string;
  action?: string;
  validated_needs?: Need[];
  validated_quick_wins?: UseCase[];
  validated_structuration_ia?: UseCase[];
  excluded_needs?: string[];
  user_comment?: string;
}

/**
 * FR: Output state du workflow LangGraph
 */
export interface WorkflowOutput {
  needs?: Need[];
  quick_wins?: UseCase[];
  structuration_ia?: UseCase[];
  report_path?: string;
  errors?: string[];
  current_step?: string;
  workshop_data?: any;
  transcript_data?: any;
  web_search_data?: any;
}

// ==================================
// API Requests & Responses
// ==================================

/**
 * FR: Request pour upload de fichiers
 */
export interface UploadFilesRequest {
  excel_file: File;
  pdf_json_files: File[];
}

/**
 * FR: Response après upload de fichiers
 */
export interface UploadFilesResponse {
  excel_file_path: string;
  pdf_json_file_paths: string[];
  company_name: string;
  thread_id: string;
}

/**
 * FR: Request pour générer des besoins
 */
export interface GenerateNeedsRequest {
  excel_file_path: string;
  pdf_json_file_paths: string[];
  company_name: string;
  action: 'generate_needs';
}

/**
 * FR: Response après génération de besoins
 */
export interface GenerateNeedsResponse {
  needs: Need[];
}

/**
 * FR: Request pour régénérer des besoins
 */
export interface RegenerateNeedsRequest {
  excluded_needs: string[];  // Titres des besoins à exclure
  user_comment?: string;
  action: 'regenerate_needs';
}

/**
 * FR: Request pour générer des cas d'usage
 */
export interface GenerateUseCasesRequest {
  validated_needs: Need[];
  action: 'generate_use_cases';
}

/**
 * FR: Response après génération de cas d'usage
 */
export interface GenerateUseCasesResponse {
  quick_wins: UseCase[];
  structuration_ia: UseCase[];
}

/**
 * FR: Request pour régénérer des cas d'usage
 */
export interface RegenerateUseCasesRequest {
  validated_quick_wins: UseCase[];
  validated_structuration_ia: UseCase[];
  user_comment?: string;
  action: 'regenerate_use_cases';
}

/**
 * FR: Request pour télécharger le rapport
 */
export interface DownloadReportRequest {
  validated_needs: Need[];
  validated_quick_wins: UseCase[];
  validated_structuration_ia: UseCase[];
}

// ==================================
// State Management Types
// ==================================

/**
 * FR: État global de l'application
 */
export interface AppState {
  // FR: Thread ID pour LangGraph
  threadId: string | null;
  
  // FR: Fichiers uploadés
  excelFilePath: string | null;
  pdfJsonFilePaths: string[];
  companyName: string;
  
  // FR: Besoins
  needs: Need[];
  validatedNeeds: Need[];
  
  // FR: Cas d'usage
  quickWins: UseCase[];
  structurationIA: UseCase[];
  validatedQuickWins: UseCase[];
  validatedStructurationIA: UseCase[];
  
  // FR: État UI
  isLoading: boolean;
  error: string | null;
  currentStep: 'upload' | 'needs' | 'usecases' | 'results';
}

// ==================================
// Helper Types
// ==================================

/**
 * FR: Type pour les erreurs API
 */
export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}
