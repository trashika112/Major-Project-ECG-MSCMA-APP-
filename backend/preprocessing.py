"""
Turns an uploaded ECG file into a (1, N_LEADS, SEQ_LEN) float32 tensor ready
for MSCMA-Net, using the same per-lead mean/std the model was trained with
(loaded from the checkpoint at startup — see predict.py).
"""
import os
import numpy as np
from scipy.signal import resample as scipy_resample, find_peaks

from config import N_LEADS, SEQ_LEN


class ECGFormatError(ValueError):
    pass


class ECGValidityError(ValueError):
    """Raised when a file has the right shape/format but is not a plausible
    ECG signal (flat-line, corrupted, random noise, wrong data pasted in,
    etc.) — as opposed to ECGFormatError, which is for shape/parsing issues."""
    pass


def validate_ecg_signal(raw: np.ndarray, sampling_rate: int) -> None:
    """Sanity-checks a (T, leads) raw ECG signal BEFORE it reaches the model.

    Format checks (shape, lead count) are handled separately in
    _fix_orientation. This function checks whether the *content* looks like a
    real ECG at all, so the app doesn't confidently diagnose garbage input.
    Raises ECGValidityError with a human-readable reason if a check fails.
    """
    t, leads = raw.shape

    if not np.isfinite(raw).all():
        raise ECGValidityError(
            "The uploaded signal contains missing or invalid values (NaN/Inf). "
            "This does not look like a valid ECG export."
        )

    duration_s = t / float(sampling_rate)
    if duration_s < 2.0:
        raise ECGValidityError(
            f"The recording is only {duration_s:.1f}s long. At least 2 seconds "
            f"of signal is needed to check for a valid heartbeat rhythm."
        )

    lead_std = raw.std(axis=0)
    overall_scale = float(np.median(lead_std)) + 1e-8
    flat_leads = int(np.sum(lead_std < max(1e-6, overall_scale * 0.02)))
    if flat_leads >= leads - 1:
        raise ECGValidityError(
            "The uploaded signal is flat (little to no variation) across "
            "nearly all leads. This looks like an empty, placeholder, or "
            "corrupted file rather than a real ECG."
        )

    # Autocorrelation-based periodicity check: real ECG has a strongly
    # repeating waveform (P-QRS-T every beat), so the signal correlates well
    # with a time-shifted copy of itself at the beat-to-beat lag. Random
    # noise or corrupted data does not, no matter how peaks are counted —
    # this catches cases plain peak-detection can be fooled by.
    #
    # Important: check EVERY lead, not just the highest-amplitude one — a
    # lead's amplitude doesn't predict how clean/periodic its rhythm looks
    # (e.g. precordial leads like V2/V3 can have complex morphology and a
    # lower autocorrelation score than a quieter limb lead, even on a
    # perfectly normal ECG). Take the best score found across all leads.
    lag_min = max(1, int(sampling_rate * 60.0 / 250))  # fastest plausible beat (250bpm)
    lag_max = min(t - 1, int(sampling_rate * 60.0 / 25))  # slowest plausible beat (25bpm)
    if lag_max <= lag_min:
        raise ECGValidityError(
            "The recording is too short relative to its sampling rate to "
            "check for a valid heartbeat rhythm."
        )

    best_overall_score = -1.0
    best_overall_lag = None

    for lead_idx in range(leads):
        ref_lead = raw[:, lead_idx] - raw[:, lead_idx].mean()
        zero_lag = float(np.dot(ref_lead, ref_lead))
        if zero_lag <= 1e-8:
            continue  # this particular lead is flat; other leads are checked below

        full_autocorr = np.correlate(ref_lead, ref_lead, mode="full")
        normalized_autocorr = full_autocorr[len(full_autocorr) // 2:] / zero_lag
        window = normalized_autocorr[lag_min:lag_max + 1]

        local_peak_idx, _ = find_peaks(window)
        if len(local_peak_idx) == 0:
            continue

        lead_best_offset = int(local_peak_idx[np.argmax(window[local_peak_idx])])
        lead_best_score = float(window[lead_best_offset])

        if lead_best_score > best_overall_score:
            best_overall_score = lead_best_score
            best_overall_lag = lag_min + lead_best_offset

    if best_overall_lag is None:
        raise ECGValidityError(
            "No repeating heartbeat pattern could be detected in any lead "
            "(the signal's self-similarity doesn't peak at any particular beat "
            "interval). This does not look like a valid ECG recording."
        )

    # A real, clearly periodic beat pattern typically re-correlates at
    # >= ~0.2 with itself one beat later in its best lead; noise/random
    # data falls well below this even in its best-scoring lead.
    if best_overall_score < 0.2:
        raise ECGValidityError(
            "No repeating heartbeat pattern could be detected in this signal "
            f"(best periodicity score across all leads: {best_overall_score:.2f}, "
            f"need >= 0.20). This does not look like a valid ECG recording."
        )

    implied_bpm = 60.0 * sampling_rate / best_overall_lag
    if not (25 <= implied_bpm <= 260):
        raise ECGValidityError(
            f"The detected beat pattern implies an unrealistic heart rate "
            f"(~{implied_bpm:.0f} bpm). This does not look like a valid ECG recording."
        )


def _fix_orientation(sig: np.ndarray) -> np.ndarray:
    """Return (T, n_leads). Accepts either (T, leads) or (leads, T)."""
    if sig.ndim != 2:
        raise ECGFormatError(f"Expected a 2D ECG array, got shape {sig.shape}.")
    if sig.shape[1] == N_LEADS:
        return sig
    if sig.shape[0] == N_LEADS:
        return sig.T
    raise ECGFormatError(
        f"Could not find a {N_LEADS}-lead axis in an array of shape {sig.shape}. "
        f"Expected one dimension to equal {N_LEADS}."
    )


def _resample_to_seq_len(sig: np.ndarray, sampling_rate: int) -> np.ndarray:
    """sig: (T, leads). Resamples in time so the model always sees SEQ_LEN
    timesteps (SEQ_LEN was fixed at training time, e.g. 1000 samples @ 100Hz = 10s)."""
    t, leads = sig.shape
    target_t = SEQ_LEN
    if t == target_t:
        return sig
    # Resample from whatever length/rate we got to the fixed model input length.
    resampled = scipy_resample(sig, target_t, axis=0)
    return resampled.astype(np.float32)


def load_csv(path: str) -> np.ndarray:
    # Try with header first, fall back to no header.
    try:
        arr = np.genfromtxt(path, delimiter=",", skip_header=1)
        if arr.ndim != 2 or np.isnan(arr).all():
            raise ValueError
    except Exception:
        arr = np.genfromtxt(path, delimiter=",")
    if arr.ndim == 1:
        raise ECGFormatError("CSV parsed as a single column/row — check the delimiter and shape.")
    return arr.astype(np.float32)


def load_npy(path: str) -> np.ndarray:
    arr = np.load(path)
    return arr.astype(np.float32)


def load_wfdb(base_path_no_ext: str) -> np.ndarray:
    import wfdb
    record = wfdb.rdrecord(base_path_no_ext)
    return record.p_signal.astype(np.float32)  # (T, leads)


# Common variable names MATLAB ECG exports use for the actual signal matrix.
# Checked in this order; first match wins. Covers PhysioNet-style exports
# (which commonly use 'val'), plus a few other common conventions.
_MAT_SIGNAL_KEYS = ("val", "signal", "ecg", "data", "X", "x")


def load_mat(path: str) -> np.ndarray:
    """Loads a .mat file and returns the (T, leads) or (leads, T) signal array.

    MATLAB files don't have a fixed schema, so we can't assume a key name.
    Strategy: look for one of the common signal variable names first; if none
    match, fall back to the largest 2D numeric array in the file (excluding
    MATLAB's own '__header__'/'__version__'/'__globals__' meta keys) — in
    practice ECG .mat exports almost always have exactly one real array.
    """
    from scipy.io import loadmat

    mat = loadmat(path)
    candidate_keys = [k for k in mat.keys() if not k.startswith("__")]
    if not candidate_keys:
        raise ECGFormatError("The .mat file has no usable variables.")

    chosen_key = None
    for key in _MAT_SIGNAL_KEYS:
        if key in mat:
            chosen_key = key
            break

    if chosen_key is None:
        # fall back: pick the largest 2D numeric array among the remaining keys
        best_size = -1
        for key in candidate_keys:
            arr = mat[key]
            if isinstance(arr, np.ndarray) and arr.ndim == 2 and np.issubdtype(arr.dtype, np.number):
                if arr.size > best_size:
                    best_size = arr.size
                    chosen_key = key
        if chosen_key is None:
            raise ECGFormatError(
                f"Could not find a 2D numeric signal array in the .mat file. "
                f"Found variables: {candidate_keys}. Expected one of {_MAT_SIGNAL_KEYS} "
                f"or a single 2D numeric matrix."
            )

    arr = np.asarray(mat[chosen_key])
    if arr.ndim != 2:
        raise ECGFormatError(f"Signal variable '{chosen_key}' in .mat file is not 2D (shape {arr.shape}).")
    return arr.astype(np.float32)


def load_ecg_file(path: str, file_format: str, sampling_rate: int = 100) -> np.ndarray:
    """Returns raw (T, leads) float32 array — NOT yet normalized."""
    file_format = file_format.lower()
    if file_format == "csv":
        raw = load_csv(path)
    elif file_format == "npy":
        raw = load_npy(path)
    elif file_format == "mat":
        raw = load_mat(path)
    elif file_format == "wfdb":
        base = path[:-4] if path.endswith((".hea", ".dat")) else path
        raw = load_wfdb(base)
    else:
        raise ECGFormatError(f"Unsupported file format '{file_format}'. Use csv, npy, mat, or wfdb.")

    raw = _fix_orientation(raw)          # (T, leads)
    validate_ecg_signal(raw, sampling_rate)  # content sanity check, before resampling
    raw = _resample_to_seq_len(raw, sampling_rate)  # (SEQ_LEN, leads)
    return raw


def to_model_input(raw_t_leads: np.ndarray, lead_mean: np.ndarray, lead_std: np.ndarray) -> np.ndarray:
    """raw_t_leads: (SEQ_LEN, leads) -> normalized (1, leads, SEQ_LEN) for the model."""
    normalized = (raw_t_leads - lead_mean) / (lead_std + 1e-8)
    x = normalized.T  # (leads, SEQ_LEN)
    return x[np.newaxis, ...].astype(np.float32)  # (1, leads, SEQ_LEN)
