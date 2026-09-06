import { BarChart as BarC, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function ModelComparisonPage() {
  const data = [
    { name: 'FedAvg', f1: 0.81, accuracy: 0.83 },
    { name: 'FedProx', f1: 0.83, accuracy: 0.85 },
    { name: 'Per-FedAvg', f1: 0.86, accuracy: 0.87 },
    { name: 'QAPFL', f1: 0.92, accuracy: 0.94 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Model Comparison</h1>
      
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-96 flex flex-col">
        <h3 className="text-white mb-4">F1 Score & Accuracy Comparison</h3>
        <div className="flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarC data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis domain={[0.6, 1]} stroke="#9ca3af" />
              <Tooltip contentStyle={{backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff'}} />
              <Legend />
              <Bar dataKey="f1" fill="#8b5cf6" name="F1 Score" radius={[4, 4, 0, 0]} />
              <Bar dataKey="accuracy" fill="#10b981" name="Accuracy" radius={[4, 4, 0, 0]} />
            </BarC>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}