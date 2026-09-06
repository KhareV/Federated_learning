import { Database, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const CLIENTS = ['Alice','Bob','Carol','David','Eve','Frank','Grace','Henry'];
const personalData = CLIENTS.map((name, i) => ({
  name,
  global_f1: parseFloat((0.820 + i * 0.003 + Math.random() * 0.005).toFixed(3)),
  personal_f1: parseFloat((0.855 + i * 0.002 + Math.random() * 0.005).toFixed(3)),
  rounds: 3 + i,
  samples: [5000,7000,4000,3500,2000,6000,5500,4500][i],
  version: `v${3 + (i > 3 ? 1 : 0)}p${i+1}`,
}));

export default function PersonalModelsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Database size={24} className="text-teal-400"/> Personal Models
        </h1>
        <p className="text-gray-400 text-sm mt-1">Per-client personalized models — fine-tuned from global model</p>
      </div>

      {/* Comparison chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">F1 Score: Before vs After Personalization</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={personalData} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }}/>
            <YAxis domain={[0.75, 1.0]} tick={{ fill: '#6b7280', fontSize: 11 }}/>
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}/>
            <Bar dataKey="global_f1" name="Global Model F1" fill="#6b7280" radius={[4,4,0,0]}/>
            <Bar dataKey="personal_f1" name="Personalized F1" fill="#14b8a6" radius={[4,4,0,0]}/>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-2 text-xs">
          <span className="flex items-center gap-1 text-gray-400"><span className="w-3 h-3 bg-gray-500 rounded inline-block"></span> Global Model</span>
          <span className="flex items-center gap-1 text-teal-400"><span className="w-3 h-3 bg-teal-500 rounded inline-block"></span> Personalized Model</span>
        </div>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-7 px-4 py-3 border-b border-gray-800 text-xs text-gray-500 font-medium uppercase">
          <div>Client</div><div>Version</div><div>Rounds</div><div>Samples</div>
          <div>Global F1</div><div>Personal F1</div><div>Improvement</div>
        </div>
        {personalData.map(d => {
          const improvement = ((d.personal_f1 - d.global_f1) / d.global_f1 * 100);
          return (
            <div key={d.name} className="grid grid-cols-7 px-4 py-3 border-b border-gray-800/50 text-sm hover:bg-gray-800/30 transition-colors">
              <div className="text-white font-medium">{d.name}</div>
              <div className="text-gray-400 font-mono text-xs">{d.version}</div>
              <div className="text-gray-300">{d.rounds}</div>
              <div className="text-gray-300">{d.samples.toLocaleString()}</div>
              <div className="text-gray-400">{d.global_f1.toFixed(3)}</div>
              <div className="text-teal-400 font-medium">{d.personal_f1.toFixed(3)}</div>
              <div className="text-green-400 flex items-center gap-1">
                <TrendingUp size={12}/>+{improvement.toFixed(1)}%
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-green-900/10 border border-green-800/30 rounded-xl p-4 text-green-300 text-sm">
        <strong>Research Result:</strong> Personalization improves local F1 by an average of {(personalData.reduce((s, d) => s + (d.personal_f1 - d.global_f1) / d.global_f1 * 100, 0) / personalData.length).toFixed(1)}% over the global model. This demonstrates the benefit of the personalization phase in QAPFL. All data is synthetic.
      </div>
    </div>
  );
}
