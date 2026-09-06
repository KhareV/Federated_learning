import { User, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, LineChart, Line } from 'recharts';

const CLIENTS = [
  { id: 'client_01', name: 'Alice', hr_mean: 68, hr_std: 5, spo2_mean: 98.2 },
  { id: 'client_02', name: 'Bob', hr_mean: 75, hr_std: 8, spo2_mean: 97.5 },
  { id: 'client_06', name: 'Frank', hr_mean: 92, hr_std: 10, spo2_mean: 97.2 },
];

function BellCurveChart({ mean, std, current }: { mean: number; std: number; current: number }) {
  const points = Array.from({ length: 80 }, (_, i) => {
    const x = mean - 3.5 * std + (i / 79) * 7 * std;
    const y = Math.exp(-0.5 * Math.pow((x - mean) / std, 2)) / (std * Math.sqrt(2 * Math.PI));
    return { x: Math.round(x * 10) / 10, y: Math.round(y * 10000) / 10000 };
  });
  const devZ = Math.abs((current - mean) / std);
  const devLabel = devZ < 1 ? 'WITHIN BASELINE' : devZ < 2 ? 'MILD DEVIATION' : devZ < 3 ? 'MODERATE DEVIATION' : 'SIGNIFICANT DEVIATION';
  const devColor = devZ < 1 ? 'text-green-400' : devZ < 2 ? 'text-blue-400' : devZ < 3 ? 'text-amber-400' : 'text-red-400';
  return (
    <div>
      <ResponsiveContainer width="100%" height={140}>
        <AreaChart data={points}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="x" tick={{ fill: '#6b7280', fontSize: 10 }} />
          <YAxis hide />
          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            formatter={(v: number) => [v.toFixed(4), 'Density']} />
          <ReferenceLine x={mean - 2 * std} stroke="#374151" strokeDasharray="4 4" />
          <ReferenceLine x={mean + 2 * std} stroke="#374151" strokeDasharray="4 4" />
          <ReferenceLine x={current} stroke="#fbbf24" strokeWidth={2} label={{ value: `Current: ${current}`, fill: '#fbbf24', fontSize: 10 }} />
          <Area type="monotone" dataKey="y" stroke="#3b82f6" fill="#3b82f620" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex items-center justify-between mt-2 text-sm">
        <span className="text-gray-400">Baseline: {mean - 2 * std}–{mean + 2 * std} BPM</span>
        <span className={`font-medium ${devColor}`}>{devLabel} ({devZ.toFixed(1)}σ)</span>
      </div>
    </div>
  );
}

const baselineHistory = Array.from({ length: 30 }, (_, i) => ({
  day: `D${i + 1}`,
  hr_mean: 68 + (i * 0.1) + (Math.random() - 0.5) * 2,
  hr_std: 5 + (Math.random() - 0.5) * 0.5,
}));

export default function PersonalizedBaselinePage() {
  const selected = CLIENTS[0];
  const currentHR = 73;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <User size={24} className="text-purple-400"/> Personalized Baseline
          </h1>
          <p className="text-gray-400 text-sm mt-1">Learned physiological baselines — Synthetic Demo Data</p>
        </div>
      </div>

      {/* Client selector */}
      <div className="flex gap-3">
        {CLIENTS.map(c => (
          <div key={c.id} className="bg-blue-900/30 border border-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
            {c.name}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* HR Baseline Distribution */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">HR Baseline Distribution — {selected.name}</h3>
          <BellCurveChart mean={selected.hr_mean} std={selected.hr_std} current={currentHR} />
          <div className="mt-4 grid grid-cols-3 gap-2">
            {[
              { label: 'Baseline Mean', value: `${selected.hr_mean} BPM` },
              { label: 'Current HR', value: `${currentHR} BPM` },
              { label: 'Deviation', value: `${((currentHR - selected.hr_mean) / selected.hr_std).toFixed(1)}σ` },
            ].map(s => (
              <div key={s.label} className="bg-gray-800 rounded-lg p-2 text-center">
                <div className="text-gray-500 text-xs">{s.label}</div>
                <div className="text-white text-sm font-medium mt-0.5">{s.value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Personalization status */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Personalization Status</h3>
          <div className="space-y-3">
            {[
              { label: 'Local model version', value: 'v3 (personalized)' },
              { label: 'Training samples', value: '5,000' },
              { label: 'Personalization rounds', value: '7' },
              { label: 'Last updated', value: '2h ago' },
              { label: 'HR baseline samples', value: '4,821 usable' },
              { label: 'SpO₂ mean (learned)', value: `${selected.spo2_mean}%` },
              { label: 'Baseline status', value: 'Stable (no shift)' },
            ].map(r => (
              <div key={r.label} className="flex justify-between items-center py-1.5 border-b border-gray-800 last:border-0">
                <span className="text-gray-400 text-sm">{r.label}</span>
                <span className="text-white text-sm">{r.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Baseline drift history */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">Baseline Evolution (Last 30 days)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={baselineHistory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 10 }} interval={4} />
            <YAxis domain={[60, 80]} tick={{ fill: '#6b7280', fontSize: 11 }} />
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
              formatter={(v: number) => [`${v.toFixed(1)} BPM`]} />
            <Line type="monotone" dataKey="hr_mean" stroke="#a78bfa" strokeWidth={2} dot={false} name="HR Baseline Mean" />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-gray-500 text-xs mt-2">Stable baseline over 30 days — no significant drift detected. Slight upward trend (0.1 BPM/day) within normal physiological variation for synthetic data.</p>
      </div>
    </div>
  );
}
