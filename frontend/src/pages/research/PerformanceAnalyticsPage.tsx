import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LineChart, Line } from 'recharts';

const experiments = [
  { name: 'E1: Centralized', accuracy: 0.871, f1: 0.856, fpr: 0.122, comms: 0, time: 45.2 },
  { name: 'E2: FedAvg', accuracy: 0.841, f1: 0.826, fpr: 0.142, comms: 24.3, time: 18.2 },
  { name: 'E3: PersonalFL', accuracy: 0.862, f1: 0.849, fpr: 0.121, comms: 26.1, time: 22.5 },
  { name: 'E4: QAPFL', accuracy: 0.896, f1: 0.884, fpr: 0.082, comms: 24.3, time: 23.1 },
];

const COLORS = ['#6b7280', '#60a5fa', '#34d399', '#3b82f6'];
const roundMetrics = Array.from({ length: 10 }, (_, i) => ({
  round: i + 1,
  e2: parseFloat((0.826 + i * 0.002).toFixed(4)),
  e3: parseFloat((0.849 + i * 0.002).toFixed(4)),
  e4: parseFloat((0.884 + i * 0.003).toFixed(4)),
}));

export default function PerformanceAnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Performance Analytics</h1>
        <p className="text-gray-400 text-sm mt-1">Cross-experiment performance summary — Synthetic Research Data</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">F1 Score Comparison</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={experiments} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false}/>
              <XAxis type="number" domain={[0.7, 1.0]} tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 9 }} width={100}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(v: number) => [v.toFixed(3), 'F1']}/>
              <Bar dataKey="f1" radius={[0,4,4,0]}>
                {experiments.map((_, i) => <Cell key={i} fill={COLORS[i]}/>)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">F1 vs Training Round</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={roundMetrics}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <YAxis domain={[0.8, 1.0]} tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelFormatter={v => `Round ${v}`}/>
              <Line dataKey="e2" stroke="#60a5fa" strokeWidth={2} dot={false} name="FedAvg"/>
              <Line dataKey="e3" stroke="#34d399" strokeWidth={2} dot={false} name="PersonalFL"/>
              <Line dataKey="e4" stroke="#3b82f6" strokeWidth={2.5} dot={false} name="QAPFL"/>
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2 text-xs">
            <span className="text-blue-400">— FedAvg</span>
            <span className="text-emerald-400">— PersonalFL</span>
            <span className="text-blue-600 font-bold">— QAPFL</span>
          </div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-6 px-4 py-3 border-b border-gray-800 text-xs text-gray-500 uppercase font-medium">
          <div className="col-span-2">Experiment</div>
          <div>Accuracy</div><div>F1</div><div>FPR</div><div>Comm/Time</div>
        </div>
        {experiments.map((e, i) => (
          <div key={e.name} className="grid grid-cols-6 px-4 py-3 border-b border-gray-800/50 text-sm">
            <div className="col-span-2 flex items-center gap-2">
              <span className="w-3 h-3 rounded inline-block flex-shrink-0" style={{ backgroundColor: COLORS[i] }}></span>
              <span className="text-gray-300 text-xs">{e.name}</span>
            </div>
            <div className="text-gray-300">{e.accuracy.toFixed(3)}</div>
            <div className={i === 3 ? 'text-blue-400 font-bold' : 'text-gray-300'}>{e.f1.toFixed(3)}</div>
            <div className={i === 3 ? 'text-green-400 font-bold' : 'text-gray-300'}>{e.fpr.toFixed(3)}</div>
            <div className="text-gray-500 text-xs">{e.comms > 0 ? `${e.comms}MB` : 'N/A'} / {e.time.toFixed(0)}s</div>
          </div>
        ))}
      </div>
      <p className="text-gray-600 text-xs">All performance metrics are computed from synthetic physiological data simulations. Not clinically validated.</p>
    </div>
  );
}
