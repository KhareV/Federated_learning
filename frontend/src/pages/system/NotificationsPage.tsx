import { useState } from 'react';
import { Bell, CheckCheck, Trash2, AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';

const NOTIFS = [
  { id: '1', type: 'warning', title: 'Signal Quality Warning', desc: 'ECG SQI dropped to 62% for client_03 (Carol). High motion artifact detected.', time: '14:22', source: 'Signal QA', read: false },
  { id: '2', type: 'info', title: 'FL Round 7 Completed', desc: 'QAPFL training round 7 completed. Global F1 improved: 0.872 → 0.891 (+2.2%).', time: '14:15', source: 'FL Server', read: false },
  { id: '3', type: 'alert', title: 'Low-Confidence Anomaly Event', desc: 'Low-confidence anomaly detected for client_01 (Alice). Score: 0.63, SQI: 52%. Not reported as high-confidence due to poor signal quality.', time: '14:10', source: 'Anomaly Detector', read: false },
  { id: '4', type: 'info', title: 'Baseline Updated', desc: 'Personal baseline for client_01 (Alice) updated using 1,240 new samples.', time: '14:05', source: 'Baseline Learner', read: true },
  { id: '5', type: 'success', title: 'Device Connected', desc: 'ESP32_001 (Wristband Alpha) connected via BLE. Battery: 92%.', time: '13:58', source: 'Device Manager', read: true },
  { id: '6', type: 'info', title: 'Low Battery Warning', desc: 'ESP32_005 (Eve) battery level at 23%. Recommend charging.', time: '13:45', source: 'Device Manager', read: true },
  { id: '7', type: 'alert', title: 'High Anomaly Score', desc: 'High-confidence anomaly detected for client_06 (Frank). Score: 0.82, SQI: 87%. Recommended review.', time: '13:42', source: 'Anomaly Detector', read: true },
  { id: '8', type: 'success', title: 'FL Round 6 Completed', desc: 'QAPFL training round 6 completed. Global F1: 0.872.', time: '13:35', source: 'FL Server', read: true },
];

const typeConfig: Record<string, { icon: React.ReactNode; bg: string; border: string; dot: string }> = {
  warning: { icon: <AlertTriangle size={16}/>, bg: 'text-amber-400', border: 'border-amber-800/30', dot: 'bg-amber-400' },
  info: { icon: <Info size={16}/>, bg: 'text-blue-400', border: 'border-blue-800/30', dot: 'bg-blue-400' },
  alert: { icon: <AlertTriangle size={16}/>, bg: 'text-red-400', border: 'border-red-800/30', dot: 'bg-red-400' },
  success: { icon: <CheckCircle size={16}/>, bg: 'text-green-400', border: 'border-green-800/30', dot: 'bg-green-400' },
};

export default function NotificationsPage() {
  const [notifs, setNotifs] = useState(NOTIFS);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const markAllRead = () => setNotifs(n => n.map(x => ({ ...x, read: true })));
  const markRead = (id: string) => setNotifs(n => n.map(x => x.id === id ? { ...x, read: true } : x));
  const dismiss = (id: string) => setNotifs(n => n.filter(x => x.id !== id));

  const shown = notifs.filter(n => filter === 'all' || !n.read);
  const unread = notifs.filter(n => !n.read).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Bell size={24} className="text-blue-400"/> Notifications</h1>
          <p className="text-gray-400 text-sm mt-1">{unread} unread · {notifs.length} total</p>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
            {(['all', 'unread'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded text-sm capitalize transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}>{f}</button>
            ))}
          </div>
          <button onClick={markAllRead} className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-sm">
            <CheckCheck size={14}/> Mark all read
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {shown.map(n => {
          const cfg = typeConfig[n.type];
          return (
            <div key={n.id} className={`bg-gray-900 border rounded-xl p-4 transition-opacity ${!n.read ? cfg.border : 'border-gray-800'} ${n.read ? 'opacity-60' : ''}`}>
              <div className="flex items-start gap-4">
                <div className={`flex-shrink-0 mt-0.5 ${cfg.bg}`}>{cfg.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-white font-medium text-sm">{n.title}</span>
                      {!n.read && <span className="ml-2 inline-block w-2 h-2 rounded-full bg-blue-400 align-middle"></span>}
                    </div>
                    <span className="text-gray-500 text-xs flex-shrink-0">{n.time}</span>
                  </div>
                  <p className="text-gray-400 text-sm mt-1">{n.desc}</p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-gray-600 text-xs">Source: {n.source}</span>
                    <div className="flex gap-2">
                      {!n.read && <button onClick={() => markRead(n.id)} className="text-blue-400 text-xs hover:underline">Mark read</button>}
                      <button onClick={() => dismiss(n.id)} className="text-gray-600 text-xs hover:text-red-400 flex items-center gap-1"><Trash2 size={10}/> Dismiss</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        {shown.length === 0 && (
          <div className="text-center py-12 text-gray-600">
            <Bell size={32} className="mx-auto mb-3 opacity-30"/>
            <p>No {filter === 'unread' ? 'unread' : ''} notifications</p>
          </div>
        )}
      </div>
    </div>
  );
}
