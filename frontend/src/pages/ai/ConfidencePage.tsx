import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine, LineChart, Line, AreaChart, Area } from 'recharts';

const scatterData = [
  // Q1: Normal + high quality (blue)
  ...Array.from({ length: 20 }, () => ({ x: Math.random() * 0.45, y: 65 + Math.random() * 35, q: 'normal_hq' })),
  // Q2: Anomaly + high quality (red)
  ...Array.from({ length: 8 }, () => ({ x: 0.55 + Math.random() * 0.45, y: 65 + Math.random() * 35, q: 'anomaly_hq' })),
  // Q3: Normal + poor quality (gray)
  ...Array.from({ length: 12 }, () => ({ x: Math.random() * 0.45, y: 10 + Math.random() * 40, q: 'normal_pq' })),
  // Q4: Anomaly + poor quality (amber)
  ...Array.from({ length: 10 }, () => ({ x: 0.55 + Math.random() * 0.45, y: 10 + Math.random() * 40, q: 'anomaly_pq' })),
];

const colorMap: Record<string, string> = {
  normal_hq: '#3b82f6',
  anomaly_hq: '#ef4444',
  normal_pq: '#6b7280',
  anomaly_pq: '#fbbf24',
};

const confidenceSeries = Array.from({ length: 60 }, (_, i) => ({
  t: i,
  raw: 0.78 + Math.sin(i * 0.4) * 0.12 + (Math.random() - 0.5) * 0.06,
  adjusted: 0.65 + Math.sin(i * 0.4) * 0.10 + (Math.random() - 0.5) * 0.06,
}));

export default function ConfidencePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Prediction Confidence & Uncertainty</h1>
        <p className="text-gray-400 text-sm mt-1">Why signal quality matters for anomaly detection — Synthetic Demo Data</p>
      </div>

      {/* Key insight */}
      <div className="bg-blue-900/20 border border-blue-800/30 rounded-xl p-4 text-blue-200 text-sm">
        <strong>Research Insight:</strong> QAPFL addresses a fundamental problem — noisy sensor data can produce high anomaly scores that look confident to the model. By adjusting confidence using signal quality, the system avoids false high-confidence alerts from poor-quality readings. This is the motivation for the LOW_CONFIDENCE_EVENT classification.
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Scatter quadrant */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Anomaly Score vs Signal Quality</h3>
          <ResponsiveContainer width="100%" height={280}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 30, left: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="x" type="number" name="Anomaly Score" domain={[0, 1]} tick={{ fill: '#6b7280', fontSize: 10 }}
                label={{ value: 'Anomaly Score →', position: 'insideBottom', offset: -10, fill: '#6b7280', fontSize: 11 }} />
              <YAxis dataKey="y" type="number" name="Signal Quality" domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }}
                label={{ value: 'Signal Quality (SQI) →', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 11 }} width={55} />
              <ReferenceLine x={0.5} stroke="#374151" strokeDasharray="6 3" />
              <ReferenceLine y={60} stroke="#374151" strokeDasharray="6 3" />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(v: number, name: string) => [v.toFixed(2), name]} />
              <Scatter data={scatterData} name="Sample">
                {scatterData.map((entry, i) => <Cell key={i} fill={colorMap[entry.q]} opacity={0.8} />)}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          {/* Quadrant labels */}
          <div className="grid grid-cols-2 gap-2 text-xs mt-2">
            <div className="bg-gray-800 rounded p-2 text-blue-400">↖ Q1: Normal + High Quality ✓ Reliable</div>
            <div className="bg-gray-800 rounded p-2 text-red-400">↗ Q2: Anomaly + High Quality ⚠ Reliable alert</div>
            <div className="bg-gray-800 rounded p-2 text-gray-400">↙ Q3: Normal + Poor Quality ? Uncertain</div>
            <div className="bg-gray-800 rounded p-2 text-amber-400">↘ Q4: Anomaly + Poor Quality ❓ LOW_CONFIDENCE</div>
          </div>
        </div>

        {/* Confidence comparison */}
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-medium mb-4">Confidence: Raw vs SQI-Adjusted</h3>
            <ResponsiveContainer width="100%" height={170}>
              <AreaChart data={confidenceSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="t" tick={false} />
                <YAxis domain={[0, 1]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  formatter={(v: number, n: string) => [v.toFixed(3), n === 'raw' ? 'Raw Confidence' : 'SQI-Adjusted']}
                  labelStyle={{ display: 'none' }} />
                <Area type="monotone" dataKey="raw" stroke="#f87171" fill="#f8717115" strokeWidth={2} dot={false} name="raw" />
                <Area type="monotone" dataKey="adjusted" stroke="#34d399" fill="#34d39915" strokeWidth={2} dot={false} name="adjusted" />
              </AreaChart>
            </ResponsiveContainer>
            <div className="flex gap-4 mt-2 text-xs">
              <span className="text-red-400">— Raw confidence (unadjusted)</span>
              <span className="text-emerald-400">— SQI-adjusted confidence</span>
            </div>
            <p className="text-gray-500 text-xs mt-2">Adjusted = raw × (SQI / 100) × correction_factor. Prevents overconfident false positives from poor-quality signals.</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-medium mb-3">Current Statistics</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Current Anomaly Score', value: '0.18', color: 'text-green-400' },
                { label: 'Raw Confidence', value: '0.82', color: 'text-white' },
                { label: 'SQI-Adjusted Confidence', value: '0.65', color: 'text-cyan-400' },
                { label: 'Signal Quality (SQI)', value: '79%', color: 'text-blue-400' },
                { label: 'Classification', value: 'NORMAL', color: 'text-green-400' },
                { label: 'MC Dropout Uncertainty', value: '0.12', color: 'text-white' },
              ].map(s => (
                <div key={s.label} className="bg-gray-800 rounded-lg p-2">
                  <div className="text-gray-500 text-xs">{s.label}</div>
                  <div className={`font-medium text-sm mt-0.5 ${s.color}`}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
