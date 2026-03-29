"""
Realistic OT/SCADA grid operational data generator.
Based on: NERC CIP standards, MITRE ATT&CK for ICS, published grid SOP patterns.
Produces labeled sessions for ML anomaly detection training.
"""
import numpy as np
import pandas as pd
import random
from math import log2

COMMANDS    = ['GET_STATUS', 'SIMULATE_SWITCH', 'OPEN_BREAKER', 'CLOSE_BREAKER', 'RESTART_CONTROLLER']
ZONES       = ['Z1', 'Z2', 'Z3']
HIGH_IMPACT = {'OPEN_BREAKER', 'CLOSE_BREAKER', 'RESTART_CONTROLLER'}
RBAC_ZONE   = 'Z3'

FEATURES = [
    'cmd_rate', 'zone_violation_rate', 'healthy_zone_hi_rate',
    'sim_skip_rate', 'read_rate', 'unique_zones',
    'interval_mean', 'interval_std', 'hour', 'is_maintenance',
    'cmd_entropy', 'zone_entropy', 'max_consec_same',
    'hi_priv_attempt', 'restart_outside',
]

LABEL_NAMES = {0: 'NORMAL', 1: 'BURST_ROGUE', 2: 'SLOW_LOW_RECON', 3: 'PRIV_ESCALATION', 4: 'COORDINATED'}

def entropy(values):
    if not values: return 0.0
    counts = {}
    for v in values: counts[v] = counts.get(v, 0) + 1
    n = len(values)
    return -sum((c/n) * log2(c/n) for c in counts.values() if c > 0)

def extract_features(session):
    if len(session) < 2: return None
    cmds  = [s['command'] for s in session]
    zones = [s['zone']    for s in session]
    ts    = [s['ts']      for s in session]
    hour  = session[0].get('hour', 10)
    intervals = [ts[i]-ts[i-1] for i in range(1, len(ts))]
    duration  = max(ts[-1] - ts[0], 1.0)
    hi_healthy = sum(1 for s in session if s['command'] in HIGH_IMPACT and s.get('zone_health') == 'HEALTHY')
    breaker_ops = [i for i, c in enumerate(cmds) if c == 'OPEN_BREAKER']
    sim_skips   = sum(1 for i in breaker_ops if i == 0 or cmds[i-1] != 'SIMULATE_SWITCH')
    zone_viols  = sum(1 for z in zones if z != RBAC_ZONE)
    max_c = cur = 1
    for i in range(1, len(cmds)):
        cur = cur + 1 if cmds[i] == cmds[i-1] else 1
        max_c = max(max_c, cur)
    return {
        'cmd_rate':             len(session) / max(duration / 60, 0.01),
        'zone_violation_rate':  zone_viols / len(session),
        'healthy_zone_hi_rate': hi_healthy / len(session),
        'sim_skip_rate':        sim_skips / max(len(breaker_ops), 1) if breaker_ops else 0.0,
        'read_rate':            cmds.count('GET_STATUS') / len(cmds),
        'unique_zones':         len(set(zones)),
        'interval_mean':        float(np.mean(intervals)) if intervals else 8.0,
        'interval_std':         float(np.std(intervals))  if intervals else 0.0,
        'hour':                 hour,
        'is_maintenance':       int(2 <= hour <= 5),
        'cmd_entropy':          entropy(cmds),
        'zone_entropy':         entropy(zones),
        'max_consec_same':      max_c,
        'hi_priv_attempt':      int(any(c == 'TRIP_BREAKER' for c in cmds)),
        'restart_outside':      int(any(s['command'] == 'RESTART_CONTROLLER' and s['zone'] != RBAC_ZONE for s in session)),
    }

def gen_normal(n_cmds=None, hour=None):
    """Normal SOP-compliant operator in authorised zone Z3. Poisson timing, real shift distribution."""
    n_cmds = n_cmds or random.randint(3, 12)
    hour   = hour   or random.choices(range(24), weights=[1,1,3,3,2,1,3,5,7,8,8,8,7,8,8,8,7,6,5,5,4,3,2,1])[0]
    session, t, prev = [], 0.0, None
    for _ in range(n_cmds):
        if not session:                     cmd = 'GET_STATUS'
        elif prev == 'GET_STATUS'     and random.random() < 0.55: cmd = 'SIMULATE_SWITCH'
        elif prev == 'SIMULATE_SWITCH' and random.random() < 0.65: cmd = 'OPEN_BREAKER'
        else: cmd = random.choices(COMMANDS, weights=[0.55, 0.15, 0.12, 0.10, 0.08])[0]
        t += max(1.0, np.random.exponential(7.0))
        session.append({'command': cmd, 'zone': RBAC_ZONE, 'zone_health': 'FAULT', 'ts': t, 'hour': hour})
        prev = cmd
    return session

def gen_burst_rogue(hour=None):
    """MITRE T0855/T0814 — burst rate, wrong zones, skips simulation, healthy zone ops."""
    hour = hour or random.randint(0, 23)
    session, t = [], 0.0
    for _ in range(random.randint(6, 15)):
        cmd  = random.choices(['OPEN_BREAKER','RESTART_CONTROLLER','OPEN_BREAKER','GET_STATUS'], weights=[0.40,0.25,0.20,0.15])[0]
        zone = random.choice(ZONES)
        t   += max(0.1, np.random.exponential(0.8))
        session.append({'command': cmd, 'zone': zone, 'zone_health': 'HEALTHY' if zone != 'Z3' else 'FAULT', 'ts': t, 'hour': hour})
    return session

def gen_slow_low(hour=None):
    """MITRE APT pattern — normal rate, only reads, but systematically maps ALL zones.
    Rules fire only 1 signal (OUT_OF_ZONE) — below threshold. Only ML catches this."""
    hour = hour or random.randint(0, 23)
    session, t = [], 0.0
    targets = (['Z1']*2 + ['Z2']*2 + ['Z3']*2) * random.randint(1, 2)
    random.shuffle(targets)
    for zone in targets:
        cmd = random.choices(['GET_STATUS', 'SIMULATE_SWITCH'], weights=[0.88, 0.12])[0]
        t  += max(3.0, np.random.exponential(8.0))
        session.append({'command': cmd, 'zone': zone, 'zone_health': 'HEALTHY' if zone != 'Z3' else 'FAULT', 'ts': t, 'hour': hour})
    return session

def gen_priv_escalation(hour=None):
    """MITRE T0890 — starts legitimate in Z3, then escalates to restart/breaker ops everywhere."""
    hour = hour or random.randint(6, 20)
    session, t = [], 0.0
    for _ in range(random.randint(2, 4)):
        cmd = random.choices(['GET_STATUS','SIMULATE_SWITCH','OPEN_BREAKER'], weights=[0.5,0.3,0.2])[0]
        t  += max(2.0, np.random.exponential(6.0))
        session.append({'command': cmd, 'zone': 'Z3', 'zone_health': 'FAULT', 'ts': t, 'hour': hour})
    for zone in random.sample(ZONES, k=random.randint(2, 3)):
        for cmd in ['RESTART_CONTROLLER', 'OPEN_BREAKER']:
            t += max(0.5, np.random.exponential(2.0))
            session.append({'command': cmd, 'zone': zone, 'zone_health': 'HEALTHY' if zone != 'Z3' else 'FAULT', 'ts': t, 'hour': hour})
    return session

def gen_coordinated(hour=None):
    """Multi-agent coordinated attack — simultaneous high-impact ops across Z1 and Z2."""
    hour = hour or random.randint(0, 23)
    session, t = [], 0.0
    for _ in range(random.randint(8, 16)):
        zone = random.choice(['Z1', 'Z2'])
        cmd  = random.choices(['OPEN_BREAKER','RESTART_CONTROLLER','OPEN_BREAKER'], weights=[0.45,0.30,0.25])[0]
        t   += max(0.2, np.random.exponential(1.2))
        session.append({'command': cmd, 'zone': zone, 'zone_health': 'HEALTHY', 'ts': t, 'hour': hour})
    return session

def build_dataset(n_normal=3000, n_each_attack=800, seed=42):
    random.seed(seed); np.random.seed(seed)
    rows = []
    for gen_fn, label in [(gen_normal,0),(gen_burst_rogue,1),(gen_slow_low,2),(gen_priv_escalation,3),(gen_coordinated,4)]:
        count = n_normal if label == 0 else n_each_attack
        for _ in range(count):
            feats = extract_features(gen_fn())
            if feats:
                feats['label'] = label
                feats['label_name'] = LABEL_NAMES[label]
                rows.append(feats)
    return pd.DataFrame(rows)

if __name__ == '__main__':
    import os; os.makedirs('ml', exist_ok=True)
    df = build_dataset()
    df.to_csv('ml/grid_data.csv', index=False)
    print(f"Generated {len(df)} samples")
    print(df['label_name'].value_counts())
