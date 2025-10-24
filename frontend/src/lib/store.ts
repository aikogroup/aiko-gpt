import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UiStore {
  // Files
  excelFile: File | null;
  transcriptFiles: File[];
  companyName: string;
  
  // State
  isBusy: boolean;
  phase: 'upload' | 'needs' | 'usecases' | 'results';
  
  // Persisted selections
  selectedNeeds: any[];
  selectedUseCases: any[];
  
  // Actions
  setExcelFile: (file: File | null) => void;
  setTranscriptFiles: (files: File[]) => void;
  setCompanyName: (name: string) => void;
  setIsBusy: (busy: boolean) => void;
  setPhase: (phase: 'upload' | 'needs' | 'usecases' | 'results') => void;
  setSelectedNeeds: (needs: any[]) => void;
  setSelectedUseCases: (useCases: any[]) => void;
  
  // Reset
  reset: () => void;
}

export const useUiStore = create<UiStore>()(
  persist(
    (set) => ({
      // Initial state
      excelFile: null,
      transcriptFiles: [],
      companyName: '',
      isBusy: false,
      phase: 'upload',
      selectedNeeds: [],
      selectedUseCases: [],
      
      // Actions
      setExcelFile: (file) => set({ excelFile: file }),
      setTranscriptFiles: (files) => set({ transcriptFiles: files }),
      setCompanyName: (name) => set({ companyName: name }),
      setIsBusy: (busy) => set({ isBusy: busy }),
      setPhase: (phase) => set({ phase }),
      setSelectedNeeds: (needs) => set({ selectedNeeds: needs }),
      setSelectedUseCases: (useCases) => set({ selectedUseCases: useCases }),
      
      // Reset
      reset: () => set({
        excelFile: null,
        transcriptFiles: [],
        companyName: '',
        isBusy: false,
        phase: 'upload'
      })
    }),
    {
      name: 'aiko-ui-store',
      partialize: (state) => ({
        companyName: state.companyName,
        phase: state.phase
      })
    }
  )
);
