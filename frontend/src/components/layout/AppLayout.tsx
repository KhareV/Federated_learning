import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { 
  Activity, Monitor, Users, TrendingUp, Bell, FileText,
  Heart, Wind, Droplets, Signal, Brain, AlertTriangle, 
  User, Eye, BarChart2, Network, Server, Database, Shield,
  GitMerge, Cpu, TestTube, Layers, BarChart, Settings,
  Wifi, ChevronLeft, ChevronRight, Sun, Moon, LogOut,
  HardDrive, Sliders, BookOpen, ChevronDown
} from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';
import { useAuthStore } from '../../stores/authStore';
import { useNotificationStore } from '../../stores/notificationStore';

type NavItem = { label: string; path: string; icon: React.ReactNode };
type NavSection = { title: string; items: NavItem[] };

const navigation: NavSection[] = [
  {
    title: 'MAIN',
    items: [
      { label: 'Overview', path: '/overview', icon: <Activity size={16} /> },
      { label: 'Live Monitoring', path: '/monitoring', icon: <Monitor size={16} /> },
      { label: 'Patient Profiles', path: '/patients', icon: <Users size={16} /> },
      { label: 'Health Trends', path: '/trends', icon: <TrendingUp size={16} /> },
      { label: 'Alerts', path: '/alerts', icon: <Bell size={16} /> },
      { label: 'Reports', path: '/reports', icon: <FileText size={16} /> },
    ]
  },
  {
    title: 'SIGNALS',
    items: [
      { label: 'ECG Analysis', path: '/signals/ecg', icon: <Heart size={16} /> },
      { label: 'PPG Analysis', path: '/signals/ppg', icon: <Wind size={16} /> },
      { label: 'SpO₂ Analysis', path: '/signals/spo2', icon: <Droplets size={16} /> },
      { label: 'Signal Quality', path: '/signals/quality', icon: <Signal size={16} /> },
    ]
  },
  {
    title: 'AI',
    items: [
      { label: 'AI Insights', path: '/ai/insights', icon: <Brain size={16} /> },
      { label: 'Anomaly Detection', path: '/ai/anomaly', icon: <AlertTriangle size={16} /> },
      { label: 'Personalized Baseline', path: '/ai/baseline', icon: <User size={16} /> },
      { label: 'Explainable AI', path: '/ai/explainability', icon: <Eye size={16} /> },
      { label: 'Prediction Confidence', path: '/ai/confidence', icon: <BarChart2 size={16} /> },
    ]
  },
  {
    title: 'FEDERATED LEARNING',
    items: [
      { label: 'FL Overview', path: '/fl/overview', icon: <Network size={16} /> },
      { label: 'Clients', path: '/fl/clients', icon: <Server size={16} /> },
      { label: 'Training Rounds', path: '/fl/rounds', icon: <GitMerge size={16} /> },
      { label: 'Aggregation', path: '/fl/aggregation', icon: <Layers size={16} /> },
      { label: 'Global Model', path: '/fl/global-model', icon: <Cpu size={16} /> },
      { label: 'Personal Models', path: '/fl/personal-models', icon: <Database size={16} /> },
      { label: 'Privacy & Security', path: '/fl/privacy', icon: <Shield size={16} /> },
    ]
  },
  {
    title: 'RESEARCH',
    items: [
      { label: 'Model Comparison', path: '/research/comparison', icon: <BarChart size={16} /> },
      { label: 'Experiments', path: '/research/experiments', icon: <TestTube size={16} /> },
      { label: 'Robustness Testing', path: '/research/robustness', icon: <Sliders size={16} /> },
      { label: 'Ablation Study', path: '/research/ablation', icon: <Layers size={16} /> },
      { label: 'Performance Analytics', path: '/research/analytics', icon: <BarChart2 size={16} /> },
      { label: 'Research Results', path: '/research/results', icon: <BookOpen size={16} /> },
    ]
  },
  {
    title: 'SYSTEM',
    items: [
      { label: 'Devices', path: '/system/devices', icon: <Wifi size={16} /> },
      { label: 'Data Management', path: '/system/data', icon: <HardDrive size={16} /> },
      { label: 'Notifications', path: '/system/notifications', icon: <Bell size={16} /> },
      { label: 'Settings', path: '/system/settings', icon: <Settings size={16} /> },
      { label: 'System Health', path: '/system/health', icon: <Activity size={16} /> },
    ]
  },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { theme, toggleTheme } = useSettingsStore();
  const { user, logout } = useAuthStore();
  const { unreadCount } = useNotificationStore();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className={`min-h-screen flex ${theme === 'dark' ? 'dark bg-gray-950' : 'bg-gray-50'}`}>
      {/* Sidebar */}
      <aside className={`${collapsed ? 'w-16' : 'w-64'} transition-all duration-300 bg-gray-900 border-r border-gray-800 flex flex-col flex-shrink-0 h-screen sticky top-0`}>
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-gray-800">
          {!collapsed && (
            <div>
              <div className="text-white font-bold text-sm">QAPFL Monitor</div>
              <div className="text-gray-400 text-xs">Health Research Platform</div>
            </div>
          )}
          <button onClick={() => setCollapsed(!collapsed)} className="ml-auto text-gray-400 hover:text-white p-1">
            {collapsed ? <ChevronRight size={16}/> : <ChevronLeft size={16}/>}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 space-y-1">
          {navigation.map((section) => (
            <div key={section.title} className="mb-2">
              {!collapsed && (
                <div className="px-4 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  {section.title}
                </div>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2 text-sm transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    } ${collapsed ? 'justify-center' : ''}`
                  }
                  title={collapsed ? item.label : undefined}
                >
                  {item.icon}
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-gray-800 p-4">
          {!collapsed && user && (
            <div className="mb-3">
              <div className="text-white text-sm font-medium">{user.username}</div>
              <div className="text-gray-400 text-xs capitalize">{user.role}</div>
            </div>
          )}
          <div className="flex gap-2">
            <button onClick={toggleTheme} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded" title="Toggle theme">
              {theme === 'dark' ? <Sun size={14}/> : <Moon size={14}/>}
            </button>
            <button onClick={handleLogout} className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded" title="Logout">
              <LogOut size={14}/>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Topbar */}
        <header className="h-16 border-b border-gray-800 bg-gray-900 flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="text-white font-medium">Health Monitoring & FL Research Platform</div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
              <span className="text-gray-400 text-sm">System Online</span>
            </div>
            <NavLink to="/system/notifications" className="relative text-gray-400 hover:text-white p-2">
              <Bell size={18}/>
              {unreadCount > 0 && (
                <span className="absolute -top-0 -right-0 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </NavLink>
            <div className="text-gray-400 text-sm">{user?.username || 'Guest'}</div>
          </div>
        </header>

        {/* Disclaimer */}
        <div className="bg-amber-900/20 border-b border-amber-800/30 px-6 py-2 text-amber-400 text-xs">
          ⚠️ RESEARCH PROTOTYPE — Not intended for medical diagnosis, treatment, or emergency decision-making. All outputs are research results only.
        </div>

        {/* Page content */}
        <div className="flex-1 overflow-auto p-6 bg-gray-950 text-gray-100">
          <Outlet />
        </div>
      </main>
    </div>
  );
}