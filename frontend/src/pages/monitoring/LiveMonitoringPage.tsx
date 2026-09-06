import { useState, useEffect } from 'react';
import { Activity, Heart, Droplets, AlertTriangle, Battery, Wifi, Play, Square } from 'lucide-react';
import { useMonitoringStore } from '../../stores/monitoringStore';

export default function LiveMonitoringPage() {
  const { isMonitoring, liveHR, liveSPO2, ecgSQI, ppgSQI, anomalyClass, setMonitoring } = useMonitoringStore();
  const [ecgData, setEcgData] = useState<number[]>([]);

  useEffect(() => {
    if (!isMonitoring) return;
    const interval = setInterval(() => {
      setEcgData(prev => [...prev.slice(-100), Math.random() * 100]);
    }, 100);
    return () => clearInterval(interval);
  }, [isMonitoring]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-gray-900 p-4 rounded-xl border border-gray-800">
        <div className="flex gap-4">
          <div className="flex items-center gap-2"><Wifi size={16} className="text-green-400"/> ESP32_001 connected</div>
          <div className="flex items-center gap-2"><Battery size={16} className="text-green-400"/> 82%</div>
        </div>
        <div>
          {isMonitoring ? 
            <button onClick={() => setMonitoring(false)} className="flex items-center gap-2 bg-red-600 px-4 py-2 rounded text-white"><Square size={16}/> Stop</button> :
            <button onClick={() => setMonitoring(true)} className="flex items-center gap-2 bg-blue-600 px-4 py-2 rounded text-white"><Play size={16}/> Start Session</button>
          }
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-64 relative overflow-hidden flex flex-col">
            <h3 className="text-white mb-2">Live ECG</h3>
            <div className="flex-1 flex items-end overflow-hidden">
               {/* Extremely simple placeholder for scrolling D3 waveform */}
               <div className="w-full flex items-end h-full gap-1">
                 {ecgData.map((d, i) => (
                   <div key={i} className="bg-green-500 w-1" style={{ height: `${d}%` }}></div>
                 ))}
               </div>
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-64 flex flex-col">
            <h3 className="text-white mb-2">Live PPG</h3>
            <div className="flex-1 flex items-center justify-center text-gray-500">PPG Waveform placeholder</div>
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
            <Heart size={32} className="mx-auto text-red-400 animate-pulse-slow mb-2" />
            <div className="text-6xl font-bold text-white">{isMonitoring ? (liveHR || 72) : '--'}</div>
            <div className="text-gray-400">BPM</div>
          </div>
          
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
            <Droplets size={32} className="mx-auto text-cyan-400 mb-2" />
            <div className="text-6xl font-bold text-white">{isMonitoring ? (liveSPO2 || 98) : '--'}</div>
            <div className="text-gray-400">SpO₂ %</div>
          </div>
          
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
             <h3 className="text-white mb-4">Signal Quality</h3>
             <div className="space-y-4">
               <div>
                 <div className="flex justify-between text-sm mb-1"><span>ECG</span><span>{ecgSQI}%</span></div>
                 <div className="w-full bg-gray-800 h-2 rounded"><div className="bg-green-400 h-2 rounded" style={{width: `${ecgSQI}%`}}></div></div>
               </div>
               <div>
                 <div className="flex justify-between text-sm mb-1"><span>PPG</span><span>{ppgSQI}%</span></div>
                 <div className="w-full bg-gray-800 h-2 rounded"><div className="bg-blue-400 h-2 rounded" style={{width: `${ppgSQI}%`}}></div></div>
               </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}