import { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const TIME_RANGES = ['1h', '6h', '24h', '7d', '30d'] as const;
type TimeRange = typeof TIME_RANGES[number];

function genSeries(n: number, base: number, std: number, trend = 0, seed = 1) {
  const data = [];
  let val = base;
  for (let i = 0; i < n; i++) {
    val += trend + (Math.sin(i * 0.4 + seed) * std * 0.5) + ((Math.random() - 0.5) * std * 0.3);
    val = Math.max(base - 3 * std, Math.min(base + 3 * std, val));
    data.push({ t: i, value: Math.round(val * 10) / 10 });
  }
  return data;
}

function gen2Series(n: number, base1: number, base2: number, std: number) {
  const data = [];
  for (let i = 0; i < n; i++) {
    data.push({
      t: i,
      a: Math.round((base1 + Math.sin(i * 0.3) * std + (Math.random() - 0.5) * std * 0.3) * 10) / 10,
      b: Math.round((base2 + Math.sin(i * 0.3 + 1) * std + (Math.random() - 0.5) * std * 0.3) * 10) / 10,
    });
  }
  return data;
}

const POINTS: Record<TimeRange, number> = { '1h': 60, '6h': 72, '24h': 96, '7d': 168, '30d': 120 };

function TrendBadge({ trend }: { trend: 'up' | 'down' | 'stable' }) {
  if (trend === 'up') return <span className="flex items-center gap-1 text-red-400 text-xs"><TrendingUp size={12}/>Rising</span>;
  if (trend === 'down') return <span className="flex items-center gap-1 text-green-400 text-xs"><TrendingDown size={12}/>Falling</span>;
  return <span className="flex items-center gap-1 text-gray-400 text-xs"><Minus size={12}/>Stable</span>;
}

function InsightCard({ icon, title, text, type }: { icon: React.ReactNode; title: string; text: string; type: 'info' | 'warning' | 'good' }) {
  const colors = {
    info: 'border-blue-800/40 bg-blue-900/10 text-blue-300',
    warning: 'border-amber-800/40 bg-amber-900/10 text-amber-300',
    good: 'border-green-800/40 bg-green-900/10 text-green-300',
  };
  return (
    <div className={`border rounded-xl p-4 ${colors[type]}`}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{icon}</div>
        <div>
          <div className="font-medium text-sm mb-1">{title}</div>
          <div className="text-xs opacity-80">{text}</div>
        </div>
      </div>
    </div>
  );
}

export default function HealthTrendsPage() {
  const [range, setRange] = useState<TimeRange>('24h');
  const n = POINTS[range];

  const hrData = genSeries(n, 72, 6, 0.02);
  const spo2Data = genSeries(n, 97.8, 0.8, -0.005, 2);
  const hrvData = genSeries(n, 42, 8, 0, 3);
  const anomalyData = genSeries(n, 0.12, 0.08, 0.001, 4).map(d => ({ ...d, value: Math.max(0, Math.min(1, d.value)) }));
  const sqiData = genSeries(n, 76, 12, 0, 5).map(d => ({ ...d, value: Math.max(10, Math.min(100, d.value)) }));
  const confData = genSeries(n, 0.82, 0.1, 0, 6).map(d => ({ ...d, value: Math.max(0, Math.min(1, d.value)) }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Health Trends</h1>
          <p className="text-gray-400 text-sm mt-1">Longitudinal analysis — Synthetic Demo Data</p>
        </div>
        <div className="flex gap-2 bg-gray-900 border border-gray-800 rounded-lg p-1">
          {TIME_RANGES.map(r => (
            <button key={r} onClick={() => setRange(r)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                range === r ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}>{r}</button>
          ))}
        </div>
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { title: 'Heart Rate', data: hrData, color: '#f87171', unit: 'BPM', trend: 'stable' as const, ref: 72 },
          { title: 'SpO₂', data: spo2Data, color: '#22d3ee', unit: '%', trend: 'down' as const, ref: 97.5 },
          { title: 'HRV (SDNN)', data: hrvData, color: '#a78bfa', unit: 'ms', trend: 'stable' as const, ref: 42 },
          { title: 'Anomaly Score', data: anomalyData, color: '#fbbf24', unit: '', trend: 'up' as const, ref: 0.5 },
          { title: 'Signal Quality (SQI)', data: sqiData, color: '#34d399', unit: '%', trend: 'stable' as const, ref: 60 },
          { title: 'Model Confidence', data: confData, color: '#60a5fa', unit: '', trend: 'stable' as const, ref: 0.7 },
        ].map(({ title, data, color, unit, trend, ref }) => (
          <div key={title} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-medium">{title}</h3>
              <TrendBadge trend={trend} />
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="t" tick={false} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} width={40} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ display: 'none' }}
                  itemStyle={{ color }}
                  formatter={(v: number) => [`${v.toFixed(1)} ${unit}`, title]}
                />
                <ReferenceLine y={ref} stroke={color} strokeDasharray="4 4" strokeOpacity={0.5} />
                <Area type="monotone" dataKey="value" stroke={color} fill={color + '20'} strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      {/* Trend Insights */}
      <div>
        <h2 className="text-white font-semibold mb-4">Data-Driven Trend Insights</h2>
        <div className="grid grid-cols-2 gap-3">
          <InsightCard type="warning" icon={<TrendingUp size={16}/>}
            title="Anomaly Frequency Increasing"
            text="Anomaly score shows a mild upward trend over the selected window. This may correlate with the observed signal quality variability during the last monitoring session." />
          <InsightCard type="good" icon={<TrendingDown size={16}/>}
            title="HR Within Learned Baseline"
            text="Heart rate has remained within the user's personalized baseline range (mean ±2σ) for 94% of the selected period. No significant baseline shift detected." />
          <InsightCard type="info" icon={<AlertCircle size={16}/>}
            title="SpO₂ Mild Downward Variation"
            text="SpO₂ shows small downward variation (< 1%). This is within normal physiological noise range for this synthetic client profile. No clinical significance claimed." />
          <InsightCard type="good" icon={<TrendingUp size={16}/>}
            title="Personalization Effect"
            text="Local model confidence improved by ~4% since last FL personalization round. Fewer low-confidence events compared with the global model baseline." />
        </div>
        <p className="text-gray-600 text-xs mt-3">⚠️ Insights are generated from synthetic research data. No medical conclusions should be drawn.</p>
      </div>
    </div>
  );
}
