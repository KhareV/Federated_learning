import { Cpu, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const VERSIONS = ['v1', 'v2', 'v3', 'v4 (current)'];

const history = Array.from({ length: 10 }, (_, i) => ({
  round: i + 1,
  accuracy: parseFloat((0.810 + i * 0.009 + (Math.random() - 0.5) * 0.002).toFixed(4)),
  f1: parseFloat((0.795 + i * 0.009 + (Math.random() - 0.5) * 0.002).toFixed(4)),
  loss: parseFloat((0.28 - i * 0.016 + (Math.random() - 0.5) * 0.003).toFixed(4)),
  precision: parseFloat((0.820 + i * 0.007).toFixed(4)),
  recall: parseFloat((0.775 + i * 0.011).toFixed(4)),
}));

const currentMetrics = [
  { name: 'Accuracy', value: 0.891 }, { name: 'F1', value: 0.878 },
  { name: 'Precision', value: 0.896 }, { name: 'Recall', value: 0.862 },
  { name: 'AUC-ROC', value: 0.923 },
];

const architecture = [
  { layer: 'Input', shape: '[batch, 20, 24]', desc: '20-step windows, 24 features' },
  { layer: 'LSTM Encoder', shape: '[batch, 20, 64]', desc: 'hidden_size=64, num_layers=2, dropout=0.2' },
  { layer: 'LSTM Decoder', shape: '[batch, 20, 64]', desc: 'Mirror of encoder' },
  { layer: 'Output', shape: '[batch, 20, 24]', desc: 'Reconstruction of input' },
  { layer: 'Anomaly Score', shape: 'scalar', desc: 'Mean reconstruction error → normalized [0,1]' },
];

export default function GlobalModelPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Cpu size={24} className="text-indigo-400"/> Global Model
        </h1>
        <p className="text-gray-400 text-sm mt-1">Federated global model — current version and history</p>
      </div>

      {/* Current model card */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-indigo-800/50 rounded-xl p-5">
          <div className="text-xs text-indigo-400 font-medium mb-2">CURRENT MODEL</div>
          <div className="text-2xl font-bold text-white mb-1">v4 — LSTM Autoencoder</div>
          <div className="text-gray-400 text-sm mb-4">Federated via QAPFL · 10 training rounds · 8 clients</div>
          <div className="grid grid-cols-2 gap-3">
            {currentMetrics.map(m => (
              <div key={m.name} className="bg-gray-800 rounded-lg p-2">
                <div className="text-gray-500 text-xs">{m.name}</div>
                <div className="text-white font-bold text-lg">{m.value.toFixed(3)}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Model Architecture</h3>
          <div className="space-y-2">
            {architecture.map((a, i) => (
              <div key={i} className="flex items-center gap-4 p-2.5 bg-gray-800 rounded-lg">
                <div className="w-28 text-blue-400 text-sm font-medium flex-shrink-0">{a.layer}</div>
                <div className="w-36 text-purple-300 font-mono text-xs flex-shrink-0">{a.shape}</div>
                <div className="text-gray-400 text-xs">{a.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Training history charts */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Global Loss</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <YAxis tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelFormatter={v => `Round ${v}`}/>
              <Line type="monotone" dataKey="loss" stroke="#f87171" strokeWidth={2} dot={{ r: 3 }}/>
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Accuracy & F1</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <YAxis domain={[0.75, 1.0]} tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelFormatter={v => `Round ${v}`}/>
              <Line type="monotone" dataKey="accuracy" stroke="#34d399" strokeWidth={2} dot={{ r: 2 }} name="Accuracy"/>
              <Line type="monotone" dataKey="f1" stroke="#60a5fa" strokeWidth={2} dot={{ r: 2 }} name="F1"/>
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Precision & Recall</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <YAxis domain={[0.75, 1.0]} tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelFormatter={v => `Round ${v}`}/>
              <Line type="monotone" dataKey="precision" stroke="#a78bfa" strokeWidth={2} dot={{ r: 2 }} name="Precision"/>
              <Line type="monotone" dataKey="recall" stroke="#fbbf24" strokeWidth={2} dot={{ r: 2 }} name="Recall"/>
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Version selector */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">Model Version History</h3>
        <div className="flex gap-3">
          {VERSIONS.map((v, i) => (
            <div key={v} className={`flex-1 p-3 rounded-lg border text-center ${v.includes('current') ? 'border-indigo-700 bg-indigo-900/20' : 'border-gray-700 bg-gray-800'}`}>
              <div className="text-white font-medium">{v}</div>
              <div className="text-gray-500 text-xs mt-1">Round {(i + 1) * 3 - 2}–{Math.min((i + 1) * 3, 10)}</div>
              <div className="text-gray-400 text-xs">F1: {(0.820 + i * 0.019).toFixed(3)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
