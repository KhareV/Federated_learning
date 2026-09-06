import { Wifi, Battery, RefreshCw, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const DEVICES = [
  { id: 'ESP32_001', name: 'Wristband Alpha', ble: 'A4:B2:C1:D3:E5:F7', fw: '1.4.2', battery: 0.92, rate: 250, packets: 24.8, loss: 0.2, status: 'connected', last_seen: '< 1s ago' },
  { id: 'ESP32_002', name: 'Wristband Beta', ble: 'B5:C3:D2:E4:F6:A8', fw: '1.4.2', battery: 0.78, rate: 250, packets: 24.6, loss: 0.8, status: 'connected', last_seen: '< 1s ago' },
  { id: 'ESP32_003', name: 'Wristband Gamma', ble: 'C6:D4:E3:F5:A7:B9', fw: '1.3.8', battery: 0.55, rate: 250, packets: 23.1, loss: 4.2, status: 'poor_signal', last_seen: '2s ago' },
  { id: 'ESP32_005', name: 'Wristband Epsilon', ble: 'E8:F6:A5:B7:C9:D1', fw: '1.4.0', battery: 0.23, rate: 250, packets: 24.4, loss: 1.1, status: 'low_battery', last_seen: '< 1s ago' },
  { id: 'ESP32_006', name: 'Wristband Zeta', ble: 'F9:A7:B6:C8:D0:E2', fw: '1.4.2', battery: 0.67, rate: 250, packets: 24.9, loss: 0.3, status: 'connected', last_seen: '< 1s ago' },
  { id: 'ESP32_004', name: 'Wristband Delta', ble: 'D7:E5:F4:A6:B8:C0', fw: '1.4.1', battery: 0.88, rate: 250, packets: 0, loss: 0, status: 'disconnected', last_seen: '3m ago' },
];

const STATUS = {
  connected: { label: 'Connected', color: 'text-green-400', dot: 'bg-green-400', icon: <CheckCircle size={14} className="text-green-400"/> },
  poor_signal: { label: 'Poor Signal', color: 'text-amber-400', dot: 'bg-amber-400', icon: <AlertCircle size={14} className="text-amber-400"/> },
  low_battery: { label: 'Low Battery', color: 'text-red-400', dot: 'bg-red-400', icon: <AlertCircle size={14} className="text-red-400"/> },
  disconnected: { label: 'Disconnected', color: 'text-gray-500', dot: 'bg-gray-500', icon: <XCircle size={14} className="text-gray-500"/> },
};

export default function DevicesPage() {
  const connected = DEVICES.filter(d => d.status !== 'disconnected').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Device Management</h1>
          <p className="text-gray-400 text-sm mt-1">ESP32 + MAX30102 + AD8232 BLE devices</p>
        </div>
        <div className="flex gap-3">
          <div className="flex items-center gap-2 bg-green-900/20 border border-green-800/30 px-3 py-2 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            <span className="text-green-400 text-sm">{connected} / {DEVICES.length} Online</span>
          </div>
          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">
            <Wifi size={14}/> Pair New Device
          </button>
        </div>
      </div>

      <div className="grid gap-4">
        {DEVICES.map(d => {
          const s = STATUS[d.status as keyof typeof STATUS];
          return (
            <div key={d.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gray-800 flex items-center justify-center">
                    <Wifi size={22} className={s.color}/>
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-white font-semibold">{d.name}</span>
                      <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${s.dot} ${d.status !== 'disconnected' ? 'animate-pulse' : ''}`}></div>
                        <span className={`text-sm ${s.color}`}>{s.label}</span>
                      </div>
                    </div>
                    <div className="text-gray-500 text-xs mt-1">
                      {d.id} · BLE: {d.ble} · FW: {d.fw}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  {d.status === 'disconnected' ? (
                    <button className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs">Connect</button>
                  ) : (
                    <button className="px-3 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs">Disconnect</button>
                  )}
                  <button className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs flex items-center gap-1">
                    <RefreshCw size={12}/> Calibrate
                  </button>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-5 gap-3">
                <div className="bg-gray-800 rounded-lg p-2.5">
                  <div className="text-gray-500 text-xs flex items-center gap-1"><Battery size={11}/> Battery</div>
                  <div className={`font-medium text-sm mt-1 ${d.battery > 0.3 ? 'text-white' : 'text-red-400'}`}>{Math.round(d.battery * 100)}%</div>
                  <div className="h-1 bg-gray-700 rounded-full mt-1.5">
                    <div className={`h-full rounded-full ${d.battery > 0.5 ? 'bg-green-500' : d.battery > 0.2 ? 'bg-amber-500' : 'bg-red-500'}`}
                      style={{ width: `${d.battery * 100}%` }}></div>
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-2.5">
                  <div className="text-gray-500 text-xs">Sampling Rate</div>
                  <div className="text-white font-medium text-sm mt-1">{d.rate} Hz</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-2.5">
                  <div className="text-gray-500 text-xs">Packet Rate</div>
                  <div className={`font-medium text-sm mt-1 ${d.status !== 'disconnected' ? 'text-white' : 'text-gray-600'}`}>{d.packets > 0 ? `${d.packets}/s` : '—'}</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-2.5">
                  <div className="text-gray-500 text-xs">Packet Loss</div>
                  <div className={`font-medium text-sm mt-1 ${d.loss < 1 ? 'text-green-400' : d.loss < 3 ? 'text-amber-400' : 'text-red-400'}`}>{d.packets > 0 ? `${d.loss}%` : '—'}</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-2.5">
                  <div className="text-gray-500 text-xs">Last Seen</div>
                  <div className="text-white text-sm mt-1">{d.last_seen}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
