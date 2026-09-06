import { Wind } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

function generatePPG(n = 250, hr = 72, noise = 0.05) {
  const data = [];
  const fs = 50;
  for (let i = 0; i < n; i++) {
    const t = i / fs;
    const beatPeriod = 60 / hr;
    const phase = (t % beatPeriod) / beatPeriod;
    let ppg = 0.5;
    ppg += 0.9 * Math.exp(-Math.pow((phase - 0.20), 2) / (2 * 0.005));  // Systolic
    ppg += 0.25 * Math.exp(-Math.pow((phase - 0.55), 2) / (2 * 0.003)); // Dicrotic
    ppg += (Math.random() - 0.5) * noise;
    data.push({ i, raw: Math.round(ppg * 1000) / 1000, filtered: Math.round((ppg - (Math.random() - 0.5) * noise * 0.5) * 1000) / 1000 });
  }
  return data;
}

const ppgData = generatePPG(250);
const pulseIntervals = Array.from({ length: 20 }, (_, i) => ({ beat: i + 1, pi: 820 + Math.round((Math.random() - 0.5) * 40) }));

const qualityComponents = [
  { name: 'Baseline Stability', score: 82, color: '#34d399' },
  { name: 'Amplitude Stability', score: 75, color: '#60a5fa' },
  { name: 'Peak Regularity', score: 78, color: '#a78bfa' },
  { name: 'Noise Estimate', score: 71, color: '#fbbf24' },
];

export default function PPGAnalysisPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Wind size={24} className="text-blue-400"/> PPG Analysis
          </h1>
          <p className="text-gray-400 text-sm mt-1">Photoplethysmography signal analysis — Synthetic Demo Data</p>
        </div>
      </div>

      {/* PPG Waveform */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">PPG Waveform (5 seconds)</h3>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={ppgData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="i" tick={false} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={[0.3, 1.7]} />
            <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
              formatter={(v: number) => [v.toFixed(3) + ' a.u.']} labelStyle={{ display: 'none' }} />
            <Line type="monotone" dataKey="raw" stroke="#374151" dot={false} strokeWidth={1} name="Raw" />
            <Line type="monotone" dataKey="filtered" stroke="#60a5fa" dot={false} strokeWidth={2} name="Filtered" />
          </LineChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-2 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="inline-block w-4 h-0.5 bg-gray-600"></span> Raw PPG</span>
          <span className="flex items-center gap-1"><span className="inline-block w-4 h-0.5 bg-blue-400"></span> Filtered (0.5–5Hz bandpass)</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Pulse Intervals */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Pulse Interval Series</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={pulseIntervals}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="beat" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis domain={[750, 900]} tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(v: number) => [`${v} ms`, 'Pulse Interval']} />
              <Line type="monotone" dataKey="pi" stroke="#60a5fa" dot={{ fill: '#60a5fa', r: 3 }} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div className="bg-gray-800 rounded-lg p-2">
              <div className="text-gray-400 text-xs">Mean PI</div>
              <div className="text-white font-medium">{Math.round(pulseIntervals.reduce((a, b) => a + b.pi, 0) / pulseIntervals.length)} ms</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-2">
              <div className="text-gray-400 text-xs">PI Std Dev</div>
              <div className="text-white font-medium">±{Math.round(Math.sqrt(pulseIntervals.map(d => Math.pow(d.pi - 820, 2)).reduce((a, b) => a + b, 0) / pulseIntervals.length))} ms</div>
            </div>
          </div>
        </div>

        {/* Quality Breakdown */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">PPG Quality Breakdown</h3>
          <div className="space-y-4">
            {qualityComponents.map(qc => (
              <div key={qc.name}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-gray-400 text-sm">{qc.name}</span>
                  <span className="text-white text-sm font-medium">{qc.score}%</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${qc.score}%`, backgroundColor: qc.color }}></div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-gray-800">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">Motion Artifact</span>
              <span className="text-green-400 text-sm font-medium">Not Detected</span>
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-gray-400 text-sm">Overall PPG SQI</span>
              <span className="text-white text-sm font-bold">76 / 100 — GOOD</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
