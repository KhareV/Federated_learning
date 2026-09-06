import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Lock, User, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { authApi } from '../../services/api';

export default function LoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [role, setRole] = useState<'admin' | 'researcher' | 'user'>('admin');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const DEMO_CREDS = [
    { role: 'admin' as const, username: 'admin', password: 'admin123', description: 'Full access' },
    { role: 'researcher' as const, username: 'researcher', password: 'research123', description: 'AI, FL, experiments' },
    { role: 'user' as const, username: 'user', password: 'user123', description: 'Personal health data' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await authApi.login(username, password);
      const { access_token, user } = res.data;
      login(user, access_token);
      navigate('/overview');
    } catch (err: any) {
      // For demo: allow offline mock login
      const mockUser = { id: '1', username, email: `${username}@research.local`, role };
      login(mockUser, 'mock-token-' + username);
      navigate('/overview');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center">
              <Activity size={32} className="text-white" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">QAPFL Health Monitor</h1>
          <p className="text-gray-400 text-sm mt-1">Non-Invasive Wearable Health Monitoring with Federated Learning</p>
        </div>

        {/* Form */}
        <div className="bg-gray-900 rounded-2xl p-8 border border-gray-800">
          <h2 className="text-white font-semibold mb-6">Sign in to Research Platform</h2>
          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg flex items-center gap-2 text-red-400 text-sm">
              <AlertCircle size={16}/> {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-gray-400 text-sm mb-1 block">Username</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-3 text-gray-500"/>
                <input value={username} onChange={e => setUsername(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Username"/>
              </div>
            </div>
            <div>
              <label className="text-gray-400 text-sm mb-1 block">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-3 text-gray-500"/>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Password"/>
              </div>
            </div>
            <div>
              <label className="text-gray-400 text-sm mb-1 block">Role (demo)</label>
              <select value={role} onChange={e => {
                const r = e.target.value as 'admin' | 'researcher' | 'user';
                setRole(r);
                const cred = DEMO_CREDS.find(c => c.role === r);
                if (cred) { setUsername(cred.username); setPassword(cred.password); }
              }} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500">
                <option value="admin">Administrator</option>
                <option value="researcher">Researcher</option>
                <option value="user">User</option>
              </select>
            </div>
            <button type="submit" disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-6 pt-6 border-t border-gray-800">
            <p className="text-gray-500 text-xs mb-3">Demo credentials:</p>
            <div className="space-y-2">
              {DEMO_CREDS.map(c => (
                <button key={c.role} onClick={() => { setRole(c.role); setUsername(c.username); setPassword(c.password); }}
                  className="w-full text-left p-2 rounded bg-gray-800 hover:bg-gray-750 border border-gray-700 text-xs">
                  <span className="text-blue-400 font-mono">{c.username}</span>
                  <span className="text-gray-500"> / </span>
                  <span className="text-gray-300 font-mono">{c.password}</span>
                  <span className="text-gray-500 ml-2">— {c.description}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-gray-600 text-xs mt-4">
          ⚠️ Research Prototype — Not for clinical use
        </p>
      </div>
    </div>
  );
}