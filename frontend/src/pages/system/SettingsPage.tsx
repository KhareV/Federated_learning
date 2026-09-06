import { useState } from 'react';
import { Settings, Save, RotateCcw, AlertTriangle } from 'lucide-react';

type Section = 'signal' | 'anomaly' | 'fl' | 'qapfl' | 'simulator' | 'display';

function SliderField({ label, desc, value, min, max, step, onChange, unit }: {
  label: string; desc: string; value: number; min: number; max: number; step: number;
  onChange: (v: number) => void; unit?: string;
}) {
  return (
    <div className="py-3 border-b border-gray-800 last:border-0">
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="text-white text-sm font-medium">{label}</div>
          <div className="text-gray-500 text-xs">{desc}</div>
        </div>
        <div className="text-blue-400 text-sm font-mono font-bold">{value}{unit}</div>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 bg-gray-700 rounded-full appearance-none cursor-pointer accent-blue-500"/>
      <div className="flex justify-between text-xs text-gray-600 mt-1">
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [section, setSection] = useState<Section>('anomaly');
  const [anomalyThreshold, setAnomalyThreshold] = useState(0.50);
  const [sqiThreshold, setSqiThreshold] = useState(60);
  const [confMin, setConfMin] = useState(0.40);
  const [flRounds, setFlRounds] = useState(10);
  const [localEpochs, setLocalEpochs] = useState(5);
  const [lr, setLr] = useState(0.001);
  const [minClients, setMinClients] = useState(3);
  const [alpha, setAlpha] = useState(0.35);
  const [beta, setBeta] = useState(0.25);
  const [gamma, setGamma] = useState(0.30);
  const [delta, setDelta] = useState(0.10);
  const [saved, setSaved] = useState(false);

  const qapflSum = alpha + beta + gamma + delta;
  const qapflValid = Math.abs(qapflSum - 1.0) < 0.01;

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const sections: { id: Section; label: string }[] = [
    { id: 'anomaly', label: 'Anomaly Detection' },
    { id: 'fl', label: 'Federated Learning' },
    { id: 'qapfl', label: 'QAPFL Weights' },
    { id: 'signal', label: 'Signal Processing' },
    { id: 'simulator', label: 'Simulator' },
    { id: 'display', label: 'Display' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Settings size={24} className="text-gray-400"/> Settings</h1>
          <p className="text-gray-400 text-sm mt-1">Platform configuration — all parameters affect live computation</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-sm">
            <RotateCcw size={14}/> Reset Defaults
          </button>
          <button onClick={handleSave} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">
            <Save size={14}/> {saved ? 'Saved!' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Nav */}
        <div className="col-span-1">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-2 space-y-1">
            {sections.map(s => (
              <button key={s.id} onClick={() => setSection(s.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  section === s.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}>{s.label}</button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="col-span-3 bg-gray-900 border border-gray-800 rounded-xl p-6">
          {section === 'anomaly' && (
            <div>
              <h2 className="text-white font-semibold mb-4">Anomaly Detection Thresholds</h2>
              <SliderField label="Anomaly Score Threshold" desc="Score above this → classified as anomaly (0=very sensitive, 1=very strict)" value={anomalyThreshold} min={0.1} max={0.9} step={0.01} onChange={setAnomalyThreshold} />
              <SliderField label="Signal Quality Threshold (SQI)" desc="Minimum SQI for high-confidence classification. Below this → LOW_CONFIDENCE_EVENT" value={sqiThreshold} min={20} max={90} step={5} onChange={setSqiThreshold} unit="%" />
              <SliderField label="Minimum Confidence SQI" desc="SQI below this → very low confidence. Anomaly confidence multiplied by SQI/100" value={confMin} min={0.1} max={0.8} step={0.05} onChange={setConfMin} />
            </div>
          )}
          {section === 'fl' && (
            <div>
              <h2 className="text-white font-semibold mb-4">Federated Learning Configuration</h2>
              <SliderField label="FL Rounds" desc="Number of training rounds per experiment" value={flRounds} min={1} max={50} step={1} onChange={setFlRounds} />
              <SliderField label="Local Epochs" desc="Local training epochs per client per round" value={localEpochs} min={1} max={20} step={1} onChange={setLocalEpochs} />
              <SliderField label="Learning Rate" desc="Local optimizer learning rate" value={lr} min={0.0001} max={0.01} step={0.0001} onChange={setLr} />
              <SliderField label="Minimum Clients" desc="Minimum clients required to start a training round" value={minClients} min={2} max={8} step={1} onChange={setMinClients} />
            </div>
          )}
          {section === 'qapfl' && (
            <div>
              <h2 className="text-white font-semibold mb-1">QAPFL Aggregation Weights</h2>
              <p className="text-gray-400 text-xs mb-4">These control how the quality score is computed: quality_score = α·SQI + β·data_quality + γ·local_F1 + δ·(1-uncertainty)</p>
              {!qapflValid && (
                <div className="flex items-center gap-2 text-amber-400 text-xs mb-4 p-3 bg-amber-900/20 border border-amber-800/30 rounded-lg">
                  <AlertTriangle size={14}/> Weights sum to {qapflSum.toFixed(2)} — they should sum to 1.00. The server will auto-normalize.
                </div>
              )}
              <div className="p-3 bg-blue-900/10 border border-blue-800/20 rounded-lg mb-4 font-mono text-xs text-blue-300">
                quality_score = {alpha.toFixed(2)}·SQI + {beta.toFixed(2)}·data_quality + {gamma.toFixed(2)}·local_F1 + {delta.toFixed(2)}·(1-uncertainty)
                <br/>Sum = {qapflSum.toFixed(2)} {qapflValid ? '✓' : '⚠'}
              </div>
              <SliderField label="α — Signal Quality Weight" desc="Contribution of ECG/PPG SQI to quality score" value={alpha} min={0} max={1} step={0.05} onChange={setAlpha} />
              <SliderField label="β — Data Quality Weight" desc="Contribution of usable sample fraction" value={beta} min={0} max={1} step={0.05} onChange={setBeta} />
              <SliderField label="γ — Model Performance Weight" desc="Contribution of local F1 score" value={gamma} min={0} max={1} step={0.05} onChange={setGamma} />
              <SliderField label="δ — Uncertainty Penalty Weight" desc="Penalty for high MC Dropout uncertainty" value={delta} min={0} max={1} step={0.05} onChange={setDelta} />
            </div>
          )}
          {section === 'signal' && (
            <div>
              <h2 className="text-white font-semibold mb-4">Signal Processing Parameters</h2>
              <div className="space-y-3 text-sm">
                {[
                  { label: 'ECG Sampling Rate', value: '250 Hz', note: 'Fixed by hardware' },
                  { label: 'PPG Sampling Rate', value: '50 Hz', note: 'Fixed by hardware' },
                  { label: 'ECG Bandpass Low', value: '0.5 Hz', note: 'Removes baseline wander' },
                  { label: 'ECG Bandpass High', value: '40 Hz', note: 'Removes high-freq noise' },
                  { label: 'Notch Filter Frequency', value: '50 Hz', note: 'Removes powerline interference' },
                  { label: 'PPG Bandpass Low', value: '0.5 Hz', note: 'Removes DC and drift' },
                  { label: 'PPG Bandpass High', value: '5.0 Hz', note: 'Removes motion artifacts' },
                ].map(p => (
                  <div key={p.label} className="flex justify-between items-center py-2 border-b border-gray-800">
                    <div>
                      <div className="text-gray-300">{p.label}</div>
                      <div className="text-gray-600 text-xs">{p.note}</div>
                    </div>
                    <div className="text-white font-mono">{p.value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {section === 'simulator' && (
            <div>
              <h2 className="text-white font-semibold mb-4">Simulator Configuration</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {[
                  { label: 'Number of Clients', value: '8' },
                  { label: 'Sampling Interval', value: '0.04s' },
                  { label: 'Stream Duration', value: 'Continuous' },
                  { label: 'Random Seed', value: '42 (reproducible)' },
                ].map(s => (
                  <div key={s.label} className="bg-gray-800 rounded-lg p-3">
                    <div className="text-gray-500 text-xs">{s.label}</div>
                    <div className="text-white mt-1">{s.value}</div>
                  </div>
                ))}
              </div>
              <p className="text-gray-500 text-xs mt-4">Simulator parameters are configured in <code className="text-blue-400">.env</code> file. Advanced parameters require restart.</p>
            </div>
          )}
          {section === 'display' && (
            <div>
              <h2 className="text-white font-semibold mb-4">Display Settings</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-gray-800">
                  <div>
                    <div className="text-white text-sm">Theme</div>
                    <div className="text-gray-500 text-xs">Dark/Light mode</div>
                  </div>
                  <div className="flex gap-2">
                    <button className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs">Dark</button>
                    <button className="px-3 py-1.5 rounded-lg bg-gray-700 text-gray-300 text-xs">Light</button>
                  </div>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <div className="text-white text-sm">ECG Waveform Window</div>
                    <div className="text-gray-500 text-xs">Duration shown in live view</div>
                  </div>
                  <span className="text-white text-sm">5 seconds</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
