import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useAuthStore } from './stores/authStore';
import { useSettingsStore } from './stores/settingsStore';

// Layout
import AppLayout from './components/layout/AppLayout';
// Auth
import LoginPage from './pages/auth/LoginPage';
// Main
import OverviewPage from './pages/overview/OverviewPage';
import LiveMonitoringPage from './pages/monitoring/LiveMonitoringPage';
import PatientProfilesPage from './pages/patients/PatientProfilesPage';
import HealthTrendsPage from './pages/trends/HealthTrendsPage';
import AlertsPage from './pages/alerts/AlertsPage';
import ReportsPage from './pages/reports/ReportsPage';
// Signals
import ECGAnalysisPage from './pages/signals/ECGAnalysisPage';
import PPGAnalysisPage from './pages/signals/PPGAnalysisPage';
import SPO2AnalysisPage from './pages/signals/SPO2AnalysisPage';
import SignalQualityPage from './pages/signals/SignalQualityPage';
// AI
import AIInsightsPage from './pages/ai/AIInsightsPage';
import AnomalyDetectionPage from './pages/ai/AnomalyDetectionPage';
import PersonalizedBaselinePage from './pages/ai/PersonalizedBaselinePage';
import ExplainabilityPage from './pages/ai/ExplainabilityPage';
import ConfidencePage from './pages/ai/ConfidencePage';
// FL
import FLOverviewPage from './pages/fl/FLOverviewPage';
import FLClientsPage from './pages/fl/FLClientsPage';
import FLRoundsPage from './pages/fl/FLRoundsPage';
import AggregationPage from './pages/fl/AggregationPage';
import GlobalModelPage from './pages/fl/GlobalModelPage';
import PersonalModelsPage from './pages/fl/PersonalModelsPage';
import PrivacyPage from './pages/fl/PrivacyPage';
// Research
import ModelComparisonPage from './pages/research/ModelComparisonPage';
import ExperimentsPage from './pages/research/ExperimentsPage';
import RobustnessPage from './pages/research/RobustnessPage';
import AblationPage from './pages/research/AblationPage';
import PerformanceAnalyticsPage from './pages/research/PerformanceAnalyticsPage';
import ResearchResultsPage from './pages/research/ResearchResultsPage';
// System
import DevicesPage from './pages/system/DevicesPage';
import DataManagementPage from './pages/system/DataManagementPage';
import NotificationsPage from './pages/system/NotificationsPage';
import SettingsPage from './pages/system/SettingsPage';
import SystemHealthPage from './pages/system/SystemHealthPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});

export default function App() {
  const { theme } = useSettingsStore();

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/overview" replace />} />

            {/* MAIN */}
            <Route path="overview" element={<OverviewPage />} />
            <Route path="monitoring" element={<LiveMonitoringPage />} />
            <Route path="patients" element={<PatientProfilesPage />} />
            <Route path="trends" element={<HealthTrendsPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="reports" element={<ReportsPage />} />

            {/* SIGNALS */}
            <Route path="signals/ecg" element={<ECGAnalysisPage />} />
            <Route path="signals/ppg" element={<PPGAnalysisPage />} />
            <Route path="signals/spo2" element={<SPO2AnalysisPage />} />
            <Route path="signals/quality" element={<SignalQualityPage />} />

            {/* AI */}
            <Route path="ai/insights" element={<AIInsightsPage />} />
            <Route path="ai/anomaly" element={<AnomalyDetectionPage />} />
            <Route path="ai/baseline" element={<PersonalizedBaselinePage />} />
            <Route path="ai/explainability" element={<ExplainabilityPage />} />
            <Route path="ai/confidence" element={<ConfidencePage />} />

            {/* FEDERATED LEARNING */}
            <Route path="fl/overview" element={<FLOverviewPage />} />
            <Route path="fl/clients" element={<FLClientsPage />} />
            <Route path="fl/rounds" element={<FLRoundsPage />} />
            <Route path="fl/aggregation" element={<AggregationPage />} />
            <Route path="fl/global-model" element={<GlobalModelPage />} />
            <Route path="fl/personal-models" element={<PersonalModelsPage />} />
            <Route path="fl/privacy" element={<PrivacyPage />} />

            {/* RESEARCH */}
            <Route path="research/comparison" element={<ModelComparisonPage />} />
            <Route path="research/experiments" element={<ExperimentsPage />} />
            <Route path="research/robustness" element={<RobustnessPage />} />
            <Route path="research/ablation" element={<AblationPage />} />
            <Route path="research/analytics" element={<PerformanceAnalyticsPage />} />
            <Route path="research/results" element={<ResearchResultsPage />} />

            {/* SYSTEM */}
            <Route path="system/devices" element={<DevicesPage />} />
            <Route path="system/data" element={<DataManagementPage />} />
            <Route path="system/notifications" element={<NotificationsPage />} />
            <Route path="system/settings" element={<SettingsPage />} />
            <Route path="system/health" element={<SystemHealthPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}