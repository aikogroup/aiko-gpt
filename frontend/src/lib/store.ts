/**
 * Store - State management global (Zustand)
 * 
 * FR: Gestion de l'état global de l'application
 */

// TODO (FR): Importer Zustand
// import { create } from 'zustand';
// import { Need, UseCase } from './schemas';

// TODO (FR): Définir l'interface du store
// interface AppState {
//   // FR: Fichiers uploadés
//   excelFileId: string | null;
//   transcriptFileIds: string[];
//   companyName: string;
//   
//   // FR: Besoins
//   needs: Need[];
//   validatedNeeds: Need[];
//   
//   // FR: Cas d'usage
//   quickWins: UseCase[];
//   structurationIA: UseCase[];
//   validatedQuickWins: UseCase[];
//   validatedStructurationIA: UseCase[];
//   
//   // FR: Actions
//   setExcelFileId: (id: string) => void;
//   setTranscriptFileIds: (ids: string[]) => void;
//   setCompanyName: (name: string) => void;
//   setNeeds: (needs: Need[]) => void;
//   setValidatedNeeds: (needs: Need[]) => void;
//   setQuickWins: (useCases: UseCase[]) => void;
//   setStructurationIA: (useCases: UseCase[]) => void;
//   setValidatedQuickWins: (useCases: UseCase[]) => void;
//   setValidatedStructurationIA: (useCases: UseCase[]) => void;
//   
//   // FR: Actions utilitaires
//   toggleNeedSelection: (needId: string) => void;
//   updateNeedTitle: (needId: string, newTitle: string) => void;
//   toggleUseCaseSelection: (useCaseId: string, category: 'quick_win' | 'structuration_ia') => void;
//   
//   // FR: Reset
//   reset: () => void;
// }

// TODO (FR): Créer le store
// export const useStore = create<AppState>((set) => ({
//   // FR: États initiaux
//   excelFileId: null,
//   transcriptFileIds: [],
//   companyName: '',
//   needs: [],
//   validatedNeeds: [],
//   quickWins: [],
//   structurationIA: [],
//   validatedQuickWins: [],
//   validatedStructurationIA: [],
//   
//   // FR: Implémentation des actions
//   setExcelFileId: (id) => set({ excelFileId: id }),
//   // ... etc
//   
//   reset: () => set({
//     excelFileId: null,
//     // ... reset all states
//   }),
// }));

export {};

