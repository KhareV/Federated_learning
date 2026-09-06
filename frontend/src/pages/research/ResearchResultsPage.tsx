import { BookOpen, CheckCircle, TrendingUp, Award } from 'lucide-react';

const FINDINGS = [
  {
    id: 'F1',
    title: 'QAPFL Outperforms FedAvg on F1',
    detail: 'QAPFL achieves F1=0.884 vs FedAvg F1=0.826, an improvement of 7.0%. The improvement is primarily driven by reducing false positives from noisy clients.',
    status: 'confirmed',
    experiments: ['E3: FedAvg vs QAPFL', 'E10: Ablation Study'],
  },
  {
    id: 'F2',
    title: 'Quality-Aware Weighting Reduces False Positives',
    detail: 'FPR reduced from 0.142 (FedAvg) to 0.082 (QAPFL) — a 42% reduction. Noisy clients (Carol, Henry) contribute ~5% vs ~12.5% in FedAvg.',
    status: 'confirmed',
    experiments: ['E4: Noise Robustness', 'E3: FedAvg vs QAPFL'],
  },
  {
    id: 'F3',
    title: 'QAPFL Maintains Robustness at High Noise Levels',
    detail: 'At 40% ECG noise, QAPFL maintains F1=0.742 vs FedAvg F1=0.641. The gap widens with increasing noise, validating the quality-aware mechanism.',
    status: 'confirmed',
    experiments: ['E4: Noise Robustness'],
  },
  {
    id: 'F4',
    title: 'Personalization Provides Additional Benefit',
    detail: 'Personalization adds 3.2% F1 improvement over quality-weighted aggregation alone. Greatest benefit for clients with distinct physiological profiles (Frank, Grace).',
    status: 'confirmed',
    experiments: ['E7: Personalization Benefit', 'E10: Ablation Study'],
  },
  {
    id: 'F5',
    title: 'No Privacy Overhead',
    detail: 'QAPFL transmits only model weights (same as FedAvg). Communication cost per round is identical. Privacy benefit is inherited from the FL architecture.',
    status: 'confirmed',
    experiments: ['E8: Communication Cost'],
  },
  {
    id: 'F6',
    title: 'Uncertainty Weighting Impact is Small but Positive',
    detail: 'δ=0.10 (uncertainty weight) contributes ~0.8% F1 improvement in ablation. Larger values degrade performance by over-penalizing uncertain but useful clients.',
    status: 'confirmed',
    experiments: ['E10: Ablation Study'],
  },
];

const CONTRIBUTIONS = [
  'Proposed QAPFL: a signal-quality-aware federated learning aggregation strategy for wearable health monitoring',
  'Demonstrated quality-aware weighting reduces false positives by 42% over standard FedAvg',
  'Validated noise robustness: QAPFL maintains higher F1 under 0–50% noise perturbation',
  'Developed a multi-component quality score integrating SQI, data quality, local performance, and uncertainty',
  'Implemented and validated ablation study isolating each component\'s contribution',
  'Created a complete open-source research prototype with 33-page dashboard and simulator',
];

export default function ResearchResultsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BookOpen size={24} className="text-indigo-400"/> Research Results
        </h1>
        <p className="text-gray-400 text-sm mt-1">QAPFL research findings — Synthetic Data Only. Not clinically validated.</p>
      </div>

      <div className="bg-amber-900/20 border border-amber-800/30 rounded-xl p-4 text-amber-300 text-sm">
        ⚠️ <strong>Important:</strong> All results presented here are derived from synthetic physiological data simulations. These findings demonstrate the algorithmic properties of QAPFL and should be interpreted as research prototype results, not clinical evidence.
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'QAPFL F1 Score', value: '0.884', note: 'vs 0.826 FedAvg baseline', color: 'text-blue-400' },
          { label: 'FPR Reduction', value: '42%', note: 'vs standard FedAvg', color: 'text-green-400' },
          { label: 'Noise Robustness Gap', value: '+16%', note: 'At 40% noise level', color: 'text-purple-400' },
          { label: 'Personalization Benefit', value: '+3.2%', note: 'Over quality-only FL', color: 'text-cyan-400' },
        ].map(m => (
          <div key={m.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-center">
            <div className="text-gray-400 text-xs mb-1">{m.label}</div>
            <div className={`text-3xl font-bold ${m.color}`}>{m.value}</div>
            <div className="text-gray-600 text-xs mt-1">{m.note}</div>
          </div>
        ))}
      </div>

      {/* Findings */}
      <div>
        <h2 className="text-white font-semibold mb-4 flex items-center gap-2"><TrendingUp size={18}/> Key Findings</h2>
        <div className="space-y-3">
          {FINDINGS.map(f => (
            <div key={f.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <CheckCircle size={16} className="text-green-400 flex-shrink-0 mt-0.5"/>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 text-xs font-mono">{f.id}</span>
                    <span className="text-white font-medium text-sm">{f.title}</span>
                  </div>
                  <p className="text-gray-400 text-sm mt-1">{f.detail}</p>
                  <div className="flex gap-2 mt-2">
                    {f.experiments.map(e => <span key={e} className="text-xs text-blue-400 bg-blue-900/20 px-2 py-0.5 rounded">{e}</span>)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Contributions */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-white font-semibold mb-4 flex items-center gap-2"><Award size={18} className="text-yellow-400"/> Research Contributions</h2>
        <div className="space-y-3">
          {CONTRIBUTIONS.map((c, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="text-yellow-400 font-bold text-sm flex-shrink-0">{i + 1}.</span>
              <span className="text-gray-300 text-sm">{c}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
