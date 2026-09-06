import { useState } from 'react';
import { Server, Database, Battery, Wifi, Filter } from 'lucide-react';

const CLIENTS = [
  { id: 'client_01', name: 'Alice', desc: 'Clean data, stable baseline', ecg_sqi: 88, ppg_sqi: 85, accuracy: 0.921, f1: 0.914, loss: 0.089, uncertainty: 0.08, battery: 0.92, dataset: 5000, usable: 4950, weight: 0.0 },
  { id: 'client_02', name: 'Bob', desc: 'Moderate noise, large dataset', ecg_sqi: 72, ppg_sqi: 70, accuracy: 0.887, f1: 0.876, loss: 0.143, uncertainty: 0.14, battery: 0.78, dataset: 7000, usable: 6580, weight: 0.0 },
  { id: 'client_03', name: 'Carol', desc: 'High motion artifacts, poor ECG', ecg_sqi: 45, ppg_sqi: 42, accuracy: 0.831, f1: 0.804, loss: 0.221, uncertainty: 0.28, battery: 0.55, dataset: 4000, usable: 3100, weight: 0.0 },
  { id: 'client_04', name: 'David', desc: 'Missing data segments', ecg_sqi: 74, ppg_sqi: 79, accuracy: 0.869, f1: 0.856, loss: 0.163, uncertainty: 0.17, battery: 0.88, dataset: 3500, usable: 2730, weight: 0.0 },
  { id: 'client_05', name: 'Eve', desc: 'Resource limited, small dataset', ecg_sqi: 71, ppg_sqi: 73, accuracy: 0.845, f1: 0.831, loss: 0.187, uncertainty: 0.19, battery: 0.23, dataset: 2000, usable: 1890, weight: 0.0 },
  { id: 'client_06', name: 'Frank', desc: 'Elevated HR baseline', ecg_sqi: 78, ppg_sqi: 76, accuracy: 0.875, f1: 0.862, loss: 0.155, uncertainty: 0.16, battery: 0.67, dataset: 6000, usable: 5740, weight: 0.0 },
  { id: 'client_07', name: 'Grace', desc: 'High SpO2 variability', ecg_sqi: 80, ppg_sqi: 65, accuracy: 0.858, f1: 0.844, loss: 0.173, uncertainty: 0.18, battery: 0.81, dataset: 5500, usable: 5150, weight: 0.0 },
  { id: 'client_08', name: 'Henry', desc: 'Mixed quality, anomaly-prone', ecg_sqi: 55, ppg_sqi: 58, accuracy: 0.820, f1: 0.793, loss: 0.248, uncertainty: 0.31, battery: 0.44, dataset: 4500, usable: 3600, weight: 0.0 },
];

function SQIBar({ value, label }: { value: number; label: string }) {
  const color = value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-blue-500' : value >= 40 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-white">{value}%</span>
      </div>
      <div className="h-1.5 bg-gray-700 rounded-full">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }}></div>
      </div>
    </div>
  );
}

export default function FLClientsPage() {
  const [sortBy, setSortBy] = useState<'ecg_sqi' | 'f1' | 'battery' | 'dataset'>('ecg_sqi');
  const sorted = [...CLIENTS].sort((a, b) => (b as any)[sortBy] - (a as any)[sortBy]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">FL Clients</h1>
          <p className="text-gray-400 text-sm mt-1">8 simulated federated learning clients with distinct profiles</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-400"/>
          <span className="text-gray-400 text-sm">Sort by:</span>
          {(['ecg_sqi', 'f1', 'battery', 'dataset'] as const).map(s => (
            <button key={s} onClick={() => setSortBy(s)}
              className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${sortBy === s ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
              {s === 'ecg_sqi' ? 'ECG SQI' : s === 'f1' ? 'Local F1' : s === 'battery' ? 'Battery' : 'Dataset'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {sorted.map(c => {
          const avgSqi = (c.ecg_sqi + c.ppg_sqi) / 2;
          const sqiColor = avgSqi >= 80 ? 'border-green-800' : avgSqi >= 60 ? 'border-blue-800' : avgSqi >= 40 ? 'border-amber-800' : 'border-red-800';
          return (
            <div key={c.id} className={`bg-gray-900 border rounded-xl p-4 ${sqiColor}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-white font-semibold">{c.name}</div>
                  <div className="text-gray-500 text-xs mt-0.5">{c.id}</div>
                </div>
                <div className="flex items-center gap-1">
                  <Battery size={12} className={c.battery > 0.3 ? 'text-green-400' : 'text-red-400'} />
                  <span className={`text-xs ${c.battery > 0.3 ? 'text-green-400' : 'text-red-400'}`}>{Math.round(c.battery * 100)}%</span>
                </div>
              </div>

              <p className="text-gray-500 text-xs mb-3">{c.desc}</p>

              <div className="space-y-2 mb-3">
                <SQIBar value={c.ecg_sqi} label="ECG SQI" />
                <SQIBar value={c.ppg_sqi} label="PPG SQI" />
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Local F1</div>
                  <div className="text-white font-medium">{c.f1.toFixed(3)}</div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Accuracy</div>
                  <div className="text-white font-medium">{c.accuracy.toFixed(3)}</div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Uncertainty</div>
                  <div className="text-white font-medium">{c.uncertainty.toFixed(2)}</div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Dataset</div>
                  <div className="text-white font-medium">{c.usable.toLocaleString()}/{c.dataset.toLocaleString()}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
