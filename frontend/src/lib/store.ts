/**
 * Store - State management global (Zustand)
 * 
 * FR: Gestion de l'état global de l'application
 */

import { create } from 'zustand';
import type { Need, UseCase, UseCaseCategory } from './schemas';

// ==================================
// Interface du store
// ==================================

interface AppState {
  // FR: Thread ID LangGraph
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
  
  // ==================================
  // Actions
  // ==================================
  
  // FR: Thread management
  setThreadId: (id: string) => void;
  
  // FR: Upload
  setExcelFilePath: (path: string) => void;
  setPdfJsonFilePaths: (paths: string[]) => void;
  setCompanyName: (name: string) => void;
  
  // FR: Besoins
  setNeeds: (needs: Need[]) => void;
  setValidatedNeeds: (needs: Need[]) => void;
  toggleNeedSelection: (needId: string) => void;
  updateNeedTitle: (needId: string, newTitle: string) => void;
  
  // FR: Cas d'usage
  setQuickWins: (useCases: UseCase[]) => void;
  setStructurationIA: (useCases: UseCase[]) => void;
  setValidatedQuickWins: (useCases: UseCase[]) => void;
  setValidatedStructurationIA: (useCases: UseCase[]) => void;
  toggleUseCaseSelection: (useCaseId: string, category: UseCaseCategory) => void;
  
  // FR: UI
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCurrentStep: (step: 'upload' | 'needs' | 'usecases' | 'results') => void;
  
  // FR: Reset
  reset: () => void;
}

// ==================================
// Création du store
// ==================================

const initialState = {
  threadId: null,
  excelFilePath: null,
  pdfJsonFilePaths: [],
  companyName: '',
  needs: [],
  validatedNeeds: [],
  quickWins: [],
  structurationIA: [],
  validatedQuickWins: [],
  validatedStructurationIA: [],
  isLoading: false,
  error: null,
  currentStep: 'upload' as const,
};

export const useStore = create<AppState>((set) => ({
  // FR: États initiaux
  ...initialState,
  
  // ==================================
  // Implémentation des actions
  // ==================================
  
  // FR: Thread management
  setThreadId: (id) => set({ threadId: id }),
  
  // FR: Upload
  setExcelFilePath: (path) => set({ excelFilePath: path }),
  setPdfJsonFilePaths: (paths) => set({ pdfJsonFilePaths: paths }),
  setCompanyName: (name) => set({ companyName: name }),
  
  // FR: Besoins
  setNeeds: (needs) => set({ needs }),
  
  setValidatedNeeds: (validatedNeeds) => set({ validatedNeeds }),
  
  toggleNeedSelection: (needId) =>
    set((state) => ({
      needs: state.needs.map((need) =>
        need.id === needId ? { ...need, selected: !need.selected } : need
      ),
    })),
  
  updateNeedTitle: (needId, newTitle) =>
    set((state) => ({
      needs: state.needs.map((need) =>
        need.id === needId ? { ...need, title: newTitle, edited: true } : need
      ),
    })),
  
  // FR: Cas d'usage
  setQuickWins: (quickWins) => set({ quickWins }),
  
  setStructurationIA: (structurationIA) => set({ structurationIA }),
  
  setValidatedQuickWins: (validatedQuickWins) => set({ validatedQuickWins }),
  
  setValidatedStructurationIA: (validatedStructurationIA) =>
    set({ validatedStructurationIA }),
  
  toggleUseCaseSelection: (useCaseId, category) =>
    set((state) => {
      if (category === 'quick_win') {
        return {
          quickWins: state.quickWins.map((uc) =>
            uc.id === useCaseId ? { ...uc, selected: !uc.selected } : uc
          ),
        };
      } else {
        return {
          structurationIA: state.structurationIA.map((uc) =>
            uc.id === useCaseId ? { ...uc, selected: !uc.selected } : uc
          ),
        };
      }
    }),

  // FR: Mise à jour des cas d'usage
  updateUseCaseTitle: (useCaseId, newTitle, category) =>
    set((state) => {
      if (category === 'quick_win') {
        return {
          quickWins: state.quickWins.map((uc) =>
            uc.id === useCaseId ? { ...uc, title: newTitle, edited: true } : uc
          ),
        };
      } else {
        return {
          structurationIA: state.structurationIA.map((uc) =>
            uc.id === useCaseId ? { ...uc, title: newTitle, edited: true } : uc
          ),
        };
      }
    }),

  updateUseCaseDescription: (useCaseId, newDescription, category) =>
    set((state) => {
      if (category === 'quick_win') {
        return {
          quickWins: state.quickWins.map((uc) =>
            uc.id === useCaseId ? { ...uc, description: newDescription, edited: true } : uc
          ),
        };
      } else {
        return {
          structurationIA: state.structurationIA.map((uc) =>
            uc.id === useCaseId ? { ...uc, description: newDescription, edited: true } : uc
          ),
        };
      }
    }),

  updateUseCaseTechnologies: (useCaseId, newTechnologies, category) =>
    set((state) => {
      const technologies = newTechnologies.split(',').map(tech => tech.trim()).filter(tech => tech);
      if (category === 'quick_win') {
        return {
          quickWins: state.quickWins.map((uc) =>
            uc.id === useCaseId ? { ...uc, ai_technologies: technologies, edited: true } : uc
          ),
        };
      } else {
        return {
          structurationIA: state.structurationIA.map((uc) =>
            uc.id === useCaseId ? { ...uc, ai_technologies: technologies, edited: true } : uc
          ),
        };
      }
    }),
  
  // FR: UI
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  setCurrentStep: (currentStep) => set({ currentStep }),
  
  // FR: Reset complet
  reset: () => set(initialState),
}));

// ==================================
// Selectors utiles
// ==================================

/**
 * FR: Récupère les besoins sélectionnés
 */
export const getSelectedNeeds = (state: AppState): Need[] =>
  state.needs.filter((need) => need.selected);

/**
 * FR: Récupère les cas d'usage sélectionnés
 */
export const getSelectedUseCases = (
  state: AppState
): { quickWins: UseCase[]; structurationIA: UseCase[] } => ({
  quickWins: state.quickWins.filter((uc) => uc.selected),
  structurationIA: state.structurationIA.filter((uc) => uc.selected),
});
