// Auth
export interface User { id: string; username: string; email: string; role: 'admin' | 'researcher' | 'user'; }
export interface AuthState { user: User | null; token: string | null; isAuthenticated: boolean; }

// Monitoring
export interface SensorReading { timestamp: string; hr: number; spo2: number; ecg_sqi: number; ppg_sqi: number; overall_sqi: number; anomaly_score: number; confidence: number; anomaly_class: string; }
export interface MonitoringSession { id: string; session_id: string; user_id: string; device_id: string; start_time: string; end_time?: string; total_samples: number; anomaly_count: number; avg_hr: number; avg_spo2: number; avg_ecg_sqi: number; avg_ppg_sqi: number; }

// Device
export interface Device { id: string; device_id: string; name: string; ble_address: string; firmware_version: string; battery_level: number; sampling_rate: number; status: 'connected' | 'disconnected' | 'pairing'; last_seen: string; signal_status: string; }

// Signal Quality
export interface SignalQuality { ecg_sqi: number; ppg_sqi: number; overall_sqi: number; quality_label: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR'; reasons: string[]; }

// Anomaly
export interface AnomalyEvent { id: string; timestamp: string; anomaly_score: number; confidence: number; classification: 'NORMAL' | 'POSSIBLE_ANOMALY' | 'LOW_CONFIDENCE_EVENT' | 'HIGH_CONFIDENCE_ANOMALY'; affected_signals: string[]; signal_quality: number; explanation: Record<string, number>; }

// Baseline
export interface PersonalBaseline { hr_mean: number; hr_std: number; hr_min: number; hr_max: number; spo2_mean: number; spo2_std: number; hrv_sdnn_mean: number; hrv_rmssd_mean: number; samples_used: number; last_updated: string; version: number; }

// FL
export interface FLClient { client_id: string; name: string; description: string; dataset_size: number; usable_samples: number; ecg_sqi: number; ppg_sqi: number; local_accuracy: number; local_f1: number; local_loss: number; uncertainty: number; battery_level: number; last_participation: string; aggregation_weight: number; total_rounds: number; }
export interface FLRound { id: string; round_number: number; strategy: string; participating_clients: string[]; avg_local_loss: number; global_loss: number; global_accuracy: number; global_f1: number; avg_sqi: number; communication_cost_bytes: number; training_time_seconds: number; aggregation_weights: Record<string, number>; started_at: string; completed_at: string; }
export interface FLStatus { current_round: number; total_rounds: number; active_clients: number; completed_clients: number; global_model_version: string; global_accuracy: number; avg_local_accuracy: number; aggregation_status: string; is_training: boolean; communication_volume_mb: number; }

// Experiment
export interface Experiment { id: string; experiment_id: string; name: string; type: string; config: Record<string, any>; seed: number; model: string; status: 'pending' | 'running' | 'completed' | 'failed'; created_at: string; completed_at?: string; }
export interface ExperimentResult { metric_name: string; metric_value: number; round_number?: number; noise_level?: number; client_id?: string; }

// Model
export interface ModelVersion { id: string; version_str: string; model_type: string; architecture: Record<string, any>; performance_metrics: Record<string, number>; training_rounds: number; created_at: string; is_current: boolean; }

// Alert
export interface AlertRule { id: string; name: string; type: string; severity: 'low' | 'medium' | 'high' | 'critical'; threshold: number; enabled: boolean; }
export interface Notification { id: string; severity: string; source: string; title: string; description: string; is_read: boolean; created_at: string; }

// System
export interface SystemHealth { backend: string; database: string; ml_service: string; fl_server: string; websocket: string; latency_ms: number; uptime_seconds: number; }
