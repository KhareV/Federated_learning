import { AlertTriangle, CheckCircle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AnomalyDetectionPage() {
  const data = Array.from({length: 40}, (_, i) => ({
    time: i,
    score: i > 25 && i < 30 ? 0.8 + Math.random() * 0.2 : 0.1 + Math.random() * 0.1
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Anomaly Detection</h1>
      
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-64 flex flex-col">
        <h3 className="text-white mb-4">Anomaly Score Timeline</h3>
        <div className="flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9ca3af" />
              <YAxis domain={[0, 1]} stroke="#9ca3af" />
              <Tooltip contentStyle={{backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff'}} />
              <Area type="monotone" dataKey="score" stroke="#f43f5e" fill="#f43f5e33" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white mb-4">Recent Events</h3>
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase border-b border-gray-800">
            <tr>
              <th className="px-6 py-3">Time</th>
              <th className="px-6 py-3">Score</th>
              <th className="px-6 py-3">Confidence</th>
              <th className="px-6 py-3">Classification</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-800 text-gray-300">
              <td className="px-6 py-4">14:10:22</td>
              <td className="px-6 py-4 text-red-400">0.91</td>
              <td className="px-6 py-4 text-green-400">High (95%)</td>
              <td className="px-6 py-4 flex items-center gap-2"><AlertTriangle size={14} className="text-red-400"/> HIGH_CONFIDENCE_ANOMALY</td>
            </tr>
            <tr className="border-b border-gray-800 text-gray-300">
              <td className="px-6 py-4">13:45:10</td>
              <td className="px-6 py-4 text-amber-400">0.65</td>
              <td className="px-6 py-4 text-amber-400">Low (40%)</td>
              <td className="px-6 py-4 flex items-center gap-2"><AlertTriangle size={14} className="text-amber-400"/> LOW_CONFIDENCE_EVENT</td>
            </tr>
            <tr className="text-gray-300">
              <td className="px-6 py-4">13:12:00</td>
              <td className="px-6 py-4 text-green-400">0.12</td>
              <td className="px-6 py-4 text-green-400">High (98%)</td>
              <td className="px-6 py-4 flex items-center gap-2"><CheckCircle size={14} className="text-green-400"/> NORMAL</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}