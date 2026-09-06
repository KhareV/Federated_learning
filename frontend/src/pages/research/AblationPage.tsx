import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ArrowRight, CheckCircle } from 'lucide-react';

const CONFIGS = [
  {
    id: 'A',
    name: 'FedAvg Baseline',
    desc: 'Standard Federated Averaging, equal weights, no personalization, no quality weighting',
    accuracy: 0.841, f1: 0.826, fpr: 0.142, comm: 24.3, time: 18.2,
    components: ['FedAvg Aggregation'],
  },
  {
    id: 'B',
    name: 'FedAvg + Personalization',
    desc: 'FedAvg global aggregation + local fine-tuning on each client',
    accuracy: 0.862, f1: 0.849, fpr: 0.121, comm: 24.3, time: 21.5,
    components: ['FedAvg Aggregation', 'Personalization'],
  },
  {
    id: 'C',
    name: 'FedAvg + Quality Weighting',
    desc: 'FedAvg with signal quality-aware aggregation weights, no personalization',
    accuracy: 0.871, f1: 0.859, fpr: 0.108, comm: 24.3, time: 18.8,
    components: ['Quality-Aware Aggregation'],
  },
  {
    id: 'D',
    name: 'Quality Weighting + Personalization',
    desc: 'Quality-weighted aggregation AND local personalization fine-tuning',
    accuracy: 0.886, f1: 0.875, fpr: 0.094, comm: 24.3, time: 22.1,
    components: ['Quality-Aware Aggregation', 'Personalization'],
  },
  {
    id: 'E',
    name: 'Full QAPFL',
    desc: 'All components: Quality-aware aggregation + personalization + uncertainty weighting',
    accuracy: 0.896, f1: 0.884, fpr: 0.082, comm: 24.3, time: 22.8,
    components: ['Quality-Aware Aggregation', 'Uncertainty Weighting', 'Personalization'],
  },
];

const COLORS = ['#6b7280','#60a5fa','#34d399','#fbbf24','#3b82f6'];

export default function AblationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Ablation Study</h1>
        <p className="text-gray-400 text-sm mt-1">Contribution of each QAPFL component — Experiment 10</p>
      </div>

      <div className="bg-blue-900/20 border border-blue-800/30 rounded-xl p-4 text-blue-200 text-sm">
        <strong>Purpose:</strong> Ablation studies isolate the contribution of each model component by systematically adding/removing them. Configuration A is the baseline (FedAvg); each step adds one QAPFL component to show its incremental benefit.
      </div>

      {/* Config cards */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        {CONFIGS.map((c, i) => (
          <div key={c.id} className="flex-shrink-0 w-52 bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-sm font-bold`}
                style={{ backgroundColor: COLORS[i] }}>{c.id}</span>
              <span className="text-white text-sm font-medium truncate">{c.name}</span>
            </div>
            <p className="text-gray-500 text-xs mb-3">{c.desc}</p>
            <div className="space-y-1">
              {c.components.map(comp => (
                <div key={comp} className="flex items-center gap-1 text-xs text-green-400">
                  <CheckCircle size={10}/> {comp}
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-gray-800">
              <div className="text-gray-500 text-xs">F1 Score</div>
              <div className="text-white font-bold text-lg">{c.f1.toFixed(3)}</div>
            </div>
          </div>
        ))}
      </div>

      {/* F1 comparison chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">F1 Score by Configuration</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={CONFIGS}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
            <XAxis dataKey="id" tick={{ fill: '#9ca3af', fontSize: 13 }}/>
            <YAxis domain={[0.75, 1.0]} tick={{ fill: '#6b7280', fontSize: 11 }}/>
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
              formatter={(v: number) => [v.toFixed(3), 'F1 Score']}
              labelFormatter={(l) => CONFIGS.find(c => c.id === l)?.name || l}/>
            <Bar dataKey="f1" radius={[6,6,0,0]}>
              {CONFIGS.map((_, i) => <Cell key={i} fill={COLORS[i]}/>)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex flex-wrap gap-3 mt-2 text-xs">
          {CONFIGS.map((c, i) => (
            <span key={c.id} className="flex items-center gap-1" style={{ color: COLORS[i] }}>
              <span className="w-3 h-3 rounded inline-block" style={{ backgroundColor: COLORS[i] }}></span>
              {c.id}: {c.name}
            </span>
          ))}
        </div>
      </div>

      {/* Full results table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-7 px-4 py-3 border-b border-gray-800 text-xs text-gray-500 uppercase font-medium">
          <div className="col-span-2">Configuration</div>
          <div>Accuracy</div><div>F1</div><div>FPR</div><div>Comm (MB)</div><div>Time (s)</div>
        </div>
        {CONFIGS.map((c, i) => (
          <div key={c.id} className="grid grid-cols-7 px-4 py-3 border-b border-gray-800/50 text-sm hover:bg-gray-800/30">
            <div className="col-span-2 flex items-center gap-2">
              <span className="w-5 h-5 rounded flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                style={{ backgroundColor: COLORS[i] }}>{c.id}</span>
              <span className="text-gray-300 truncate">{c.name}</span>
            </div>
            <div className="text-gray-300">{c.accuracy.toFixed(3)}</div>
            <div className={c.id === 'E' ? 'text-blue-400 font-bold' : 'text-gray-300'}>{c.f1.toFixed(3)}</div>
            <div className="text-gray-300">{c.fpr.toFixed(3)}</div>
            <div className="text-gray-300">{c.comm.toFixed(1)}</div>
            <div className="text-gray-300">{c.time.toFixed(1)}</div>
          </div>
        ))}
      </div>

      <div className="bg-green-900/10 border border-green-800/30 rounded-xl p-4 text-green-300 text-sm">
        <strong>Conclusion:</strong> Each QAPFL component contributes incrementally. Full QAPFL (Config E) achieves the highest F1 ({CONFIGS[4].f1.toFixed(3)}) with the lowest FPR ({CONFIGS[4].fpr.toFixed(3)}). Personalization and quality-aware weighting together account for {((CONFIGS[4].f1 - CONFIGS[0].f1) / CONFIGS[0].f1 * 100).toFixed(1)}% improvement over FedAvg baseline. All results from synthetic data.
      </div>
    </div>
  );
}
