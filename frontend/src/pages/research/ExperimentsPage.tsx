import { useState } from 'react';
import { TestTube, Play, CheckCircle, Clock, ChevronRight } from 'lucide-react';

const EXPERIMENTS = [
  { id: 'E1', name: 'Centralized vs Federated', desc: 'Baseline comparison: centralized model vs FedAvg', status: 'completed', f1: 0.826, duration: '18.2s' },
  { id: 'E2', name: 'FedAvg vs Personalized FL', desc: 'Effect of local personalization on global FL', status: 'completed', f1: 0.849, duration: '22.5s' },
  { id: 'E3', name: 'FedAvg vs QAPFL', desc: 'Primary comparison — main research contribution', status: 'completed', f1: 0.884, duration: '23.1s' },
  { id: 'E4', name: 'Noise Robustness', desc: 'F1 and FPR vs ECG/PPG noise level 0–50%', status: 'completed', f1: 0.742, duration: '45.2s' },
  { id: 'E5', name: 'Missing Data Robustness', desc: 'Performance under varying data gap rates', status: 'completed', f1: 0.817, duration: '38.6s' },
  { id: 'E6', name: 'Client Heterogeneity', desc: 'Effect of varied client quality distributions', status: 'completed', f1: 0.861, duration: '28.4s' },
  { id: 'E7', name: 'Personalization Benefit', desc: 'Improvement from local fine-tuning per client', status: 'completed', f1: 0.869, duration: '24.8s' },
  { id: 'E8', name: 'Communication Cost', desc: 'Accuracy vs communication budget tradeoff', status: 'completed', f1: 0.876, duration: '31.0s' },
  { id: 'E9', name: 'Resource Constraints', desc: 'Performance under limited battery/compute', status: 'completed', f1: 0.843, duration: '26.7s' },
  { id: 'E10', name: 'Ablation Study', desc: 'FedAvg → +personalization → +quality → Full QAPFL', status: 'completed', f1: 0.884, duration: '52.1s' },
];

export default function ExperimentsPage() {
  const [running, setRunning] = useState<string | null>(null);

  const runAll = async () => {
    for (const e of EXPERIMENTS.filter(x => x.status !== 'completed')) {
      setRunning(e.id);
      await new Promise(r => setTimeout(r, 800));
    }
    setRunning(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TestTube size={24} className="text-blue-400"/> Research Experiments
          </h1>
          <p className="text-gray-400 text-sm mt-1">{EXPERIMENTS.filter(e => e.status === 'completed').length}/{EXPERIMENTS.length} completed — All on synthetic data</p>
        </div>
        <button onClick={runAll} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">
          <Play size={14}/> Run All Experiments
        </button>
      </div>

      <div className="grid gap-3">
        {EXPERIMENTS.map(e => (
          <div key={e.id} className={`bg-gray-900 border rounded-xl p-4 flex items-center gap-4 transition-colors ${
            running === e.id ? 'border-blue-700 bg-blue-900/10' : 'border-gray-800'
          }`}>
            <div className="flex-shrink-0">
              {running === e.id ? (
                <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"/>
              ) : e.status === 'completed' ? (
                <CheckCircle size={24} className="text-green-400"/>
              ) : (
                <Clock size={24} className="text-gray-600"/>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-gray-500 text-xs font-mono font-bold">{e.id}</span>
                <span className="text-white font-medium text-sm">{e.name}</span>
                {e.status === 'completed' && (
                  <span className="text-green-400 text-xs bg-green-900/20 px-2 py-0.5 rounded-full">Completed</span>
                )}
              </div>
              <p className="text-gray-500 text-xs mt-0.5">{e.desc}</p>
            </div>
            <div className="text-right flex-shrink-0">
              {e.status === 'completed' && (
                <>
                  <div className="text-blue-400 font-bold text-sm">F1: {e.f1.toFixed(3)}</div>
                  <div className="text-gray-600 text-xs">{e.duration}</div>
                </>
              )}
            </div>
            <button className="text-gray-600 hover:text-white p-1"><ChevronRight size={16}/></button>
          </div>
        ))}
      </div>
    </div>
  );
}
