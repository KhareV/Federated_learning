import { Layers } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AggregationPage() {
  const data = [
    { client: 'C1', weight: 0.35, quality: 92, sqi: 95 },
    { client: 'C2', weight: 0.25, quality: 85, sqi: 88 },
    { client: 'C3', weight: 0.15, quality: 72, sqi: 70 },
    { client: 'C4', weight: 0.05, quality: 45, sqi: 50 },
    { client: 'C5', weight: 0.20, quality: 81, sqi: 82 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">QAPFL Quality-Aware Aggregation</h1>
      
      <div className="bg-blue-900/20 border border-blue-800 p-6 rounded-xl text-blue-100">
        <h3 className="font-bold flex items-center gap-2 mb-2"><Layers size={20}/> QAPFL Weighting Strategy</h3>
        <p className="text-sm">Unlike FedAvg which weights clients by dataset size, QAPFL scales weights according to a combination of Signal Quality Index (SQI), historical local performance, and dataset uncertainty.</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-96 flex flex-col">
          <h3 className="text-white mb-4">Aggregation Weights</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="client" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff'}} />
                <Bar dataKey="weight" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-96 flex flex-col">
          <h3 className="text-white mb-4">Signal Quality Influence</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="client" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff'}} />
                <Bar dataKey="quality" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}