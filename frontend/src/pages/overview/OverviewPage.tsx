import { useQuery } from '@tanstack/react-query';
import { Activity, Heart, Droplets, Wifi, AlertTriangle, Brain, TrendingUp, Clock } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useMonitoringStore } from '../../stores/monitoringStore';
import { systemApi, anomalyApi, monitoringApi } from '../../services/api';

// Generate synthetic demo data for charts
const generateHRData = () => Array.from({ length: 60 }, (_, i) => ({
  time: `${60-i}m`, hr: 68 + Math.sin(i * 0.3) * 8 + (Math.random() - 0.5) * 4
})).reverse();

const generateSPO2Data = () => Array.from({ length: 60 }, (_, i) => ({
  time: `${60-i}m`, spo2: 97.5 + Math.sin(i * 0.2) * 1 + (Math.random() - 0.5) * 0.5
})).reverse();

const generateAnomalyData = () => Array.from({ length: 60 }, (_, i) => ({
  time: `${60-i}m`, score: Math.max(0, 0.1 + Math.sin(i * 0.4) * 0.08 + (Math.random() - 0.5) * 0.05)
})).reverse();

const generateSQIData = () => Array.from({ length: 60 }, (_, i) => ({
  time: `${60-i}m`, sqi: Math.min(100, Math.max(40, 78 + Math.sin(i * 0.5) * 12 + (Math.random() - 0.5) * 8))
})).reverse();

const recentEvents = [
  { time: '14:22', type: 'info', icon: '🔵', text: 'Monitoring session started', source: 'System' },
  { time: '14:18', type: 'warning', icon: '🟡', text: 'Signal quality warning — ECG SQI dropped to 62%', source: 'Signal QA' },
  { time: '14:15', type: 'success', icon: '🟢', text: 'FL Round 7 completed — Global F1: 0.891', source: 'FL Server' },
  { time: '14:10', type: 'alert', icon: '🟠', text: 'Low-confidence anomaly event detected', source: 'Anomaly Detector' },
  { time: '14:05', type: 'info', icon: '🔵', text: 'Personal baseline updated — 1,240 samples', source: 'Baseline Learner' },
  { time: '13:58', type: 'info', icon: '🔵', text: 'Device connected — ESP32_001 (BLE)', source: 'Device Manager' },
];

function StatCard({ label, value, unit, icon, color, status }: any) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-gray-400 text-sm">{label}</span>
        <span className={`p-2 rounded-lg ${color}`}>{icon}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold text-white">{value}</span>
        <span className="text-gray-400 text-sm mb-1">{unit}</span>
      </div>
      {status && <div className={`mt-2 text-xs font-medium px-2 py-0.5 rounded-full inline-block ${
        status === 'Normal' ? 'bg-green-900/50 text-green-400' :
        status === 'Warning' ? 'bg-amber-900/50 text-amber-400' :
        status === 'Good' || status === 'Excellent' ? 'bg-blue-900/50 text-blue-400' : 'bg-gray-800 text-gray-400'
      }`}>{status}</div>}
    </div>
  );
}

export default function OverviewPage() {
  const { liveHR, liveSPO2, ecgSQI, ppgSQI, anomalyClass } = useMonitoringStore();
  const hrData = generateHRData();
  const spo2Data = generateSPO2Data();
  const anomalyData = generateAnomalyData();
  const sqiData = generateSQIData();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Overview Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Real-time wearable health monitoring & federated learning research platform</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-green-900/20 border border-green-800/30 rounded-lg px-3 py-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            <span className="text-green-400 text-sm font-medium">Live</span>
          </div>
          <div className="text-gray-500 text-sm flex items-center gap-1">
            <Clock size={14}/> {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard label="Heart Rate" value={liveHR || 74} unit="BPM" icon={<Heart size={16}/>} color="bg-red-900/40 text-red-400" status="Normal"/>
        <StatCard label="SpO₂" value={liveSPO2 || 98.2} unit="%" icon={<Droplets size={16}/>} color="bg-cyan-900/40 text-cyan-400" status="Good"/>
        <StatCard label="ECG SQI" value={ecgSQI || 84} unit="%" icon={<Activity size={16}/>} color="bg-green-900/40 text-green-400" status="Excellent"/>
        <StatCard label="PPG SQI" value={ppgSQI || 76} unit="%" icon={<TrendingUp size={16}/>} color="bg-blue-900/40 text-blue-400" status="Good"/>
        <StatCard label="Anomaly Risk" value={(anomalyClass === 'NORMAL' ? 'Low' : anomalyClass === 'POSSIBLE_ANOMALY' ? 'Med' : 'High')} unit="" icon={<AlertTriangle size={16}/>} color="bg-amber-900/40 text-amber-400" status={anomalyClass || "NORMAL"}/>
        <StatCard label="Device" value="1" unit="online" icon={<Wifi size={16}/>} color="bg-indigo-900/40 text-indigo-400" status="Connected"/>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Heart size={16} className="text-red-400"/> Heart Rate (Last 60 min)
          </h3>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={hrData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="time" tick={{fill:'#6b7280', fontSize:11}} interval={14}/>
              <YAxis domain={[50, 120]} tick={{fill:'#6b7280', fontSize:11}}/>
              <Tooltip contentStyle={{backgroundColor:'#1f2937', border:'1px solid #374151', borderRadius:'8px'}} labelStyle={{color:'#e5e7eb'}} itemStyle={{color:'#f87171'}}/>
              <Area type="monotone" dataKey="hr" stroke="#f87171" fill="#f871711a" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex gap-2 text-xs text-gray-500 mt-1">
            <span className="text-green-400">↑ Synthetic Demo Data</span>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Droplets size={16} className="text-cyan-400"/> SpO₂ (Last 60 min)
          </h3>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={spo2Data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="time" tick={{fill:'#6b7280', fontSize:11}} interval={14}/>
              <YAxis domain={[93, 101]} tick={{fill:'#6b7280', fontSize:11}}/>
              <Tooltip contentStyle={{backgroundColor:'#1f2937', border:'1px solid #374151', borderRadius:'8px'}} labelStyle={{color:'#e5e7eb'}} itemStyle={{color:'#22d3ee'}}/>
              <Area type="monotone" dataKey="spo2" stroke="#22d3ee" fill="#22d3ee1a" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex gap-2 text-xs text-gray-500 mt-1">
            <span className="text-green-400">↑ Synthetic Demo Data</span>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400"/> Anomaly Score (Last 60 min)
          </h3>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={anomalyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="time" tick={{fill:'#6b7280', fontSize:11}} interval={14}/>
              <YAxis domain={[0, 1]} tick={{fill:'#6b7280', fontSize:11}}/>
              <Tooltip contentStyle={{backgroundColor:'#1f2937', border:'1px solid #374151', borderRadius:'8px'}} labelStyle={{color:'#e5e7eb'}} itemStyle={{color:'#fbbf24'}}/>
              <Area type="monotone" dataKey="score" stroke="#fbbf24" fill="#fbbf241a" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Activity size={16} className="text-blue-400"/> Signal Quality (Last 60 min)
          </h3>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={sqiData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
              <XAxis dataKey="time" tick={{fill:'#6b7280', fontSize:11}} interval={14}/>
              <YAxis domain={[0, 100]} tick={{fill:'#6b7280', fontSize:11}}/>
              <Tooltip contentStyle={{backgroundColor:'#1f2937', border:'1px solid #374151', borderRadius:'8px'}} labelStyle={{color:'#e5e7eb'}} itemStyle={{color:'#60a5fa'}}/>
              <Area type="monotone" dataKey="sqi" stroke="#60a5fa" fill="#60a5fa1a" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Summary + Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Brain size={16} className="text-purple-400"/> AI System Summary
          </h3>
          <div className="bg-purple-900/10 border border-purple-800/20 rounded-lg p-4 text-gray-300 text-sm leading-relaxed">
            <p>Heart rate has remained within the user's learned baseline for the last 42 minutes (mean: 74 BPM, baseline: 68–82 BPM). SpO₂ is stable at 98.2%, within the normal monitoring range.</p>
            <p className="mt-2">Signal quality is currently <span className="text-green-400 font-medium">GOOD</span> (ECG SQI: 84%, PPG SQI: 76%). No high-confidence anomalies detected in the last monitoring window.</p>
            <p className="mt-2">FL Round 7 completed with QAPFL strategy — global model F1 improved from 0.872 → 0.891.</p>
          </div>
          <p className="text-gray-600 text-xs mt-3">⚠️ Research summary — not a medical assessment. <span className="text-blue-400">Synthetic Demo Data.</span></p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Clock size={16} className="text-gray-400"/> Recent Events
          </h3>
          <div className="space-y-3">
            {recentEvents.map((event, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="text-lg flex-shrink-0 mt-0.5">{event.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-300 text-sm">{event.text}</p>
                  <p className="text-gray-600 text-xs mt-0.5">{event.time} · {event.source}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}