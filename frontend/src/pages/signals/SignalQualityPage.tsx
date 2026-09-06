import { Signal, AlertTriangle, Info } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, Cell, ZAxis } from 'recharts';

function CircularGauge({ value, label, color }: { value: number; label: string; color: string }) {
  const r = 52; const cx = 60; const cy = 60;
  const pct = value / 100;
  const startA = Math.PI * 0.75;
  const endA = Math.PI * 2.25;
  const valA = startA + pct * (endA - startA);
  const toXY = (a: number) => ({ x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) });
  const s = toXY(startA); const e = toXY(endA); const v = toXY(valA);
  const large = (a: number) => valA - a > Math.PI ? 1 : 0;
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 120 90" className="w-32 h-24">
        <path d={`M ${s.x} ${s.y} A ${r} ${r} 0 1 1 ${e.x} ${e.y}`} fill="none" stroke="#1f2937" strokeWidth="10" strokeLinecap="round"/>
        <path d={`M ${s.x} ${s.y} A ${r} ${r} 0 ${large(startA)} 1 ${v.x} ${v.y}`} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"/>
        <text x={cx} y={cx - 8} textAnchor="middle" fill="white" fontSize="16" fontWeight="bold">{value}</text>
        <text x={cx} y={cx + 6} textAnchor="middle" fill="#6b7280" fontSize="9">%</text>
      </svg>
      <span className="text-gray-300 text-sm mt-1">{label}</span>
      <span className={`text-xs font-medium mt-0.5 ${value >= 80 ? 'text-green-400' : value >= 60 ? 'text-blue-400' : value >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
        {value >= 80 ? 'EXCELLENT' : value >= 60 ? 'GOOD' : value >= 40 ? 'FAIR' : 'POOR'}
      </span>
    </div>
  );
}

const qualityTimeline = Array.from({ length: 120 }, (_, i) => ({
  t: i,
  ecg: Math.max(20, Math.min(100, 80 + Math.sin(i * 0.3) * 15 + (Math.random() - 0.5) * 10)),
  ppg: Math.max(20, Math.min(100, 74 + Math.sin(i * 0.4 + 1) * 12 + (Math.random() - 0.5) * 8)),
  overall: Math.max(20, Math.min(100, 76 + Math.sin(i * 0.35 + 0.5) * 13 + (Math.random() - 0.5) * 8)),
}));

const scatterData = Array.from({ length: 60 }, (_, i) => ({
  sqi: Math.round(20 + Math.random() * 80),
  anomaly: Math.round(Math.random() * 80) / 100,
}));

const lowQualityReasons = [
  { reason: 'Motion artifact', count: 12, pct: 38 },
  { reason: 'Baseline wander', count: 8, pct: 25 },
  { reason: 'Electrode noise', count: 6, pct: 19 },
  { reason: 'Missing data', count: 4, pct: 13 },
  { reason: 'Amplitude too low', count: 2, pct: 6 },
];

export default function SignalQualityPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Signal size={24} className="text-blue-400"/> Signal Quality Analysis
          </h1>
          <p className="text-gray-400 text-sm mt-1">ECG & PPG Signal Quality Index (SQI) — Synthetic Demo Data</p>
        </div>
      </div>

      {/* Gauges */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-medium mb-6">Current Signal Quality</h3>
        <div className="flex justify-around">
          <CircularGauge value={84} label="ECG SQI" color="#34d399"/>
          <CircularGauge value={76} label="PPG SQI" color="#60a5fa"/>
          <CircularGauge value={79} label="Overall SQI" color="#a78bfa"/>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">Signal Quality Timeline (2h)</h3>
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={qualityTimeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
            <XAxis dataKey="t" tick={false}/>
            <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }}/>
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
              formatter={(v: number, name: string) => [`${v.toFixed(0)}%`, name.toUpperCase() + ' SQI']}
              labelStyle={{ display: 'none' }}/>
            <Area type="monotone" dataKey="ecg" stroke="#34d399" fill="#34d39910" strokeWidth={2} dot={false} name="ecg"/>
            <Area type="monotone" dataKey="ppg" stroke="#60a5fa" fill="#60a5fa10" strokeWidth={2} dot={false} name="ppg"/>
            <Area type="monotone" dataKey="overall" stroke="#a78bfa" fill="#a78bfa10" strokeWidth={2} strokeDasharray="6 3" dot={false} name="overall"/>
          </AreaChart>
        </ResponsiveContainer>
        <div className="flex gap-6 mt-2 text-xs">
          <span className="flex items-center gap-1 text-emerald-400"><span className="w-4 h-0.5 bg-emerald-400 inline-block"></span> ECG SQI</span>
          <span className="flex items-center gap-1 text-blue-400"><span className="w-4 h-0.5 bg-blue-400 inline-block"></span> PPG SQI</span>
          <span className="flex items-center gap-1 text-purple-400"><span className="w-4 h-0.5 bg-purple-400 inline-block"></span> Overall SQI</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Reasons */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400"/> Low Quality Reasons
          </h3>
          <div className="space-y-3">
            {lowQualityReasons.map(r => (
              <div key={r.reason}>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-300 text-sm">{r.reason}</span>
                  <span className="text-gray-400 text-sm">{r.count} events ({r.pct}%)</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${r.pct}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scatter: SQI vs Anomaly */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-2 flex items-center gap-2">
            <Info size={16} className="text-blue-400"/> SQI vs Anomaly Score Correlation
          </h3>
          <p className="text-gray-500 text-xs mb-3">Does poor signal quality correlate with false anomaly detections?</p>
          <ResponsiveContainer width="100%" height={180}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="sqi" name="SQI" unit="%" tick={{ fill: '#6b7280', fontSize: 10 }} label={{ value: 'Signal Quality (%)', position: 'insideBottom', fill: '#6b7280', fontSize: 10 }}/>
              <YAxis dataKey="anomaly" name="Anomaly" tick={{ fill: '#6b7280', fontSize: 10 }} label={{ value: 'Anomaly Score', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 10 }} width={50}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(v: number, n: string) => [v.toFixed(2), n]}/>
              <Scatter data={scatterData} name="Sample">
                {scatterData.map((entry, i) => (
                  <Cell key={i} fill={entry.sqi < 50 ? '#f87171' : entry.sqi < 70 ? '#fbbf24' : '#34d399'} opacity={0.7}/>
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-gray-600 text-xs mt-2">Low SQI points (red) show elevated anomaly scores — demonstrating why quality-aware confidence matters (QAPFL insight).</p>
        </div>
      </div>
    </div>
  );
}
