"""
Synthetic Physiological Signal Generator
CLEARLY LABELLED: All data is synthetic and NOT from real patients.
This is a research prototype. Data is NOT suitable for clinical use.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

class AnomalyType(Enum):
    NONE = "none"
    TACHYCARDIA = "tachycardia"          # Elevated sustained HR
    BRADYCARDIA = "bradycardia"           # Low HR
    IRREGULAR_RR = "irregular_rr"        # Irregular beat intervals  
    SUDDEN_HR_SPIKE = "sudden_hr_spike"  # Brief HR spike

@dataclass
class SyntheticECGParams:
    heart_rate: float = 70.0        # BPM
    amplitude: float = 1.0          # mV scale
    noise_level: float = 0.05       # 0.0-1.0
    baseline_wander_amplitude: float = 0.05  # Low-freq drift
    motion_artifact: bool = False   # High-freq burst noise
    fs: int = 250                   # Hz
    duration: float = 10.0          # seconds
    anomaly_type: AnomalyType = AnomalyType.NONE
    seed: Optional[int] = None

@dataclass  
class SyntheticPPGParams:
    heart_rate: float = 70.0
    perfusion: float = 1.0          # Signal amplitude scale
    noise_level: float = 0.05
    motion_artifact: bool = False
    fs: int = 50
    duration: float = 10.0
    seed: Optional[int] = None

class PhysiologicalGenerator:
    """
    Generates synthetic physiological signals for research purposes.
    
    DISCLAIMER: All generated signals are synthetic mathematical approximations
    for software testing and algorithm development only. They do not represent
    real patient data and must not be used for any clinical purposes.
    """
    IS_SYNTHETIC = True
    DATA_LABEL = "SYNTHETIC DEMO DATA - NOT REAL PATIENT DATA"
    
    def generate_ecg(self, params: SyntheticECGParams) -> np.ndarray:
        rng = np.random.RandomState(params.seed)
        n_samples = int(params.duration * params.fs)
        t = np.linspace(0, params.duration, n_samples)
        ecg = np.zeros(n_samples)
        
        waves = {
            'P':  {'offset': -0.20, 'width': 0.09, 'amp':  0.15},
            'Q':  {'offset': -0.06, 'width': 0.025, 'amp': -0.10},
            'R':  {'offset':  0.00, 'width': 0.04,  'amp':  1.00},
            'S':  {'offset':  0.07, 'width': 0.025, 'amp': -0.25},
            'T':  {'offset':  0.20, 'width': 0.11,  'amp':  0.35},
        }
        
        beat_times = self._generate_beat_times(params, rng)
        
        for beat_t in beat_times:
            if beat_t >= params.duration:
                break
            for wave_name, wave_params in waves.items():
                center = beat_t + wave_params['offset']
                width = wave_params['width']
                amp = wave_params['amp'] * params.amplitude
                ecg += amp * np.exp(-((t - center) ** 2) / (2 * width ** 2))
        
        if params.baseline_wander_amplitude > 0:
            wander_freq = 0.15 + rng.uniform(-0.05, 0.05)
            wander = params.baseline_wander_amplitude * np.sin(2 * np.pi * wander_freq * t)
            ecg += wander
        
        if params.noise_level > 0:
            noise = rng.normal(0, params.noise_level * 0.2, n_samples)
            ecg += noise
        
        if params.motion_artifact:
            burst_start = int(rng.uniform(0.2, 0.6) * n_samples)
            burst_len = int(rng.uniform(0.5, 2.0) * params.fs)
            burst_end = min(burst_start + burst_len, n_samples)
            ecg[burst_start:burst_end] += rng.normal(0, params.noise_level * 1.5, burst_end - burst_start)
        
        return ecg.astype(np.float32)
    
    def _generate_beat_times(self, params: SyntheticECGParams, rng: np.random.RandomState) -> np.ndarray:
        base_rr = 60.0 / params.heart_rate  # seconds
        hrv_std = 0.02
        beat_times = []
        t = 0.5
        
        while t < params.duration + 0.5:
            beat_times.append(t)
            
            if params.anomaly_type == AnomalyType.TACHYCARDIA:
                rr = 60.0 / max(params.heart_rate * 1.5, 150) + rng.normal(0, hrv_std * 0.5)
            elif params.anomaly_type == AnomalyType.BRADYCARDIA:
                rr = 60.0 / max(params.heart_rate * 0.6, 35) + rng.normal(0, hrv_std)
            elif params.anomaly_type == AnomalyType.IRREGULAR_RR:
                rr = base_rr + rng.normal(0, hrv_std * 5)
                rr = max(0.3, min(rr, 1.5))
            elif params.anomaly_type == AnomalyType.SUDDEN_HR_SPIKE:
                progress = t / params.duration
                if 0.3 < progress < 0.7:
                    rr = 60.0 / (params.heart_rate * 1.8) + rng.normal(0, hrv_std)
                else:
                    rr = base_rr + rng.normal(0, hrv_std)
            else:
                rr = base_rr + rng.normal(0, hrv_std)
                rr = max(0.4, rr)
            
            t += rr
        
        return np.array(beat_times)
    
    def generate_ppg(self, params: SyntheticPPGParams) -> np.ndarray:
        rng = np.random.RandomState(params.seed)
        n_samples = int(params.duration * params.fs)
        t = np.linspace(0, params.duration, n_samples)
        ppg = np.zeros(n_samples)
        
        rr_base = 60.0 / params.heart_rate
        beat_times = []
        bt = 0.3
        while bt < params.duration + 0.3:
            beat_times.append(bt)
            bt += rr_base + rng.normal(0, 0.015)
        
        for beat_t in beat_times:
            if beat_t >= params.duration:
                break
            systolic_center = beat_t + 0.12
            systolic_width = 0.08
            amp = params.perfusion * (1.0 + rng.uniform(-0.05, 0.05))
            ppg += amp * np.exp(-((t - systolic_center) ** 2) / (2 * systolic_width ** 2))
            
            dicrotic_center = beat_t + 0.35
            dicrotic_width = 0.06
            ppg += 0.3 * amp * np.exp(-((t - dicrotic_center) ** 2) / (2 * dicrotic_width ** 2))
        
        ppg += 0.5
        
        if params.noise_level > 0:
            ppg += rng.normal(0, params.noise_level * 0.1, n_samples)
        
        if params.motion_artifact:
            burst_start = int(rng.uniform(0.2, 0.5) * n_samples)
            burst_len = int(rng.uniform(1.0, 3.0) * params.fs)
            burst_end = min(burst_start + burst_len, n_samples)
            artifact = np.linspace(0, rng.uniform(-0.3, 0.3), burst_end - burst_start)
            artifact += rng.normal(0, params.noise_level * 0.5, burst_end - burst_start)
            ppg[burst_start:burst_end] += artifact
        
        return ppg.astype(np.float32)
    
    def generate_hr_timeseries(self, duration_minutes: float = 60, baseline_hr: float = 70, hr_std: float = 5, anomaly_type: Optional[AnomalyType] = None, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        rng = np.random.RandomState(seed)
        n_points = int(duration_minutes * 60)
        t = np.arange(n_points, dtype=float)
        
        slow_variation = hr_std * 0.5 * np.sin(2 * np.pi * t / (20 * 60))
        ou_hr = np.zeros(n_points)
        theta = 0.1
        sigma = hr_std * 0.3
        for i in range(1, n_points):
            ou_hr[i] = ou_hr[i-1] - theta * ou_hr[i-1] + sigma * rng.normal()
        
        hr = baseline_hr + slow_variation + ou_hr
        
        if anomaly_type == AnomalyType.TACHYCARDIA:
            anomaly_start = int(n_points * 0.4)
            anomaly_end = int(n_points * 0.6)
            hr[anomaly_start:anomaly_end] += 35 + rng.normal(0, 3, anomaly_end - anomaly_start)
        elif anomaly_type == AnomalyType.SUDDEN_HR_SPIKE:
            spike_center = int(n_points * 0.5)
            spike_width = int(2 * 60)
            spike_t = np.arange(n_points)
            hr += 40 * np.exp(-((spike_t - spike_center) ** 2) / (2 * spike_width ** 2))
        
        hr = np.clip(hr, 35, 200)
        return t, hr.astype(np.float32)
    
    def generate_spo2_timeseries(self, duration_minutes: float = 60, baseline_spo2: float = 98.0, spo2_std: float = 0.5, inject_desaturation: bool = False, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        rng = np.random.RandomState(seed)
        n_points = int(duration_minutes * 60)
        t = np.arange(n_points, dtype=float)
        
        noise = rng.normal(0, spo2_std * 0.3, n_points)
        spo2 = baseline_spo2 + noise
        
        n_dips = rng.poisson(2)
        for _ in range(n_dips):
            dip_center = rng.randint(int(n_points * 0.1), int(n_points * 0.9))
            dip_width = int(30 + rng.uniform(0, 60))
            dip_depth = rng.uniform(0.5, 1.5)
            dip_t = np.arange(n_points)
            spo2 -= dip_depth * np.exp(-((dip_t - dip_center) ** 2) / (2 * dip_width ** 2))
        
        if inject_desaturation:
            des_start = int(n_points * 0.45)
            des_end = int(n_points * 0.55)
            des_depth = rng.uniform(3, 6)
            spo2[des_start:des_end] -= des_depth
        
        spo2 = np.clip(spo2, 85, 100)
        return t, spo2.astype(np.float32)
    
    def inject_noise(self, signal: np.ndarray, noise_level_pct: float, seed: Optional[int] = None) -> np.ndarray:
        rng = np.random.RandomState(seed)
        signal_rms = np.sqrt(np.mean(signal ** 2))
        noise_std = (noise_level_pct / 100.0) * signal_rms
        return signal + rng.normal(0, noise_std, len(signal)).astype(np.float32)
    
    def inject_missing_data(self, signal: np.ndarray, missing_rate: float, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        rng = np.random.RandomState(seed)
        missing_mask = rng.random(len(signal)) < missing_rate
        signal_with_missing = signal.copy()
        signal_with_missing[missing_mask] = 0.0
        return signal_with_missing, missing_mask
