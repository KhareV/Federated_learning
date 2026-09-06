import { Eye, ArrowRight, ArrowLeft } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const FEATURES = [
  { name: 'RR Variability (SDNN)', value: 0.38, direction: 'positive' },
  { name: 'HR Deviation from Baseline', value: 0.27, direction: 'positive' },
  { name: 'ECG Waveform Deviation', value: 0.22, direction: 'positive' },
  { name: 'PPG Signal Quality', value: -0.15, direction: 'negative' },
  { name: 'SpO₂ Trend', value: -0.08, direction: 'negative' },
  { name: 'Pulse Interval Std', value: 0.12, direction: 'positive' },
  { name: 'Baseline Wander', value: 0.09, direction: 'positive' },
  { name: 'HR Mean (window)', value: -0.05, direction: 'negative' },
];

const MODELS = ['Isolation Forest', 'XGBoost', 'LSTM Autoencoder'];
const ANOMALY_EVENTS = [
  { id: 'E001', time: '14:10', score: 0.71, cls: 'LOW_CONFIDENCE_EVENT', sqi: 52 },
  { id: 'E002', time: '13:42', score: 0.82, cls: 'HIGH_CONFIDENCE_ANOMALY', sqi: 87 },
  { id: 'E003', time: '12:55', score: 0.63, cls: 'POSSIBLE_ANOMALY', sqi: 68 },
];

export default function ExplainabilityPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Eye size={24} className="text-indigo-400"/> Explainable AI
          </h1>
          <p className="text-gray-400 text-sm mt-1">Feature contribution analysis — Research anomaly detection results</p>
        </div>
        <div className="flex gap-2">
          {MODELS.map(m => (
            <button key={m} className={`px-3 py-1.5 rounded-lg text-xs ${m === 'LSTM Autoencoder' ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>{m}</button>
          ))}
        </div>
      </div>

      <div className="bg-amber-900/20 border border-amber-800/30 rounded-xl p-4 text-amber-300 text-sm">
        ⚠️ <strong>Research Result:</strong> The following feature contributions are computed by the anomaly detection model and represent statistical patterns in the synthetic data — not clinical diagnostic findings.
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Feature Importance Chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Feature Contributions (Selected Event E002)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={FEATURES} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
              <XAxis type="number" domain={[-0.2, 0.5]} tick={{ fill: '#6b7280', fontSize: 10 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} width={160} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(v: number) => [v > 0 ? `+${v.toFixed(3)}` : v.toFixed(3), 'Contribution']} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {FEATURES.map((f, i) => <Cell key={i} fill={f.value > 0 ? '#3b82f6' : '#f87171'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2 text-xs">
            <span className="flex items-center gap-1 text-blue-400">
              <span className="w-3 h-3 bg-blue-500 rounded inline-block"></span> Increases anomaly score
            </span>
            <span className="flex items-center gap-1 text-red-400">
              <span className="w-3 h-3 bg-red-500 rounded inline-block"></span> Decreases anomaly score
            </span>
          </div>
        </div>

        {/* Top factors + event list */}
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-medium mb-4">Top Contributing Factors</h3>
            <div className="space-y-3">
              {FEATURES.slice(0, 4).map((f, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`flex-shrink-0 p-1.5 rounded ${f.value > 0 ? 'bg-blue-900/40' : 'bg-red-900/40'}`}>
                    {f.value > 0 ? <ArrowRight size={14} className="text-blue-400" /> : <ArrowLeft size={14} className="text-red-400" />}
                  </div>
                  <div className="flex-1">
                    <div className="text-gray-300 text-sm">{f.name}</div>
                    <div className="h-1.5 bg-gray-800 rounded-full mt-1">
                      <div className={`h-full rounded-full ${f.value > 0 ? 'bg-blue-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.abs(f.value) / 0.4 * 100}%` }}></div>
                    </div>
                  </div>
                  <span className={`text-sm font-mono ${f.value > 0 ? 'text-blue-400' : 'text-red-400'}`}>
                    {f.value > 0 ? '+' : ''}{f.value.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-medium mb-3">Select Anomaly Event</h3>
            <div className="space-y-2">
              {ANOMALY_EVENTS.map(e => (
                <div key={e.id} className={`p-3 rounded-lg cursor-pointer border ${e.id === 'E002' ? 'bg-indigo-900/20 border-indigo-700' : 'bg-gray-800 border-gray-700 hover:border-gray-600'}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-white text-sm font-medium">{e.id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      e.cls === 'HIGH_CONFIDENCE_ANOMALY' ? 'bg-red-900/50 text-red-400' :
                      e.cls === 'LOW_CONFIDENCE_EVENT' ? 'bg-amber-900/50 text-amber-400' :
                      'bg-orange-900/50 text-orange-400'
                    }`}>{e.cls.replace(/_/g, ' ')}</span>
                  </div>
                  <div className="text-gray-500 text-xs mt-1">{e.time} · Score: {e.score} · SQI: {e.sqi}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
