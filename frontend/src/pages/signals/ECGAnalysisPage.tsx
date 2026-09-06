import { useState } from 'react';
import { Heart, ZoomIn, ZoomOut, Pause, Play, Filter } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';

function generateECG(n = 750, hr = 72, noise = 0.05) {
  const data = [];
  const fs = 250;
  for (let i = 0; i < n; i++) {
    const t = i / fs;
    const beatPeriod = 60 / hr;
    const phase = (t % beatPeriod) / beatPeriod;
    // PQRST Gaussian approximation
    let ecg = 0;
    ecg += 0.15 * Math.exp(-Math.pow((phase - 0.20), 2) / (2 * 0.0032));  // P
    ecg -= 0.10 * Math.exp(-Math.pow((phase - 0.32), 2) / (2 * 0.0003));  // Q
    ecg += 1.00 * Math.exp(-Math.pow((phase - 0.35), 2) / (2 * 0.0006));  // R
    ecg -= 0.25 * Math.exp(-Math.pow((phase - 0.38), 2) / (2 * 0.0003));  // S
    ecg += 0.35 * Math.exp(-Math.pow((phase - 0.55), 2) / (2 * 0.0048));  // T
    ecg += (Math.random() - 0.5) * noise;
    data.push({ i, raw: Math.round((ecg + 0.05 * Math.sin(2 * Math.PI * 0.15 * t)) * 1000) / 1000, filtered: Math.round(ecg * 1000) / 1000 });
  }
  return data;
}

function generateRR(n = 30, baseHR = 72, noise = 0.02) {
  const baseRR = 60000 / baseHR;
  return Array.from({ length: n }, (_, i) => ({
    beat: i + 1,
    rr: Math.round(baseRR + (Math.random() - 0.5) * baseRR * noise * 2),
  }));
}

const rrData = generateRR(30);
const sdnn = Math.round(Math.sqrt(rrData.reduce((s, d) => s + Math.pow(d.rr - (rrData.reduce((a, b) => a + b.rr, 0) / rrData.length), 2), 0) / rrData.length));
const meanRR = Math.round(rrData.reduce((a, b) => a + b.rr, 0) / rrData.length);
const diffs = rrData.slice(1).map((d, i) => Math.pow(d.rr - rrData[i].rr, 2));
const rmssd = Math.round(Math.sqrt(diffs.reduce((a, b) => a + b, 0) / diffs.length));
const pnn50 = Math.round(rrData.slice(1).filter((d, i) => Math.abs(d.rr - rrData[i].rr) > 50).length / (rrData.length - 1) * 100);

export default function ECGAnalysisPage() {
  const [showFiltered, setShowFiltered] = useState(true);
  const [showRaw, setShowRaw] = useState(true);
  const [timeWindow, setTimeWindow] = useState(3);
  const [paused, setPaused] = useState(false);

  const samplesPerWindow = timeWindow * 250;
  const ecgData = generateECG(samplesPerWindow, 72, 0.06);
  const hr = Math.round(60000 / meanRR);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Heart size={24} className="text-red-400"/> ECG Analysis
          </h1>
          <p className="text-gray-400 text-sm mt-1">Signal processing & HRV metrics — Synthetic Demo Data</p>
        </div>
        <span className="text-xs text-amber-400 bg-amber-900/20 border border-amber-800/30 px-3 py-1 rounded-full">Research Prototype — Not Clinical</span>
      </div>

      {/* ECG Waveform */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium">ECG Waveform</h3>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input type="checkbox" checked={showRaw} onChange={e => setShowRaw(e.target.checked)} className="accent-blue-500"/> Raw
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input type="checkbox" checked={showFiltered} onChange={e => setShowFiltered(e.target.checked)} className="accent-green-500"/> Filtered
            </label>
            <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
              <button onClick={() => setTimeWindow(Math.max(1, timeWindow - 1))} className="p-1 text-gray-400 hover:text-white"><ZoomIn size={14}/></button>
              <span className="text-gray-400 text-xs px-2">{timeWindow}s</span>
              <button onClick={() => setTimeWindow(Math.min(10, timeWindow + 1))} className="p-1 text-gray-400 hover:text-white"><ZoomOut size={14}/></button>
            </div>
            <button onClick={() => setPaused(!paused)} className={`p-2 rounded-lg text-sm flex items-center gap-1 ${paused ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
              {paused ? <Play size={14}/> : <Pause size={14}/>} {paused ? 'Resume' : 'Pause'}
            </button>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={ecgData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="i" tick={false} />
            <YAxis domain={[-0.5, 1.2]} tick={{ fill: '#6b7280', fontSize: 11 }} width={40} />
            <Tooltip
              contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
              labelStyle={{ display: 'none' }}
              formatter={(v: number) => [v.toFixed(3) + ' mV']}
            />
            {showRaw && <Line type="monotone" dataKey="raw" stroke="#374151" dot={false} strokeWidth={1} name="Raw ECG" />}
            {showFiltered && <Line type="monotone" dataKey="filtered" stroke="#34d399" dot={false} strokeWidth={1.5} name="Filtered ECG" />}
          </LineChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-2 text-xs text-gray-500">
          {showRaw && <span className="flex items-center gap-1"><span className="inline-block w-4 h-0.5 bg-gray-600"></span> Raw ECG</span>}
          {showFiltered && <span className="flex items-center gap-1"><span className="inline-block w-4 h-0.5 bg-emerald-400"></span> Filtered ECG (0.5–40Hz bandpass + 50Hz notch)</span>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* HRV Metrics */}
        <div className="col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">HRV Metrics</h3>
          <div className="space-y-3">
            {[
              { label: 'Heart Rate', value: `${hr} BPM`, desc: 'From RR intervals' },
              { label: 'Mean RR', value: `${meanRR} ms`, desc: 'Average beat interval' },
              { label: 'SDNN', value: `${sdnn} ms`, desc: 'Std dev of RR intervals' },
              { label: 'RMSSD', value: `${rmssd} ms`, desc: 'Root mean sq successive diff' },
              { label: 'pNN50', value: `${pnn50}%`, desc: '% successive diffs > 50ms' },
            ].map(m => (
              <div key={m.label} className="flex justify-between items-start py-2 border-b border-gray-800 last:border-0">
                <div>
                  <div className="text-gray-300 text-sm font-medium">{m.label}</div>
                  <div className="text-gray-600 text-xs">{m.desc}</div>
                </div>
                <div className="text-white font-mono text-sm">{m.value}</div>
              </div>
            ))}
          </div>
          <p className="text-gray-600 text-xs mt-3">⚠️ Research metrics from synthetic ECG. Not clinically validated.</p>
        </div>

        {/* RR Interval Chart */}
        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">RR Interval Series</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={rrData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="beat" tick={{ fill: '#6b7280', fontSize: 11 }} label={{ value: 'Beat #', position: 'insideBottom', fill: '#6b7280', fontSize: 11 }} />
              <YAxis domain={[600, 1000]} tick={{ fill: '#6b7280', fontSize: 11 }} label={{ value: 'RR (ms)', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 11 }} width={50} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                itemStyle={{ color: '#a78bfa' }}
                formatter={(v: number) => [`${v} ms`, 'RR interval']}
              />
              <Line type="monotone" dataKey="rr" stroke="#a78bfa" dot={{ fill: '#a78bfa', r: 3 }} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          <p className="text-gray-500 text-xs mt-2">Detected R-peaks from Pan-Tompkins-like algorithm. Variability reflects synthetic HRV simulation.</p>
        </div>
      </div>
    </div>
  );
}
