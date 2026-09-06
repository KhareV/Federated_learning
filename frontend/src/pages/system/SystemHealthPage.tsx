import { Activity, Cpu, Database, Wifi, AlertCircle, CheckCircle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const uptimeData = Array.from({ length: 60 }, (_, i) => ({
  t: i, cpu: Math.max(5, Math.min(90, 25 + Math.sin(i * 0.4) * 15 + (Math.random() - 0.5) * 10)),
  memory: Math.max(20, Math.min(95, 42 + Math.sin(i * 0.2) * 8 + (Math.random() - 0.5) * 5)),
  latency: Math.max(1, Math.min(50, 8 + Math.sin(i * 0.3) * 4 + (Math.random() - 0.5) * 3)),
}));

const services = [
  { name: 'FastAPI Server', status: 'running', port: 8000, uptime: '3h 42m', requests: 1284 },
  { name: 'SQLite Database', status: 'running', port: null, uptime: '3h 42m', requests: 8432 },
  { name: 'WebSocket Manager', status: 'running', port: 8000, uptime: '3h 42m', requests: 96 },
  { name: 'FL Server', status: 'idle', port: null, uptime: '2h 15m', requests: 70 },
  { name: 'Signal Simulator', status: 'running', port: null, uptime: '1h 22m', requests: 18400 },
  { name: 'Anomaly Detector', status: 'running', port: null, uptime: '3h 42m', requests: 4600 },
];

export default function SystemHealthPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Activity size={24} className="text-green-400"/> System Health
        </h1>
        <p className="text-gray-400 text-sm mt-1">Platform performance monitoring and service status</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'API Status', value: 'Operational', icon: <CheckCircle size={16}/>, color: 'text-green-400', bg: 'bg-green-900/20 border-green-800/30' },
          { label: 'Response Time', value: '8 ms avg', icon: <Activity size={16}/>, color: 'text-blue-400', bg: 'bg-blue-900/20 border-blue-800/30' },
          { label: 'Active Connections', value: '6', icon: <Wifi size={16}/>, color: 'text-cyan-400', bg: 'bg-cyan-900/20 border-cyan-800/30' },
          { label: 'DB Records', value: '48,234', icon: <Database size={16}/>, color: 'text-purple-400', bg: 'bg-purple-900/20 border-purple-800/30' },
        ].map(c => (
          <div key={c.label} className={`border rounded-xl p-4 ${c.bg}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={c.color}>{c.icon}</span>
              <span className="text-gray-400 text-sm">{c.label}</span>
            </div>
            <div className={`text-xl font-bold ${c.color}`}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { key: 'cpu', label: 'CPU Usage', color: '#60a5fa', unit: '%' },
          { key: 'memory', label: 'Memory Usage', color: '#a78bfa', unit: '%' },
          { key: 'latency', label: 'API Latency', color: '#34d399', unit: 'ms' },
        ].map(c => (
          <div key={c.key} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-medium mb-4">{c.label}</h3>
            <ResponsiveContainer width="100%" height={130}>
              <AreaChart data={uptimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937"/>
                <XAxis dataKey="t" tick={false}/>
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }}/>
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ display: 'none' }}
                  formatter={(v: number) => [`${v.toFixed(1)} ${c.unit}`, c.label]}/>
                <Area type="monotone" dataKey={c.key} stroke={c.color} fill={c.color + '15'} strokeWidth={2} dot={false}/>
              </AreaChart>
            </ResponsiveContainer>
            <div className="text-right text-xs text-gray-500 mt-1">Last 60s</div>
          </div>
        ))}
      </div>

      {/* Service status */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-white font-medium">Service Status</h3>
        </div>
        <div className="divide-y divide-gray-800">
          {services.map(s => (
            <div key={s.name} className="flex items-center justify-between px-5 py-3.5">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${s.status === 'running' ? 'bg-green-400 animate-pulse' : 'bg-amber-400'}`}></div>
                <div>
                  <div className="text-white text-sm font-medium">{s.name}</div>
                  {s.port && <div className="text-gray-500 text-xs">Port {s.port}</div>}
                </div>
              </div>
              <div className="flex items-center gap-8 text-sm">
                <div className="text-right">
                  <div className="text-gray-500 text-xs">Status</div>
                  <div className={s.status === 'running' ? 'text-green-400 capitalize' : 'text-amber-400 capitalize'}>{s.status}</div>
                </div>
                <div className="text-right">
                  <div className="text-gray-500 text-xs">Uptime</div>
                  <div className="text-gray-300">{s.uptime}</div>
                </div>
                <div className="text-right w-20">
                  <div className="text-gray-500 text-xs">Requests</div>
                  <div className="text-gray-300">{s.requests.toLocaleString()}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
