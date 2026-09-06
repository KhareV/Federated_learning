import numpy as np
from backend.ml.signal_quality.ecg_sqi import ECGSQICalculator

def test_clean_ecg_high_sqi():
    calc = ECGSQICalculator()
    # Mock clean signal
    raw_ecg = np.sin(np.linspace(0, 10, 1000))
    filtered_ecg = raw_ecg
    r_peaks = np.array([100, 300, 500, 700, 900])
    rr_intervals = np.diff(r_peaks)
    res = calc.compute_ecg_sqi(raw_ecg, filtered_ecg, r_peaks, rr_intervals, None)
    assert res.overall_sqi > 60
    
def test_noisy_ecg_low_sqi():
    calc = ECGSQICalculator()
    # Mock noisy signal
    raw_ecg = np.random.randn(1000) * 10
    filtered_ecg = np.zeros(1000) # Terribly filtered, essentially all noise
    r_peaks = np.array([10, 500, 510, 900])
    rr_intervals = np.diff(r_peaks)
    res = calc.compute_ecg_sqi(raw_ecg, filtered_ecg, r_peaks, rr_intervals, None)
    assert res.overall_sqi < 40