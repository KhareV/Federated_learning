import { FileText, Download, Clock, CheckCircle } from 'lucide-react';

const REPORTS = [
  { id: 'R001', name: 'QAPFL vs FedAvg Comparison Report', type: 'research', size: '1.2 MB', status: 'ready', created: '2026-09-05 09:00', pages: 14 },
  { id: 'R002', name: 'Noise Robustness Experiment Report', type: 'research', size: '0.8 MB', status: 'ready', created: '2026-09-05 08:30', pages: 8 },
  { id: 'R003', name: 'Ablation Study Report', type: 'research', size: '0.6 MB', status: 'ready', created: '2026-09-04 17:00', pages: 6 },
  { id: 'R004', name: 'Client Signal Quality Report', type: 'monitoring', size: '0.4 MB', status: 'ready', created: '2026-09-04 12:00', pages: 4 },
  { id: 'R005', name: 'Personalization Benefit Analysis', type: 'research', size: '0.9 MB', status: 'generating', created: '...', pages: null },
];

const TYPE = { research: 'bg-blue-900/30 text-blue-400', monitoring: 'bg-green-900/30 text-green-400' };

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><FileText size={24} className="text-indigo-400"/> Reports</h1>
          <p className="text-gray-400 text-sm mt-1">Research and monitoring reports — export-ready</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">
          <FileText size={14}/> Generate Report
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Reports', value: REPORTS.length },
          { label: 'Ready for Download', value: REPORTS.filter(r => r.status === 'ready').length },
          { label: 'Total Pages', value: REPORTS.reduce((s, r) => s + (r.pages || 0), 0) },
        ].map(s => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="text-gray-400 text-sm">{s.label}</div>
            <div className="text-white text-3xl font-bold mt-1">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="divide-y divide-gray-800">
          {REPORTS.map(r => (
            <div key={r.id} className="flex items-center gap-4 px-5 py-4 hover:bg-gray-800/30 transition-colors">
              <FileText size={20} className="text-gray-500 flex-shrink-0"/>
              <div className="flex-1 min-w-0">
                <div className="text-white text-sm font-medium">{r.name}</div>
                <div className="flex items-center gap-3 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE[r.type as keyof typeof TYPE]}`}>{r.type}</span>
                  <span className="text-gray-500 text-xs flex items-center gap-1"><Clock size={10}/> {r.created}</span>
                  {r.pages && <span className="text-gray-500 text-xs">{r.pages} pages</span>}
                  <span className="text-gray-500 text-xs">{r.size}</span>
                </div>
              </div>
              {r.status === 'ready' ? (
                <button className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-1.5 rounded-lg text-xs">
                  <Download size={12}/> Download PDF
                </button>
              ) : (
                <div className="flex items-center gap-2 text-amber-400 text-xs">
                  <div className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
                  Generating...
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
