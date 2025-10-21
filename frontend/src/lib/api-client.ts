/**
 * API Client - Appels vers le backend
 * 
 * FR: Fonctions pour communiquer avec l'API backend
 */

// TODO (FR): Configurer l'URL du backend
// const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// TODO (FR): Fonction uploadFiles()
// export async function uploadFiles(
//   excelFile: File,
//   pdfJsonFiles: File[]
// ): Promise<{ excel_id: string; transcript_ids: string[] }> {
//   // TODO (FR): Créer FormData
//   // TODO (FR): POST /api/upload
//   // TODO (FR): Retourner les IDs
// }

// TODO (FR): Fonction generateNeeds()
// export async function generateNeeds(
//   excelId: string,
//   transcriptIds: string[],
//   companyName: string
// ): Promise<{ needs: Need[] }> {
//   // TODO (FR): POST /api/run avec action "generate_needs"
//   // TODO (FR): Retourner les besoins générés
// }

// TODO (FR): Fonction regenerateNeeds()
// export async function regenerateNeeds(
//   excludedNeeds: string[],
//   comment?: string
// ): Promise<{ needs: Need[] }> {
//   // TODO (FR): POST /api/run avec action "regenerate_needs"
//   // TODO (FR): Retourner les nouveaux besoins
// }

// TODO (FR): Fonction generateUseCases()
// export async function generateUseCases(
//   validatedNeeds: Need[]
// ): Promise<{ quick_wins: UseCase[]; structuration_ia: UseCase[] }> {
//   // TODO (FR): POST /api/run avec action "generate_use_cases"
//   // TODO (FR): Retourner les cas d'usage
// }

// TODO (FR): Fonction regenerateUseCases()
// export async function regenerateUseCases(
//   validatedQuickWins: UseCase[],
//   validatedStructurationIA: UseCase[],
//   comment?: string
// ): Promise<{ quick_wins: UseCase[]; structuration_ia: UseCase[] }> {
//   // TODO (FR): POST /api/run avec action "regenerate_use_cases"
//   // TODO (FR): Logique intelligente (>= 5 validés)
//   // TODO (FR): Retourner les cas d'usage
// }

// TODO (FR): Fonction downloadReport()
// export async function downloadReport(
//   validatedNeeds: Need[],
//   validatedUseCases: { quick_wins: UseCase[]; structuration_ia: UseCase[] }
// ): Promise<Blob> {
//   // TODO (FR): GET /api/report
//   // TODO (FR): Retourner le blob pour téléchargement
// }

export {};

