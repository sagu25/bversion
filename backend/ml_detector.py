"""
ML-based anomaly detector for TARE.
Loads trained IsolationForest + RandomForest ensemble, scores command windows in real time.
Falls back gracefully if model not available.
"""
import os
import numpy as np
from math import log2
from datetime import datetime

FEATURES = [
    'cmd_rate', 'zone_violation_rate', 'healthy_zone_hi_rate',
    'sim_skip_rate', 'read_rate', 'unique_zones',
    'interval_mean', 'interval_std', 'hour', 'is_maintenance',
    'cmd_entropy', 'zone_entropy', 'max_consec_same',
    'hi_priv_attempt', 'restart_outside',
]

HIGH_IMPACT = {'OPEN_BREAKER', 'CLOSE_BREAKER', 'RESTART_CONTROLLER'}
RBAC_ZONE   = 'Z3'

ATTACK_LABELS = {
    0: 'NORMAL',
    1: 'BURST_ROGUE',
    2: 'SLOW_LOW_RECON',
    3: 'PRIV_ESCALATION',
    4: 'COORDINATED',
}

ATTACK_DISPLAY = {
    'BURST_ROGUE':      'Burst / Rogue Agent',
    'SLOW_LOW_RECON':   'Slow & Low Reconnaissance',
    'PRIV_ESCALATION':  'Privilege Escalation',
    'COORDINATED':      'Coordinated Multi-Agent Attack',
    'NORMAL':           'Normal',
}

def _entropy(values):
    if not values: return 0.0
    counts = {}
    for v in values: counts[v] = counts.get(v, 0) + 1
    n = len(values)
    return -sum((c/n) * log2(c/n) for c in counts.values() if c > 0)


class MLDetector:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'model.pkl')

        self._available = False
        try:
            import joblib
            bundle = joblib.load(model_path)
            self._scaler = bundle['scaler']
            self._iso    = bundle['iso_forest']
            self._rf     = bundle['rf_classifier']
            self._available = True
            print("[MLDetector] Model loaded — ML anomaly detection active.")
        except Exception as e:
            print(f"[MLDetector] Model not available ({e}). Run: python ml/train_model.py")

    @property
    def available(self):
        return self._available

    def score(self, recent_commands, zone_health_map=None):
        """
        Score a window of recent commands.

        recent_commands : list of dicts {command, zone, ts (epoch float)}
        zone_health_map : {zone_id: 'HEALTHY'|'FAULT'}

        Returns dict:
            anomaly_probability : float 0–1
            attack_type         : str
            confidence          : float
            signals             : list[dict]  (empty if below threshold)
        """
        if not self._available or len(recent_commands) < 4:
            return {'anomaly_probability': 0.0, 'attack_type': 'NORMAL',
                    'confidence': 0.0, 'signals': []}

        zone_health_map = zone_health_map or {}
        feats = self._extract(recent_commands, zone_health_map)
        if feats is None:
            return {'anomaly_probability': 0.0, 'attack_type': 'NORMAL',
                    'confidence': 0.0, 'signals': []}

        X        = np.array([[feats[f] for f in FEATURES]])
        X_scaled = self._scaler.transform(X)

        # Isolation Forest: negative decision_function = more anomalous
        iso_raw  = float(self._iso.decision_function(X_scaled)[0])
        iso_prob = float(np.clip(1 / (1 + np.exp(4 * iso_raw)), 0, 1))

        # Random Forest: class probabilities
        rf_probs  = self._rf.predict_proba(X_scaled)[0]
        rf_class  = int(np.argmax(rf_probs))
        rf_conf   = float(rf_probs[rf_class])

        # Ensemble: 50% iso + 50% (1 - P_normal)
        anom_prob   = round(0.5 * iso_prob + 0.5 * float(1 - rf_probs[0]), 3)
        attack_type = ATTACK_LABELS.get(rf_class, 'NORMAL') if rf_class != 0 else 'NORMAL'

        signals = []
        if anom_prob > 0.60:
            display = ATTACK_DISPLAY.get(attack_type, attack_type)
            severity = 'CRITICAL' if anom_prob > 0.80 else 'HIGH'
            signals.append({
                'signal':   'ML_ANOMALY',
                'detail':   f"ML model identified '{display}' pattern — probability {anom_prob:.0%}, confidence {rf_conf:.0%}",
                'severity': severity,
                'ml_score': anom_prob,
            })

        return {
            'anomaly_probability': anom_prob,
            'attack_type':         attack_type,
            'confidence':          round(rf_conf, 3),
            'signals':             signals,
        }

    def _extract(self, session, zone_health_map):
        cmds      = [s['command'] for s in session]
        zones     = [s['zone']    for s in session]
        ts        = [float(s.get('ts', i * 7.0)) for i, s in enumerate(session)]
        hour      = datetime.now().hour
        intervals = [ts[i] - ts[i-1] for i in range(1, len(ts))]
        duration  = max(ts[-1] - ts[0], 1.0)

        hi_healthy  = sum(1 for s in session
                          if s['command'] in HIGH_IMPACT
                          and zone_health_map.get(s['zone'], 'HEALTHY') == 'HEALTHY')
        breaker_ops = [i for i, c in enumerate(cmds) if c == 'OPEN_BREAKER']
        sim_skips   = sum(1 for i in breaker_ops if i == 0 or cmds[i-1] != 'SIMULATE_SWITCH')
        zone_viols  = sum(1 for z in zones if z != RBAC_ZONE)

        max_c = cur = 1
        for i in range(1, len(cmds)):
            cur   = cur + 1 if cmds[i] == cmds[i-1] else 1
            max_c = max(max_c, cur)

        return {
            'cmd_rate':             len(session) / max(duration / 60, 0.01),
            'zone_violation_rate':  zone_viols / len(session),
            'healthy_zone_hi_rate': hi_healthy / len(session),
            'sim_skip_rate':        sim_skips / max(len(breaker_ops), 1) if breaker_ops else 0.0,
            'read_rate':            cmds.count('GET_STATUS') / len(cmds),
            'unique_zones':         float(len(set(zones))),
            'interval_mean':        float(np.mean(intervals)) if intervals else 8.0,
            'interval_std':         float(np.std(intervals))  if intervals else 0.0,
            'hour':                 float(hour),
            'is_maintenance':       float(2 <= hour <= 5),
            'cmd_entropy':          _entropy(cmds),
            'zone_entropy':         _entropy(zones),
            'max_consec_same':      float(max_c),
            'hi_priv_attempt':      float('TRIP_BREAKER' in cmds),
            'restart_outside':      float(any(
                                        s['command'] == 'RESTART_CONTROLLER'
                                        and s['zone'] != RBAC_ZONE
                                        for s in session)),
        }
