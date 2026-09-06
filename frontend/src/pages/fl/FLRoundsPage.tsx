import { useState } from 'react';
import { GitMerge, ChevronDown, ChevronRight } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const ROUNDS = Array.from({ length: 10 }, (_, i) => ({
  round: i + 1,
  clients: ['C1','C2','C3','C4','C5','C6','C7','C8'].slice(0, 6 + (i % 3)),
  avg_local_loss: parseFloat((0.32 - i * 0.018 + (Math.random() - 0.5) * 0.01).toFixed(4)),
  global_loss: parseFloat((0.28 - i * 0.016 + (Math.random() - 0.5) * 0.008).toFixed(4)),
  global_accuracy: parseFloat((0.81 + i * 0.008 + (Math.random() - 0.5) * 0.003).toFixed(4)),
  global_f1: parseFloat((0.795 + i * 0.009 + (Math.random() - 0.5) * 0.003).toFixed(4)),
  avg_sqi: parseFloat((72 + i * 0.5 + (Math.random() - 0.5) * 2).toFixed(1)),
  comm_cost: Math.round(2.4 + Math.random() * 0.4),
  training_time: parseFloat((12.3 + Math.random() * 2).toFixed(1)),
  strategy: 'QAPFL',
}));

export default function FLRoundsPage() {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <GitMerge size={24} className="text-blue-400"/> Training Rounds
        </h1>
        <p className="text-gray-400 text-sm mt-1">FL training round history and per-round metrics</p>
      </div>

      {/* Performance curves */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Loss Convergence</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={ROUNDS}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 10 }} label={{ value: 'Round', position: 'insideBottom', fill: '#6b7280', fontSize: 10 }}/>
              <YAxis tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelFormatter={v => `Round ${v}`}/>
              <Line type="monotone" dataKey="global_loss" stroke="#f87171" strokeWidth={2} dot={{ r: 3 }} name="Global Loss"/>
              <Line type="monotone" dataKey="avg_local_loss" stroke="#fbbf24" strokeWidth={2} strokeDasharray="4 2" dot={false} name="Avg Local Loss"/>
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Accuracy & F1</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={ROUNDS}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <YAxis domain={[0.75, 1.0]} tick={{ fill: '#6b7280', fontSize: 10 }}/>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelFormatter={v => `Round ${v}`}/>
              <Line type="monotone" dataKey="global_accuracy" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} name="Global Accuracy"/>
              <Line type="monotone" dataKey="global_f1" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3 }} name="Global F1"/>
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Rounds table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-9 gap-2 px-4 py-3 border-b border-gray-800 text-xs text-gray-500 font-medium uppercase">
          <div className="col-span-1">Round</div>
          <div className="col-span-1">Clients</div>
          <div className="col-span-1">Avg Loss</div>
          <div className="col-span-1">Global Loss</div>
          <div className="col-span-1">Accuracy</div>
          <div className="col-span-1">F1</div>
          <div className="col-span-1">Avg SQI</div>
          <div className="col-span-1">Comm (MB)</div>
          <div className="col-span-1">Time (s)</div>
        </div>
        {ROUNDS.map(r => (
          <div key={r.round}>
            <button onClick={() => setExpanded(expanded === r.round ? null : r.round)}
              className="w-full grid grid-cols-9 gap-2 px-4 py-3 border-b border-gray-800/50 hover:bg-gray-800/50 text-sm transition-colors">
              <div className="col-span-1 flex items-center gap-2 text-white font-medium">
                {expanded === r.round ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}
                #{r.round}
              </div>
              <div className="col-span-1 text-gray-400">{r.clients.length}</div>
              <div className="col-span-1 text-amber-400">{r.avg_local_loss}</div>
              <div className="col-span-1 text-red-400">{r.global_loss}</div>
              <div className="col-span-1 text-green-400">{r.global_accuracy}</div>
              <div className="col-span-1 text-blue-400">{r.global_f1}</div>
              <div className="col-span-1 text-gray-300">{r.avg_sqi}%</div>
              <div className="col-span-1 text-gray-300">{r.comm_cost} MB</div>
              <div className="col-span-1 text-gray-300">{r.training_time}s</div>
            </button>
            {expanded === r.round && (
              <div className="px-6 py-4 bg-gray-800/30 border-b border-gray-800 text-sm">
                <div className="grid grid-cols-3 gap-4">
                  <div><span className="text-gray-500">Strategy:</span> <span className="text-white">{r.strategy}</span></div>
                  <div><span className="text-gray-500">Participating:</span> <span className="text-white">{r.clients.join(', ')}</span></div>
                  <div><span className="text-gray-500">Aggregation:</span> <span className="text-white">Quality-aware softmax</span></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
