import { create } from "zustand";
import { persist } from "zustand/middleware";

type UiState = {
  excelFile: File | null;
  transcriptFiles: File[];
  companyName: string;
  isBusy: boolean;
  phase: "start" | "needs" | "usecases" | "done";
  persistedSelectedNeeds: any[];
  persistedSelectedUseCases: any[];
  setExcelFile: (f: File | null) => void;
  setTranscriptFiles: (fs: File[]) => void;
  setCompanyName: (n: string) => void;
  setIsBusy: (b: boolean) => void;
  setPhase: (p: UiState["phase"]) => void;
  setPersistedSelectedNeeds: (needs: any[]) => void;
  setPersistedSelectedUseCases: (useCases: any[]) => void;
};

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      excelFile: null,
      transcriptFiles: [],
      companyName: "",
      isBusy: false,
      phase: "start",
      persistedSelectedNeeds: [],
      persistedSelectedUseCases: [],
      setExcelFile: (f) => set({ excelFile: f }),
      setTranscriptFiles: (fs) => set({ transcriptFiles: fs }),
      setCompanyName: (n) => set({ companyName: n }),
      setIsBusy: (b) => set({ isBusy: b }),
      setPhase: (p) => set({ phase: p }),
      setPersistedSelectedNeeds: (needs) => set({ persistedSelectedNeeds: Array.isArray(needs) ? needs : [] }),
      setPersistedSelectedUseCases: (useCases) => set({ persistedSelectedUseCases: Array.isArray(useCases) ? useCases : [] }),
    }),
    {
      name: "aiko-ui-storage",
      // Ne pas persister les fichiers (trop volumineux) et isBusy (état temporaire)
      partialize: (state) => ({
        companyName: state.companyName,
        phase: state.phase,
        persistedSelectedNeeds: Array.isArray(state.persistedSelectedNeeds) ? state.persistedSelectedNeeds : [],
        persistedSelectedUseCases: Array.isArray(state.persistedSelectedUseCases) ? state.persistedSelectedUseCases : [],
      }),
    }
  )
);


