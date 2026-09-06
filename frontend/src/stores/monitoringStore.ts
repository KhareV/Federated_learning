import { create } from 'zustand';

const MAX_BUFFER = 1250; // 5 seconds at 250Hz for ECG

interface MonitoringState {
  isMonitoring: boolean;
  liveHR: number;
  liveSPO2: number;
  liveECGBuffer: number[];
  livePPGBuffer: number[];
  ecgSQI: number;
  ppgSQI: number;
  overallSQI: number;
  qualityLabel: string;
  anomalyScore: number;
  anomalyClass: string;
  confidence: number;
  lastUpdated: Date | null;
  setMonitoring: (v: boolean) => void;
  updateLiveData: (data: any) => void;
  appendECGSamples: (samples: number[]) => void;
  appendPPGSamples: (samples: number[]) => void;
}

export const useMonitoringStore = create<MonitoringState>((set) => ({
  isMonitoring: false,
  liveHR: 0, liveSPO2: 0,
  liveECGBuffer: [], livePPGBuffer: [],
  ecgSQI: 0, ppgSQI: 0, overallSQI: 0,
  qualityLabel: 'UNKNOWN',
  anomalyScore: 0, anomalyClass: 'NORMAL', confidence: 0,
  lastUpdated: null,
  setMonitoring: (v) => set({ isMonitoring: v }),
  updateLiveData: (data) => set({
    liveHR: data.hr ?? 0,
    liveSPO2: data.spo2 ?? 0,
    ecgSQI: data.ecg_sqi ?? 0,
    ppgSQI: data.ppg_sqi ?? 0,
    overallSQI: data.overall_sqi ?? 0,
    qualityLabel: data.quality_label ?? 'UNKNOWN',
    anomalyScore: data.anomaly_score ?? 0,
    anomalyClass: data.anomaly_class ?? 'NORMAL',
    confidence: data.confidence ?? 0,
    lastUpdated: new Date(),
  }),
  appendECGSamples: (samples) => set((state) => ({
    liveECGBuffer: [...state.liveECGBuffer, ...samples].slice(-MAX_BUFFER)
  })),
  appendPPGSamples: (samples) => set((state) => ({
    livePPGBuffer: [...state.livePPGBuffer, ...samples].slice(-250)
  })),
}));