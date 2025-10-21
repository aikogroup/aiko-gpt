/**
 * Schemas - Types TypeScript
 * 
 * FR: Définitions de tous les types utilisés dans l'application
 * ⚠️ Doit correspondre aux modèles Pydantic du backend
 */

// TODO (FR): Type Need (Besoin)
// export interface Need {
//   id: string;
//   title: string;
//   citations: string[];  // Exactement 5 citations
//   selected: boolean;
//   edited: boolean;
// }

// TODO (FR): Type UseCase (Cas d'usage)
// export type UseCaseCategory = 'quick_win' | 'structuration_ia';
//
// export interface UseCase {
//   id: string;
//   category: UseCaseCategory;
//   title: string;
//   description: string;
//   ai_technologies: string[];
//   selected: boolean;
// }

// TODO (FR): Types pour les requêtes API

// TODO (FR): Request - Upload files
// export interface UploadFilesRequest {
//   excel_file: File;
//   pdf_json_files: File[];
// }

// TODO (FR): Response - Upload files
// export interface UploadFilesResponse {
//   excel_id: string;
//   transcript_ids: string[];
// }

// TODO (FR): Request - Generate needs
// export interface GenerateNeedsRequest {
//   excel_id: string;
//   transcript_ids: string[];
//   company_name: string;
// }

// TODO (FR): Response - Generate needs
// export interface GenerateNeedsResponse {
//   needs: Need[];
// }

// TODO (FR): Request - Regenerate needs
// export interface RegenerateNeedsRequest {
//   excluded_needs: string[];  // IDs des besoins à exclure
//   comment?: string;
// }

// TODO (FR): Request - Generate use cases
// export interface GenerateUseCasesRequest {
//   validated_needs: Need[];
// }

// TODO (FR): Response - Generate use cases
// export interface GenerateUseCasesResponse {
//   quick_wins: UseCase[];
//   structuration_ia: UseCase[];
// }

// TODO (FR): Request - Regenerate use cases
// export interface RegenerateUseCasesRequest {
//   validated_quick_wins: UseCase[];
//   validated_structuration_ia: UseCase[];
//   comment?: string;
// }

// TODO (FR): Request - Download report
// export interface DownloadReportRequest {
//   validated_needs: Need[];
//   validated_use_cases: {
//     quick_wins: UseCase[];
//     structuration_ia: UseCase[];
//   };
// }

export {};

