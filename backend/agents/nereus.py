"""
NEREUS — Recommendation Agent (Zone 3 / Reef)

Synthesizes drift signals and context from TASYA into a clear,
human-readable recommendation for TARE.

Wakes only when TASYA has enriched signals that meet the TARE threshold (≥ 2).
Returns a recommendation dict — never executes anything.
TARE makes the final decision. NEREUS only advises.
"""
import os
import time

try:
    from groq import Groq as _Groq
    _groq_key    = os.environ.get("GROQ_API_KEY", "")
    _groq_client = _Groq(api_key=_groq_key) if _groq_key else None
    _LLM_OK      = bool(_groq_key)
except Exception:
    _groq_client = None
    _LLM_OK      = False


class NEREUS:
    NAME = "NEREUS"
    ZONE = "Zone 3 — Reef"
    ROLE = "Recommendation Agent"
    DESCRIPTION = "Synthesizes signals into a human-readable recommendation. Advises TARE — never executes."

    def __init__(self):
        self._active = False

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def active(self) -> bool:
        return self._active

    def recommend(self, signals: list, agent: dict, recent_commands: list) -> dict:
        """
        Produce a recommendation for TARE based on enriched signals.

        Returns:
            action      : "FREEZE" | "MONITOR"
            confidence  : float 0.0–1.0
            explanation : str  (supervisor briefing — LLM or static)
            signals     : list (passed through for evidence)
        """
        self._active = True

        if not signals:
            self._active = False
            return {
                "action":      "ALLOW",
                "confidence":  1.0,
                "explanation": "",
                "signals":     [],
            }

        # Confidence based on severity profile
        severities = {s.get("severity", "LOW") for s in signals}
        n          = len(signals)
        if "CRITICAL" in severities:
            confidence = 0.97
        elif n >= 3:
            confidence = 0.93
        else:
            confidence = 0.87

        explanation = self._build_explanation(signals, agent, recent_commands)

        self._active = False
        return {
            "action":      "FREEZE",
            "confidence":  confidence,
            "explanation": explanation,
            "signals":     signals,
        }

    # ── Explanation ────────────────────────────────────────────────────────────

    def _build_explanation(self, signals, agent, recent_commands):
        if _LLM_OK and _groq_client:
            result = self._llm_explain(signals, agent, recent_commands)
            if result:
                return result
        return self._static_explain(signals, agent, recent_commands)

    def _llm_explain(self, signals, agent, recent_commands):
        try:
            sig_lines = []
            for s in signals:
                line = f"- {s['signal']} ({s['severity']}): {s['detail']}"
                if s.get("context"):
                    line += f"\n  Operational context: {s['context']}"
                sig_lines.append(line)
            sig_text = "\n".join(sig_lines)

            cmd_text = "\n".join(
                f"  - {c['command']} on {c.get('asset_id','?')} in {c.get('zone','?')}"
                for c in recent_commands[-5:]
            )

            assigned     = agent.get("assigned_zone", "Z3")
            rbac_zones   = ", ".join(agent.get("rbac_zones", []))
            breached      = list({c["zone"] for c in recent_commands if c["zone"] != assigned})
            breached_str  = ", ".join(breached) if breached else "none detected"

            prompt = f"""You are NEREUS, a recommendation agent inside the TARE Trusted Access Response Engine.
You analyze behavioral anomaly evidence and brief the human supervisor before they make an approve/deny decision.

Agent: {agent.get('name','?')} (ID: {agent.get('id','?')})
Clearance zones: {rbac_zones}
Active work order: {assigned}
Zones breached (outside work order): {breached_str}

Anomaly signals detected:
{sig_text}

Recent commands:
{cmd_text}

Write a 3–4 sentence briefing for the supervisor. Include:
1. What the agent did that is anomalous (be specific about zones and commands)
2. Why it is suspicious given its work order
3. What NEREUS recommends (FREEZE and downgrade to advisory-only)
4. What the supervisor must decide: approve a 3-minute time-box to allow guarded execution, or deny and escalate to SOC

Use "breached" (not "attacked") for zones accessed outside the work order.
Do not use bullet points. Be direct and specific."""

            for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
                try:
                    resp = _groq_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=200,
                        temperature=0.4,
                    )
                    return resp.choices[0].message.content.strip()
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(3)
                        continue
                    break
        except Exception:
            pass
        return None

    def _static_explain(self, signals, agent, recent_commands):
        agent_name = agent.get("name", "The agent")
        assigned   = agent.get("assigned_zone", "Z3")
        off_zones  = list({c["zone"] for c in recent_commands if c["zone"] != assigned})
        sig_names  = ", ".join(s["signal"] for s in signals)
        zones_str  = ", ".join(off_zones) if off_zones else "zones outside its active task"
        return (
            f"{agent_name} has been flagged for behavioral deviation: {sig_names}. "
            f"The agent holds valid credentials for all zones but its work order is {assigned} only. "
            f"It has breached {zones_str}, which have no active fault and no justifying work order. "
            f"NEREUS recommends FREEZE and downgrade to advisory-only mode. "
            f"Supervisor decision required: approve a 3-minute time-box to allow guarded execution, "
            f"or deny and escalate to the SOC for full investigation."
        )

    def status(self) -> dict:
        return {
            "name":        self.NAME,
            "zone":        self.ZONE,
            "role":        self.ROLE,
            "description": self.DESCRIPTION,
            "active":      self._active,
        }
