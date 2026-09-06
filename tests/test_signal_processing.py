import numpy as np
from backend.ml.signal_processing.ecg_processor import ECGProcessor

def test_ecg_bandpass_filter():
    proc = ECGProcessor()
    sig = np.random.randn(1000)
    out = proc.bandpass_filter(sig)
    assert len(out) == len(sig)

def test_r_peak_detection():
    proc = ECGProcessor()
    sig = np.sin(np.linspace(0, 10, 1000))
    peaks = proc.detect_r_peaks(sig)
    assert len(peaks) > 0