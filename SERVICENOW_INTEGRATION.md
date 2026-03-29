# TARE — ServiceNow Integration Guide
### Trusted Access Response Engine · Energy & Utilities Security Platform
*Integration Reference — Internal Use Only*

---

## Current State (POC)

TARE already builds a fully structured ServiceNow incident in memory every time
it fires. The incident object contains all the fields a real ServiceNow instance
expects. The only missing piece is the API call that sends it.

**What the POC does today:**
```python
self.active_incident = {
    "incident_id":       "INC-TARE-20260324-9644",
    "short_description": "Post-grant identity behaviour deviation detected — operations frozen",
    "priority":          "1 — Critical",
    "state":             "New",
    "assigned_to":       "SOC Analyst",
    "category":          "Security / Identity",
    "created_at":        "2026-03-24T00:17:00",
    "evidence": {
        "anomaly_signals":  [...],
        "anomaly_score":    75,
        "recent_commands":  [...],
        "actions_taken":    [...],
    }
}
```

This object is broadcast to the UI in real time. Wiring it to a live
ServiceNow instance is a ~2 hour task once you have credentials.

---

## What You Need

### 1. ServiceNow Developer Instance (Free)
- Go to **developer.servicenow.com**
- Sign up for a free account
- Request a Personal Developer Instance (PDI)
- You get a full ServiceNow environment at a URL like:
  `https://dev123456.service-now.com`
- Takes 5–10 minutes to provision

### 2. ServiceNow Credentials
From your developer instance, you need:

| Credential | Where to find it | Example |
|---|---|---|
| Instance URL | Your PDI URL | `https://dev123456.service-now.com` |
| Username | Admin username | `admin` |
| Password | Admin password | Set during instance setup |

For production, use a **dedicated integration user** with minimal permissions
instead of the admin account.

### 3. Python `requests` Library
Already available if you have pip. If not:
```
pip install requests
```

---

## How ServiceNow Incident API Works

ServiceNow exposes a REST API called the **Table API**.
Creating an incident is a single POST request to:

```
POST https://{instance}.service-now.com/api/now/table/incident
```

With Basic Auth (username + password) and a JSON body.

**Minimal working example:**
```python
import requests
import json

url = "https://dev123456.service-now.com/api/now/table/incident"

headers = {
    "Content-Type": "application/json",
    "Accept":       "application/json",
}

payload = {
    "short_description": "Post-grant identity behaviour deviation — operations frozen",
    "priority":          "1",          # 1 = Critical
    "urgency":           "1",          # 1 = High
    "impact":            "1",          # 1 = High
    "category":          "Security",
    "subcategory":       "Identity",
    "assigned_to":       "SOC Analyst",
    "description":       "Full evidence here...",
}

response = requests.post(
    url,
    auth=("admin", "your_password"),
    headers=headers,
    json=payload,
)

result = response.json()
sys_id = result["result"]["sys_id"]          # ServiceNow's internal ID
incident_number = result["result"]["number"]  # e.g. INC0010042
```

---

## Integration Steps — Step by Step

### Step 1 — Add credentials to .env

Open `backend/.env` and add:

```
GROQ_API_KEY=your_groq_key_here
SNOW_INSTANCE=dev123456
SNOW_USER=admin
SNOW_PASS=your_password_here
```

---

### Step 2 — Create servicenow_client.py

Create a new file: `backend/servicenow_client.py`

```python
"""
TARE — ServiceNow Integration Client
Sends incidents to a live ServiceNow instance via Table API.
"""
import os
import json
import requests
from datetime import datetime

SNOW_INSTANCE = os.environ.get("SNOW_INSTANCE", "")
SNOW_USER     = os.environ.get("SNOW_USER", "")
SNOW_PASS     = os.environ.get("SNOW_PASS", "")
SNOW_ENABLED  = bool(SNOW_INSTANCE and SNOW_USER and SNOW_PASS)

INCIDENT_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"

HEADERS = {
    "Content-Type": "application/json",
    "Accept":       "application/json",
}

PRIORITY_MAP = {
    "1 — Critical": "1",
    "2 — High":     "2",
    "3 — Medium":   "3",
    "4 — Low":      "4",
}


def create_incident(tare_incident: dict) -> dict:
    """
    Takes a TARE incident dict and creates a real ServiceNow incident.
    Returns the ServiceNow response or a mock response if not configured.
    """
    if not SNOW_ENABLED:
        print("[ServiceNow] Not configured — skipping live API call.")
        return {"status": "skipped", "reason": "SNOW credentials not set"}

    signals   = tare_incident.get("evidence", {}).get("anomaly_signals", [])
    commands  = tare_incident.get("evidence", {}).get("recent_commands", [])
    actions   = tare_incident.get("evidence", {}).get("actions_taken", [])
    score     = tare_incident.get("evidence", {}).get("anomaly_score", 0)

    sig_text  = "\n".join(f"- {s['signal']} ({s['severity']}): {s['detail']}" for s in signals)
    cmd_text  = "\n".join(f"- {c['command']} on {c['asset_id']} in {c['zone']} at {c['ts']}" for c in commands[-10:])
    act_text  = "\n".join(f"- {a}" for a in actions)

    description = f"""TARE AEGIS-ID — Automated Security Incident

Incident ID (TARE): {tare_incident.get('incident_id', 'N/A')}
Created At:         {tare_incident.get('created_at', datetime.now().isoformat())}
Anomaly Score:      {score}/100

DEVIATION SIGNALS DETECTED:
{sig_text}

RECENT COMMANDS (last 10):
{cmd_text}

ACTIONS TAKEN BY TARE:
{act_text}

This incident was created automatically by the TARE detection engine.
A human supervisor has been notified and must approve or deny continued access.
"""

    payload = {
        "short_description": tare_incident.get("short_description",
                             "Post-grant AI agent identity deviation detected"),
        "priority":          PRIORITY_MAP.get(tare_incident.get("priority", "1 — Critical"), "1"),
        "urgency":           "1",
        "impact":            "1",
        "category":          "Security",
        "subcategory":       "Identity",
        "assigned_to":       tare_incident.get("assigned_to", "SOC Analyst"),
        "description":       description,
        "work_notes":        f"TARE Anomaly Score: {score}/100. Signals: {', '.join(s['signal'] for s in signals)}",
    }

    try:
        response = requests.post(
            INCIDENT_URL,
            auth=(SNOW_USER, SNOW_PASS),
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json().get("result", {})
        snow_number = result.get("number", "N/A")
        snow_sys_id = result.get("sys_id", "N/A")
        print(f"[ServiceNow] Incident created: {snow_number} (sys_id: {snow_sys_id})")
        return {
            "status":      "created",
            "number":      snow_number,
            "sys_id":      snow_sys_id,
            "url":         f"https://{SNOW_INSTANCE}.service-now.com/nav_to.do?uri=incident.do?sys_id={snow_sys_id}",
        }

    except requests.exceptions.Timeout:
        print("[ServiceNow] Timeout — incident not created.")
        return {"status": "error", "reason": "timeout"}
    except requests.exceptions.HTTPError as e:
        print(f"[ServiceNow] HTTP error: {e}")
        return {"status": "error", "reason": str(e)}
    except Exception as e:
        print(f"[ServiceNow] Unexpected error: {e}")
        return {"status": "error", "reason": str(e)}


def update_incident_state(sys_id: str, state: str, work_notes: str = "") -> dict:
    """
    Updates an existing incident state.
    state: '2' = In Progress, '6' = Resolved, '7' = Closed
    """
    if not SNOW_ENABLED or not sys_id:
        return {"status": "skipped"}

    url = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident/{sys_id}"
    payload = {"state": state}
    if work_notes:
        payload["work_notes"] = work_notes

    try:
        response = requests.patch(
            url,
            auth=(SNOW_USER, SNOW_PASS),
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        print(f"[ServiceNow] Incident {sys_id} updated to state {state}.")
        return {"status": "updated"}
    except Exception as e:
        print(f"[ServiceNow] Update error: {e}")
        return {"status": "error", "reason": str(e)}
```

---

### Step 3 — Wire into tare_engine.py

In `backend/tare_engine.py`, add the import at the top:

```python
try:
    from servicenow_client import create_incident, update_incident_state, SNOW_ENABLED
except Exception:
    SNOW_ENABLED = False
    def create_incident(i): return {"status": "skipped"}
    def update_incident_state(s, t, w=""): return {"status": "skipped"}
```

In `_fire_tare()`, after building `self.active_incident`, add:

```python
# Wire to live ServiceNow (if configured)
snow_result = create_incident(self.active_incident)
if snow_result.get("status") == "created":
    self.active_incident["snow_number"] = snow_result["number"]
    self.active_incident["snow_url"]    = snow_result["url"]
    self.active_incident["snow_sys_id"] = snow_result["sys_id"]
```

In `deny_timebox()`, add escalation update:

```python
sys_id = self.active_incident.get("snow_sys_id") if self.active_incident else None
if sys_id:
    update_incident_state(sys_id, "2",
        work_notes="Supervisor denied time-box. Incident escalated to Critical. Agent locked out.")
```

---

### Step 4 — Add to requirements.txt

```
requests>=2.31.0
```

---

## What Changes in the UI

Once wired, the INCIDENT tab will show a real ServiceNow incident number
(e.g. `INC0010042`) instead of the TARE-generated ID. You can also add a
clickable link to open the incident directly in ServiceNow.

To show the real incident number in the UI, update the IncidentCard component
to display `incident.snow_number` when available.

---

## Testing Without a Live Instance

Use the **ServiceNow REST API Explorer** built into your developer instance:
- Login to your PDI
- Go to: `https://dev123456.service-now.com/nav_to.do?uri=api_explorer`
- Test the `POST /api/now/table/incident` endpoint directly in the browser

Or test with `curl`:
```bash
curl -X POST \
  https://dev123456.service-now.com/api/now/table/incident \
  -u "admin:your_password" \
  -H "Content-Type: application/json" \
  -d '{"short_description":"Test from TARE","priority":"1"}'
```

---

## ServiceNow Priority Values

| TARE Priority | ServiceNow Value | Meaning |
|---|---|---|
| 1 — Critical | `"1"` | Immediate response required |
| 2 — High | `"2"` | Respond within 1 hour |
| 3 — Medium | `"3"` | Respond within 4 hours |
| 4 — Low | `"4"` | Respond within 24 hours |

## ServiceNow State Values

| State | Value | When TARE uses it |
|---|---|---|
| New | `"1"` | Incident first created |
| In Progress | `"2"` | Supervisor denied — investigation begins |
| Resolved | `"6"` | Timebox approved and completed cleanly |
| Closed | `"7"` | Manual close after full investigation |

---

## Estimated Integration Time

| Task | Time |
|---|---|
| Get ServiceNow developer instance | 10 mins |
| Create `servicenow_client.py` | 20 mins |
| Wire into `tare_engine.py` | 20 mins |
| Test and verify incidents appear | 20 mins |
| **Total** | **~70 mins** |

---

## Production Considerations

| Topic | Recommendation |
|---|---|
| **Authentication** | Use OAuth 2.0 instead of Basic Auth for production |
| **Integration user** | Create a dedicated `tare_integration` user with only `itil` role — not admin |
| **Assignment group** | Map `assigned_to` to a real ServiceNow assignment group (e.g. `SOC-OT-GRID`) |
| **CMDB link** | Link incidents to a CMDB CI for the affected grid zone/asset |
| **Attachment** | Use `/api/now/attachment` to attach the full audit log as a file |
| **Retry logic** | Add exponential backoff if ServiceNow is temporarily unavailable |
| **Async** | Run the API call in a background thread so it doesn't block TARE's response |

---

*TARE AEGIS-ID — ServiceNow Integration Guide*
*Energy & Utilities Security Platform — Internal Use Only*
*Version: 1.0 — March 2026*
