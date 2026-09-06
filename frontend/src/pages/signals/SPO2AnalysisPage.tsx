import { Droplets, TrendingDown } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell } from 'recharts';

const spo2Series = Array.from({ length: 120 }, (_, i) => ({
  t: i,
  spo2: Math.max(94, Math.min(100, 97.8 + Math.sin(i * 0.2) * 0.8 + (Math.random() - 0.5) * 0.4)),
}));

const variabilityHist = [
  { range: '94–95', count: 1 }, { range: '95–96', count: 3 }, { range: '96–97', count: 12 },
  { range: '97–98', count: 38 }, { range: '98–99', count: 52 }, { range: '99–100', count: 14 },
];

function GaugeSVG({ value, max = 100, color }: { value: number; max?: number; color: string }) {
  const pct = value / max;
  const r = 70;
  const cx = 90;
  const cy = 90;
  const startAngle = Math.PI * 0.75;
  const endAngle = Math.PI * 2.25;
  const valueAngle = startAngle + pct * (endAngle - startAngle);
  const toX = (angle: number) => cx + r * Math.cos(angle);
  const toY = (angle: number) => cy + r * Math.sin(angle);
  const arc = (a1: number, a2: number, fill: string) => {
    const x1 = toX(a1); const y1 = toY(a1);
    const x2 = toX(a2); const y2 = toY(a2);
    const large = a2 - a1 > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
  };
  return (
    <svg viewBox="0 0 180 120" className="w-full max-w-[180px]">
      <path d={arc(startAngle, endAngle, '#374151')} fill="none" stroke="#374151" strokeWidth="14" strokeLinecap="round"/>
      <path d={arc(startAngle, valueAngle, color)} fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"/>
      <text x={cx} y={cy - 4} textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">{value.toFixed(1)}</text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="#6b7280" fontSize="11">%</text>
    </svg>
  );
}

export default function SPO2AnalysisPage() {
  const current = 98.2;
  const color = current >= 97 ? '#22d3ee' : current >= 95 ? '#fbbf24' : '#f87171';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Droplets size={24} className="text-cyan-400"/> SpO₂ Analysis
          </h1>
          <p className="text-gray-400 text-sm mt-1">Oxygen saturation analysis — Synthetic Demo Data</p>
        </div>
        <span className="text-xs text-amber-400 bg-amber-900/20 border border-amber-800/30 px-3 py-1 rounded-full">Research Prototype — Configurable Thresholds</span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Gauge */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col items-center">
          <h3 className="text-white font-medium mb-2">Current SpO₂</h3>
          <GaugeSVG value={current} max={100} color={color} />
          <div className="mt-2 text-center">
            <div className="text-xs text-gray-500">Measurement quality</div>
            <div className="text-emerald-400 text-sm font-medium mt-1">High (Confidence: 0.91)</div>
          </div>
          <div className="mt-3 p-3 bg-cyan-900/10 border border-cyan-800/20 rounded-lg text-xs text-cyan-300">
            Within expected research range for this client profile
          </div>
        </div>

        {/* Trend */}
        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">SpO₂ Trend (2h)</h3>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={spo2Series}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="t" tick={false}/>
              <YAxis domain={[93, 101]} tick={{ fill: '#6b7280', fontSize: 11 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(v: number) => [`${v.toFixed(1)}%`, 'SpO₂']} labelStyle={{ display: 'none' }}/>
              <ReferenceLine y={95} stroke="#fbbf24" strokeDasharray="4 4" label={{ value: 'Research threshold (95%)', fill: '#fbbf24', fontSize: 10 }}/>
              <Area type="monotone" dataKey="spo2" stroke="#22d3ee" fill="#22d3ee15" strokeWidth={2} dot={false}/>
            </AreaChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-4 gap-3 mt-3">
            {[
              { label: 'Mean', value: '97.8%' }, { label: 'Min', value: '96.9%' },
              { label: 'Max', value: '99.1%' }, { label: 'Std Dev', value: '±0.47%' },
            ].map(s => (
              <div key={s.label} className="bg-gray-800 rounded-lg p-2 text-center">
                <div className="text-gray-500 text-xs">{s.label}</div>
                <div className="text-white text-sm font-medium mt-0.5">{s.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Variability Distribution */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">SpO₂ Distribution</h3>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={variabilityHist}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
            <XAxis dataKey="range" tick={{ fill: '#6b7280', fontSize: 11 }}/>
            <YAxis tick={{ fill: '#6b7280', fontSize: 11 }}/>
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
              formatter={(v: number) => [`${v} readings`, 'Count']}/>
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {variabilityHist.map((entry, index) => (
                <Cell key={index} fill={entry.range === '97–98' || entry.range === '98–99' ? '#22d3ee' : entry.range === '94–95' || entry.range === '95–96' ? '#fbbf24' : '#60a5fa'}/>
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className="text-gray-600 text-xs mt-2">
          ⚠️ Research thresholds are configurable and not intended as clinical diagnostic criteria. Data is synthetic.
        </p>
      </div>
    </div>
  );
}
