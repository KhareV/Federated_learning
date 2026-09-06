import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, Activity, Heart, Droplets, Clock, Shield, AlertTriangle } from 'lucide-react';
import { flApi, baselineApi } from '../../services/api';

const MOCK_PATIENTS = [
  { id: 'client_01', name: 'Alice (Client 01)', device: 'ESP32_001', status: 'monitoring', duration: '3h 42m', avatar: 'A' },
  { id: 'client_02', name: 'Bob (Client 02)', device: 'ESP32_002', status: 'monitoring', duration: '2h 15m', avatar: 'B' },
  { id: 'client_03', name: 'Carol (Client 03)', device: 'ESP32_003', status: 'poor_quality', duration: '1h 08m', avatar: 'C' },
  { id: 'client_04', name: 'David (Client 04)', device: 'ESP32_004', status: 'monitoring', duration: '4h 21m', avatar: 'D' },
  { id: 'client_05', name: 'Eve (Client 05)', device: 'ESP32_005', status: 'low_battery', duration: '0h 55m', avatar: 'E' },
  { id: 'client_06', name: 'Frank (Client 06)', device: 'ESP32_006', status: 'monitoring', duration: '5h 02m', avatar: 'F' },
  { id: 'client_07', name: 'Grace (Client 07)', device: 'ESP32_007', status: 'monitoring', duration: '2h 38m', avatar: 'G' },
  { id: 'client_08', name: 'Henry (Client 08)', device: 'ESP32_008', status: 'poor_quality', duration: '1h 44m', avatar: 'H' },
];

const BASELINES: Record<string, any> = {
  client_01: { hr_mean: 68, hr_std: 5, hr_min: 55, hr_max: 82, spo2_mean: 98.2, spo2_std: 0.5, hrv_sdnn: 45, hrv_rmssd: 38, samples: 5000, model_version: 'v3', personalization_rounds: 7 },
  client_02: { hr_mean: 75, hr_std: 8, hr_min: 58, hr_max: 96, spo2_mean: 97.5, spo2_std: 0.8, hrv_sdnn: 38, hrv_rmssd: 31, samples: 7000, model_version: 'v3', personalization_rounds: 5 },
  client_03: { hr_mean: 82, hr_std: 12, hr_min: 60, hr_max: 108, spo2_mean: 97.0, spo2_std: 1.2, hrv_sdnn: 52, hrv_rmssd: 44, samples: 4000, model_version: 'v2', personalization_rounds: 3 },
  client_04: { hr_mean: 62, hr_std: 4, hr_min: 52, hr_max: 74, spo2_mean: 98.8, spo2_std: 0.4, hrv_sdnn: 41, hrv_rmssd: 35, samples: 3500, model_version: 'v3', personalization_rounds: 4 },
  client_05: { hr_mean: 71, hr_std: 6, hr_min: 58, hr_max: 86, spo2_mean: 97.8, spo2_std: 0.6, hrv_sdnn: 36, hrv_rmssd: 29, samples: 2000, model_version: 'v1', personalization_rounds: 2 },
  client_06: { hr_mean: 92, hr_std: 10, hr_min: 70, hr_max: 115, spo2_mean: 97.2, spo2_std: 0.9, hrv_sdnn: 49, hrv_rmssd: 41, samples: 6000, model_version: 'v3', personalization_rounds: 6 },
  client_07: { hr_mean: 70, hr_std: 7, hr_min: 55, hr_max: 88, spo2_mean: 96.5, spo2_std: 1.5, hrv_sdnn: 44, hrv_rmssd: 37, samples: 5500, model_version: 'v3', personalization_rounds: 5 },
  client_08: { hr_mean: 78, hr_std: 9, hr_min: 60, hr_max: 100, spo2_mean: 97.6, spo2_std: 1.0, hrv_sdnn: 47, hrv_rmssd: 39, samples: 4500, model_version: 'v2', personalization_rounds: 4 },
};

const STATUS_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
  monitoring: { label: 'Monitoring', color: 'text-green-400', dot: 'bg-green-400' },
  poor_quality: { label: 'Poor Signal', color: 'text-amber-400', dot: 'bg-amber-400' },
  low_battery: { label: 'Low Battery', color: 'text-red-400', dot: 'bg-red-400' },
};

function StatRow({ label, value, unit }: { label: string; value: string | number; unit?: string }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-gray-800 last:border-0">
      <span className="text-gray-400 text-sm">{label}</span>
      <span className="text-white text-sm font-medium">{value}{unit && <span className="text-gray-500 ml-1">{unit}</span>}</span>
    </div>
  );
}

export default function PatientProfilesPage() {
  const [selected, setSelected] = useState(MOCK_PATIENTS[0].id);
  const patient = MOCK_PATIENTS.find(p => p.id === selected)!;
  const baseline = BASELINES[selected];
  const statusCfg = STATUS_CONFIG[patient.status] || STATUS_CONFIG.monitoring;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Patient Profiles</h1>
          <p className="text-gray-400 text-sm mt-1">Simulated research participants — Synthetic Demo Data</p>
        </div>
        <span className="bg-blue-900/30 border border-blue-800 text-blue-400 text-xs px-3 py-1 rounded-full">{MOCK_PATIENTS.length} participants</span>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Patient List */}
        <div className="col-span-4 space-y-2">
          {MOCK_PATIENTS.map(p => {
            const cfg = STATUS_CONFIG[p.status] || STATUS_CONFIG.monitoring;
            return (
              <button key={p.id} onClick={() => setSelected(p.id)}
                className={`w-full text-left p-4 rounded-xl border transition-colors ${
                  selected === p.id ? 'bg-blue-900/30 border-blue-700' : 'bg-gray-900 border-gray-800 hover:border-gray-700'
                }`}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-white font-bold flex-shrink-0">
                    {p.avatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm font-medium truncate">{p.name}</div>
                    <div className="text-gray-500 text-xs">{p.device}</div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <div className={`w-2 h-2 rounded-full ${cfg.dot}`}></div>
                    <span className={`text-xs ${cfg.color}`}>{cfg.label}</span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Patient Detail */}
        <div className="col-span-8 space-y-4">
          {/* Header */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center text-white text-2xl font-bold">
                  {patient.avatar}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{patient.name}</h2>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-gray-400 text-sm flex items-center gap-1"><Shield size={12}/> {patient.device}</span>
                    <span className="text-gray-400 text-sm flex items-center gap-1"><Clock size={12}/> {patient.duration}</span>
                    <div className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${statusCfg.dot} animate-pulse`}></div>
                      <span className={`text-sm ${statusCfg.color}`}>{statusCfg.label}</span>
                    </div>
                  </div>
                </div>
              </div>
              <span className="text-xs text-amber-400 bg-amber-900/20 border border-amber-800/30 px-2 py-1 rounded">Synthetic Data</span>
            </div>
          </div>

          {/* Baseline & Personalization */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2"><Heart size={16} className="text-red-400"/> Heart Rate Baseline</h3>
              <StatRow label="Mean HR" value={baseline.hr_mean} unit="BPM" />
              <StatRow label="Std Dev" value={`±${baseline.hr_std}`} unit="BPM" />
              <StatRow label="Min (learned)" value={baseline.hr_min} unit="BPM" />
              <StatRow label="Max (learned)" value={baseline.hr_max} unit="BPM" />
              <StatRow label="HRV SDNN" value={baseline.hrv_sdnn} unit="ms" />
              <StatRow label="HRV RMSSD" value={baseline.hrv_rmssd} unit="ms" />
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2"><Droplets size={16} className="text-cyan-400"/> SpO₂ Baseline</h3>
              <StatRow label="Mean SpO₂" value={baseline.spo2_mean} unit="%" />
              <StatRow label="Std Dev" value={`±${baseline.spo2_std}`} unit="%" />
              <StatRow label="Lower bound (2σ)" value={`≥${(baseline.spo2_mean - 2 * baseline.spo2_std).toFixed(1)}`} unit="%" />
              <div className="mt-4 pt-4 border-t border-gray-800">
                <h4 className="text-white font-medium mb-3 text-sm">Personalization Status</h4>
                <StatRow label="Local model" value={baseline.model_version} />
                <StatRow label="Samples used" value={baseline.samples.toLocaleString()} />
                <StatRow label="Personalization rounds" value={baseline.personalization_rounds} />
              </div>
            </div>
          </div>

          {/* Anomaly History */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2"><AlertTriangle size={16} className="text-amber-400"/> Recent Anomaly Events</h3>
            <div className="space-y-2">
              {[
                { time: '2h ago', cls: 'LOW_CONFIDENCE_EVENT', score: 0.62, sqi: 52, desc: 'Possible irregular RR pattern during low SQI window' },
                { time: '5h ago', cls: 'NORMAL', score: 0.18, sqi: 88, desc: 'Normal monitoring — no anomalies' },
                { time: '1d ago', cls: 'POSSIBLE_ANOMALY', score: 0.71, sqi: 74, desc: 'Mild HR elevation above baseline' },
              ].map((event, i) => (
                <div key={i} className="flex items-center gap-4 p-3 bg-gray-800 rounded-lg">
                  <div className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${
                    event.cls === 'NORMAL' ? 'bg-green-900/50 text-green-400' :
                    event.cls === 'LOW_CONFIDENCE_EVENT' ? 'bg-amber-900/50 text-amber-400' :
                    'bg-orange-900/50 text-orange-400'
                  }`}>{event.cls.replace(/_/g, ' ')}</div>
                  <div className="flex-1">
                    <p className="text-gray-300 text-sm">{event.desc}</p>
                    <p className="text-gray-600 text-xs mt-0.5">Score: {event.score.toFixed(2)} · SQI: {event.sqi}% · {event.time}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-gray-600 text-xs mt-3">⚠️ Research anomaly detection results — not medical diagnoses.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
