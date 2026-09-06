import { useState } from 'react';
import { Bell, Plus, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';

const RULES = [
  { id: '1', name: 'High Anomaly Alert', condition: 'anomaly_score > 0.7 AND sqi > 60', severity: 'critical', enabled: true, triggers: 12 },
  { id: '2', name: 'Low SpO₂ Warning', condition: 'spo2 < 94.0 AND spo2_confidence > 0.8', severity: 'warning', enabled: true, triggers: 3 },
  { id: '3', name: 'Tachycardia Alert', condition: 'heart_rate > 120 AND duration > 30s', severity: 'warning', enabled: true, triggers: 2 },
  { id: '4', name: 'Poor Signal Quality', condition: 'overall_sqi < 40', severity: 'info', enabled: false, triggers: 47 },
  { id: '5', name: 'Low Battery Warning', condition: 'battery_level < 20', severity: 'warning', enabled: true, triggers: 5 },
  { id: '6', name: 'FL Round Failed', condition: 'active_clients < min_clients', severity: 'warning', enabled: true, triggers: 0 },
];

const RECENT = [
  { id: 'A1', rule: 'High Anomaly Alert', client: 'Frank (C06)', time: '13:42', resolved: true, severity: 'critical' },
  { id: 'A2', rule: 'Poor Signal Quality', client: 'Carol (C03)', time: '14:18', resolved: false, severity: 'info' },
  { id: 'A3', rule: 'Low Battery Warning', client: 'Eve (C05)', time: '13:45', resolved: false, severity: 'warning' },
  { id: 'A4', rule: 'Tachycardia Alert', client: 'Frank (C06)', time: '12:30', resolved: true, severity: 'warning' },
];

const SEV: Record<string, string> = {
  critical: 'text-red-400 bg-red-900/30 border-red-800/50',
  warning: 'text-amber-400 bg-amber-900/30 border-amber-800/50',
  info: 'text-blue-400 bg-blue-900/30 border-blue-800/50',
};

export default function AlertsPage() {
  const [rules, setRules] = useState(RULES);
  const toggle = (id: string) => setRules(r => r.map(x => x.id === id ? { ...x, enabled: !x.enabled } : x));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Bell size={24} className="text-amber-400"/> Alerts & Rules</h1>
          <p className="text-gray-400 text-sm mt-1">{rules.filter(r => r.enabled).length} active rules · Configurable research thresholds</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">
          <Plus size={14}/> New Rule
        </button>
      </div>

      {/* Rules */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-white font-medium">Alert Rules</h3>
        </div>
        <div className="divide-y divide-gray-800">
          {rules.map(r => (
            <div key={r.id} className="flex items-center gap-4 px-5 py-4">
              <button onClick={() => toggle(r.id)} className="flex-shrink-0">
                {r.enabled ? <ToggleRight size={24} className="text-blue-400"/> : <ToggleLeft size={24} className="text-gray-600"/>}
              </button>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-white text-sm font-medium">{r.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${SEV[r.severity]}`}>{r.severity}</span>
                  {!r.enabled && <span className="text-gray-600 text-xs">disabled</span>}
                </div>
                <div className="text-gray-500 text-xs mt-0.5 font-mono">{r.condition}</div>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-gray-500 text-xs">Triggered</div>
                <div className="text-white text-sm">{r.triggers}x</div>
              </div>
              <button className="text-gray-600 hover:text-red-400 p-1"><Trash2 size={14}/></button>
            </div>
          ))}
        </div>
      </div>

      {/* Recent alerts */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-white font-medium">Recent Alert Events</h3>
        </div>
        <div className="divide-y divide-gray-800">
          {RECENT.map(a => (
            <div key={a.id} className="flex items-center gap-4 px-5 py-4">
              <div className={`flex-shrink-0 w-2 h-2 rounded-full ${a.severity === 'critical' ? 'bg-red-400' : a.severity === 'warning' ? 'bg-amber-400' : 'bg-blue-400'}`}></div>
              <div className="flex-1">
                <div className="text-white text-sm">{a.rule}</div>
                <div className="text-gray-500 text-xs mt-0.5">{a.client} · {a.time}</div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${a.resolved ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                {a.resolved ? 'Resolved' : 'Active'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
