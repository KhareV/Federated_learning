import { Database, Trash2, Download, HardDrive } from 'lucide-react';

const DATASETS = [
  { name: 'Monitoring Sessions', records: 48, size: '2.1 MB', table: 'monitoring_sessions' },
  { name: 'Sensor Readings', records: 124_500, size: '18.4 MB', table: 'sensor_readings' },
  { name: 'ECG Segments', records: 8_200, size: '96 MB', table: 'ecg_segments' },
  { name: 'PPG Segments', records: 8_200, size: '12 MB', table: 'ppg_segments' },
  { name: 'Anomaly Events', records: 156, size: '0.2 MB', table: 'anomaly_events' },
  { name: 'FL Rounds', records: 70, size: '4.8 MB', table: 'fl_rounds' },
  { name: 'Client Metadata', records: 8, size: '0.01 MB', table: 'clients' },
  { name: 'Experiment Results', records: 10, size: '1.2 MB', table: 'experiments' },
];

export default function DataManagementPage() {
  const totalMB = DATASETS.reduce((s, d) => s + parseFloat(d.size), 0);
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><HardDrive size={24} className="text-gray-400"/> Data Management</h1>
          <p className="text-gray-400 text-sm mt-1">SQLite database tables — research data lifecycle</p>
        </div>
        <button className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-sm">
          <Download size={14}/> Export All
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Storage', value: `${totalMB.toFixed(0)} MB`, icon: <HardDrive size={16}/>, color: 'text-blue-400' },
          { label: 'Tables', value: DATASETS.length.toString(), icon: <Database size={16}/>, color: 'text-purple-400' },
          { label: 'Total Records', value: DATASETS.reduce((s, d) => s + d.records, 0).toLocaleString(), icon: <Database size={16}/>, color: 'text-green-400' },
        ].map(s => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">{s.icon} {s.label}</div>
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-5 px-4 py-3 border-b border-gray-800 text-xs text-gray-500 uppercase font-medium">
          <div className="col-span-2">Table</div><div>Records</div><div>Size</div><div>Actions</div>
        </div>
        {DATASETS.map(d => (
          <div key={d.name} className="grid grid-cols-5 px-4 py-3.5 border-b border-gray-800/50 hover:bg-gray-800/20 text-sm">
            <div className="col-span-2">
              <div className="text-white">{d.name}</div>
              <div className="text-gray-600 text-xs font-mono">{d.table}</div>
            </div>
            <div className="text-gray-300">{d.records.toLocaleString()}</div>
            <div className="text-gray-300">{d.size}</div>
            <div className="flex gap-2">
              <button className="text-xs text-blue-400 hover:underline flex items-center gap-1"><Download size={10}/> Export</button>
              <button className="text-xs text-red-400 hover:underline flex items-center gap-1"><Trash2 size={10}/> Clear</button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amber-900/20 border border-amber-800/30 rounded-xl p-4 text-amber-300 text-sm">
        ⚠️ All data is synthetically generated for research purposes. No real patient data is stored. Use "Export" to download data for offline analysis.
      </div>
    </div>
  );
}
