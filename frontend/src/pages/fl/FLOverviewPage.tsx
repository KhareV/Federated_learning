import { useFLStore } from '../../stores/flStore';
import { Network, Server, Play, Square, Settings } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function FLOverviewPage() {
  const { isTraining, currentRound, activeClients, globalAccuracy, setTraining } = useFLStore();
  
  const mockHistory = Array.from({length: 10}, (_, i) => ({
    round: i + 1,
    accuracy: 0.75 + (i * 0.02) + (Math.random() * 0.01)
  }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Federated Learning Overview</h1>
        {isTraining ? 
          <button onClick={() => setTraining(false)} className="flex items-center gap-2 bg-red-600 px-4 py-2 rounded text-white"><Square size={16}/> Stop Training</button> :
          <button onClick={() => setTraining(true)} className="flex items-center gap-2 bg-blue-600 px-4 py-2 rounded text-white"><Play size={16}/> Start Training</button>
        }
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-sm">Status</div>
          <div className={`text-2xl font-bold ${isTraining ? 'text-green-400' : 'text-gray-300'}`}>{isTraining ? 'Training' : 'Idle'}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-sm">Round</div>
          <div className="text-2xl font-bold text-white">{currentRound} / 100</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-sm">Active Clients</div>
          <div className="text-2xl font-bold text-white">{activeClients}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-sm">Global Accuracy</div>
          <div className="text-2xl font-bold text-white">{(globalAccuracy * 100).toFixed(1)}%</div>
        </div>
      </div>
      
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-96 flex flex-col">
         <h3 className="text-white mb-4">Model Performance (Accuracy)</h3>
         <div className="flex-1">
           <ResponsiveContainer width="100%" height="100%">
             <LineChart data={mockHistory}>
               <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
               <XAxis dataKey="round" stroke="#9ca3af" />
               <YAxis domain={[0.6, 1]} stroke="#9ca3af" />
               <Tooltip contentStyle={{backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff'}} />
               <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={3} />
             </LineChart>
           </ResponsiveContainer>
         </div>
      </div>
    </div>
  );
}