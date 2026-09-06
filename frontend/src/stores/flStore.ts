import { create } from 'zustand';

interface FLState {
  isTraining: boolean;
  currentRound: number;
  totalRounds: number;
  globalAccuracy: number;
  globalF1: number;
  activeClients: number;
  strategy: string;
  trainingLog: string[];
  setTraining: (v: boolean) => void;
  updateProgress: (data: any) => void;
  addLog: (msg: string) => void;
  setStrategy: (s: string) => void;
}

export const useFLStore = create<FLState>((set) => ({
  isTraining: false, currentRound: 0, totalRounds: 10,
  globalAccuracy: 0, globalF1: 0, activeClients: 0,
  strategy: 'qapfl', trainingLog: [],
  setTraining: (v) => set({ isTraining: v }),
  updateProgress: (data) => set({
    currentRound: data.round ?? 0,
    globalAccuracy: data.global_accuracy ?? 0,
    globalF1: data.global_f1 ?? 0,
    activeClients: data.active_clients ?? 0,
  }),
  addLog: (msg) => set((s) => ({ trainingLog: [...s.trainingLog.slice(-99), msg] })),
  setStrategy: (strategy) => set({ strategy }),
}));