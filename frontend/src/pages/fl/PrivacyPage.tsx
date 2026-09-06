import { Shield, Lock, Server, CheckCircle, XCircle, ArrowRight } from 'lucide-react';

function FlowStep({ label, icon, color }: { label: string; icon: React.ReactNode; color: string }) {
  return (
    <div className={`flex flex-col items-center gap-2 p-3 rounded-xl border ${color} min-w-[120px]`}>
      {icon}
      <span className="text-xs text-center font-medium text-white">{label}</span>
    </div>
  );
}

function Arrow({ red = false }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1">
      <ArrowRight size={16} className={red ? 'text-red-500' : 'text-gray-500'}/>
      {red && <span className="text-red-500 text-xs">Raw data!</span>}
    </div>
  );
}

export default function PrivacyPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield size={24} className="text-green-400"/> Privacy & Security
        </h1>
        <p className="text-gray-400 text-sm mt-1">Federated learning data architecture — privacy analysis</p>
      </div>

      <div className="bg-amber-900/20 border border-amber-800/30 rounded-xl p-4 text-amber-300 text-sm">
        ⚠️ <strong>Important:</strong> Federated Learning reduces — but does NOT eliminate — privacy risks. Raw biometric data stays local, but model updates can still leak information. This system is a research prototype and has not undergone formal privacy verification.
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Centralized approach */}
        <div className="bg-gray-900 border border-red-800/40 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
            <XCircle size={16} className="text-red-400"/> Centralized Approach (Traditional)
          </h3>
          <p className="text-gray-400 text-xs mb-4">Raw biometric data sent to cloud server</p>
          <div className="flex flex-wrap items-center gap-2">
            <FlowStep label="Raw ECG" icon={<span className="text-xl">💓</span>} color="border-gray-700"/>
            <FlowStep label="Raw PPG" icon={<span className="text-xl">🩸</span>} color="border-gray-700"/>
            <FlowStep label="Raw SpO₂" icon={<span className="text-xl">🫁</span>} color="border-gray-700"/>
            <Arrow red />
            <FlowStep label="Cloud Server" icon={<Server size={20} className="text-red-400"/>} color="border-red-800"/>
            <Arrow />
            <FlowStep label="ML Model" icon={<span className="text-xl">🤖</span>} color="border-gray-700"/>
          </div>
          <div className="mt-4 space-y-2 text-xs">
            <div className="flex items-center gap-2 text-red-400"><XCircle size={12}/> Raw biometric data transmitted over network</div>
            <div className="flex items-center gap-2 text-red-400"><XCircle size={12}/> Centralized storage of sensitive health data</div>
            <div className="flex items-center gap-2 text-red-400"><XCircle size={12}/> Single point of failure and data breach risk</div>
            <div className="flex items-center gap-2 text-red-400"><XCircle size={12}/> Requires user consent for central data collection</div>
          </div>
        </div>

        {/* FL approach */}
        <div className="bg-gray-900 border border-green-800/40 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
            <CheckCircle size={16} className="text-green-400"/> Federated Learning Approach (This System)
          </h3>
          <p className="text-gray-400 text-xs mb-4">Only model updates leave the device</p>
          <div className="flex flex-wrap items-center gap-2">
            <FlowStep label="Local Device" icon={<span className="text-xl">📱</span>} color="border-gray-700"/>
            <Arrow />
            <FlowStep label="Local Training" icon={<span className="text-xl">🏋️</span>} color="border-blue-800"/>
            <Arrow />
            <FlowStep label="Model Updates Only" icon={<Lock size={18} className="text-green-400"/>} color="border-green-800"/>
            <Arrow />
            <FlowStep label="FL Server" icon={<Server size={18} className="text-blue-400"/>} color="border-blue-800"/>
          </div>
          <div className="mt-4 space-y-2 text-xs">
            <div className="flex items-center gap-2 text-green-400"><CheckCircle size={12}/> Raw biometric data never leaves local device</div>
            <div className="flex items-center gap-2 text-green-400"><CheckCircle size={12}/> Only gradient/model updates transmitted</div>
            <div className="flex items-center gap-2 text-amber-400"><Shield size={12}/> Model updates can still leak information (gradient inversion)</div>
            <div className="flex items-center gap-2 text-amber-400"><Shield size={12}/> Differential privacy available as optional module</div>
          </div>
        </div>
      </div>

      {/* Status indicators */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-medium mb-4">Security Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Raw Data Location', value: 'Local Device Only', status: 'good' },
            { label: 'Transport Encryption', value: 'Simulated (Dev)', status: 'warning' },
            { label: 'Authentication', value: 'JWT (Mock)', status: 'warning' },
            { label: 'Differential Privacy', value: 'Optional Module', status: 'info' },
            { label: 'Model Updates', value: 'Transmitted', status: 'info' },
            { label: 'Aggregation Audit', value: 'Full Audit Trail', status: 'good' },
            { label: 'Data Retention', value: 'Metadata Only', status: 'good' },
            { label: 'Clinical Validation', value: 'NOT Validated', status: 'bad' },
          ].map(s => (
            <div key={s.label} className="bg-gray-800 rounded-lg p-3">
              <div className="text-gray-500 text-xs">{s.label}</div>
              <div className={`text-sm font-medium mt-1 ${
                s.status === 'good' ? 'text-green-400' : s.status === 'bad' ? 'text-red-400' :
                s.status === 'warning' ? 'text-amber-400' : 'text-blue-400'
              }`}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
