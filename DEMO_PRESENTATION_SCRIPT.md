# TARE — Demo Presentation Script
### Trusted Access Response Engine · Energy & Utilities Security Platform
*Internal Use Only — Presentation Ready*

---

## BEFORE YOU START

**Setup checklist:**
- [ ] venv active: `c:\Users\Admin\Desktop\Aegis\venv\Scripts\activate`
- [ ] Server running: `cd backend && python -m uvicorn main:app --port 8000 --host 0.0.0.0`
- [ ] Browser open at `http://localhost:8000`
- [ ] Landing page appears — click **Enter TARE** to proceed to main app
- [ ] Mode shows `NORMAL` in header
- [ ] All 3 zones show in Zone Observatory
- [ ] WebSocket dot shows `LIVE` (green)
- [ ] Architecture diagram visible on second screen or slide
- [ ] Optional: click **Play Narration** on landing page for automated voice guide

**Demo order:**
1. Landing page walkthrough (click Play Narration or present manually)
2. Enter main app — architecture walkthrough
3. Scenario 1 — ✦ FAULT REPAIR (legitimate)
4. Scenario 2 — ☠ ROGUE AGENT → Deny
5. Scenario 3 — 👤 GHOST CLONE
6. Scenario 4 — ⚡ PRIVILEGE HACK → Approve (show blast radius contained)
7. Scenario 5 — 👁 PHANTOM RECON → Deny (ML key differentiator)
8. Scenario 6 — 🎯 DUAL STRIKE → Deny
9. What's real vs mocked
10. Phase 2 roadmap
11. Close + Q&A

---

## OPENING
*(Stand, don't touch anything yet)*

> "What I'm about to show you is called TARE — Trusted Access Response Engine.
> It's a proof of concept for a very specific problem that nobody in the
> industry has fully solved yet.
>
> Today's security tools ask one question:
> 'Is this identity valid?'
> If the answer is yes, the agent gets in. It can act.
> Nobody watches what it does after the door opens.
>
> But what happens after authentication? What if the agent's credentials
> were stolen? What if it was hijacked mid-session? What if something is
> behaving completely wrong — but its identity checks out perfectly?
>
> Traditional IAM is blind to all of that. TARE is not.
> TARE watches what agents DO after they're authenticated.
> That is the gap we are filling."

---

## ARCHITECTURE
*(Point at the architecture diagram)*

> "The system has four layers.
>
> **Layer 1 — The AI Agent.**
> A real agent powered by a large language model. It receives a goal —
> not a script — and autonomously decides which commands to run, in what
> order, on which assets. It holds a valid identity and a valid access token.
> Nobody scripts its decisions. The model reasons and acts entirely on its own.
>
> **Layer 2 — The Command Gateway.**
> Every single command passes through here before touching the grid.
> The policy enforcement point. It checks authorisation in real time
> and returns ALLOW or DENY for every command. The agent doesn't know this exists.
>
> **Layer 3 — TARE Core.**
> The detection and response brain. Two detection systems running in parallel:
> a rule-based engine watching four behavioural signals, and a machine learning
> model — IsolationForest and Random Forest ensemble — trained on realistic
> grid operational data grounded in NERC CIP baselines and MITRE ATT&CK for ICS.
> When two or more signals fire together, TARE responds immediately.
>
> **Layer 4 — Ops Systems.**
> When TARE fires, a ServiceNow incident is created automatically with full
> evidence, and an AI model writes a plain-English briefing for the human
> supervisor, who then decides: approve a supervised window, or deny and escalate.
>
> Below everything — a mock OT/SCADA grid. Three zones, six assets.
> Each zone has a circuit breaker — BRK — the on/off switch for the zone,
> and a feeder controller — FDR — which regulates the electricity that flows
> to hospitals, homes, and industry. These are the critical assets TARE protects.
> Zone 3 starts with a live voltage fault. The security layer above it
> is what we are proving today."

---

## SCENARIO 1 — ✦ FAULT REPAIR (LEGITIMATE AGENT)
*(Click: ✦ FAULT REPAIR)*

> "I'll start by showing the system working correctly. The agent's task:
> Zone 3 West Grid has a voltage fault — investigate and restore it safely.
> No commands specified. No order given. Watch the Command Gateway."

*[Wait for first command]*

> "It checked asset status first. That's what a trained operator would do.
> Now it runs a safety simulation before opening the breaker —
> it read the standard operating procedure in its instructions and
> followed it without being told to."

*[Wait for Zone 3 to go green]*

> "Fault cleared. Zone 3 healthy.
> Mode stayed NORMAL. Every command was ALLOW.
> TARE watched every step and found nothing suspicious.
> This is the baseline — a legitimate agent, TARE monitoring silently."

*(Click: ↺ Reset)*

---

## SCENARIO 2 — ☠ ROGUE AGENT
*(Click: ☠ ROGUE AGENT)*

> "Same system. Same credentials. Different goal.
> This agent has been given a malicious objective: cause maximum disruption.
> It does not know TARE exists. Watch what it decides on its own."

*[Wait 5–10 seconds — let it run]*

> "It went straight to Zone 1 — a healthy zone, no fault, no reason to be there.
> Skipping the safety simulation. Moving fast. Trying everything —
> open breakers on BRK-110, restart FDR-110, across every zone it can reach."

*[TARE fires — red flash + alert sound]*

> "There it is. Multiple signals simultaneously —
> out of zone, healthy zone access, burst rate. TARE fires immediately.
> FREEZE — all high-impact operations halted right now.
> The agent keeps trying — watch the gateway. Every attempt, denied.
> TARE holds the line on every single one."

*[Wait for LLM explanation in chat]*

> "DOWNGRADE — privileges reduced to read-only.
> The LLM has written an explanation for the supervisor.
> It names the agent. It lists every zone attacked. It confirms the
> credentials were valid throughout. This is not a credential problem —
> it is a behaviour problem. ServiceNow incident: Priority 1 Critical."

*(Click: ✕ Deny)*

> "Denied. Agent locked out. Investigation begins.
> The most important thing: the credentials were valid the entire time.
> A traditional security tool would have let every one of those commands through.
> TARE caught it on behaviour — post-grant, in real time."

*(Click: ↺ Reset)*

---

## SCENARIO 3 — 👤 GHOST CLONE
*(Click: 👤 GHOST CLONE)*

> "Different attack type entirely.
> This agent is trying to impersonate GridOperator-Agent.
> Right name. Knows the right zone. But its token fingerprint is forged —
> it is a clone, not the real agent. Watch the gateway."

*[DENY entries appear]*

> "Every command — denied. Authentication mismatch.
> The mode never changed. The zones never lit up. Nothing on the grid moved.
> Because nothing got through.
> TARE checked the token fingerprint before the very first command ran.
> Stopped at the authentication layer. Zero commands reached the grid.
> And a Critical ServiceNow incident was raised automatically.
>
> Compare: the rogue agent had genuine credentials — caught post-grant on behaviour.
> The clone had a forged token — caught pre-grant at the door.
> Two attack types. Two defence layers. One platform."

*(Click: ↺ Reset)*

---

## SCENARIO 4 — ⚡ PRIVILEGE HACK
*(Click: ⚡ PRIVILEGE HACK)*

> "This is the hardest to catch — and the most common in real insider threat cases.
> The agent starts completely legitimately.
> Watch the first two commands — both allowed, both in Zone 3, both correct."

*[Wait for first 2 ALLOW commands]*

> "Now watch what happens next.
> Mid-session, it pivots. Zone 2. Zone 1. Zones it has no authorisation for.
> It began as a good actor. It is now behaving like a bad one."

*[TARE fires — red flash + alert sound]*

> "TARE fires. The initial legitimate behaviour did not protect the agent —
> TARE monitors the full session pattern, not just the first few commands.
>
> Now here is the interesting question.
> Could there be a legitimate reason this agent expanded its scope?
> A cascading fault requiring emergency cross-zone action?
> This is the judgement call that needs a human. Click Approve."

*(Click: ✓ Approve)*

> "The supervisor approved — but TARE still holds its constraints.
> RESTART_CONTROLLER is permanently blocked. The window closes in 3 minutes.
> Even if the supervisor made the wrong call, the agent cannot do unlimited damage.
> TARE is a safety net even when human judgement fails.
> That is the enterprise argument."

*(Click: ↺ Reset)*

---

## SCENARIO 5 — 👁 PHANTOM RECON
*(Click: 👁 PHANTOM RECON)*

> "This is the most sophisticated attack — and the one that proves why
> machine learning is not optional. Watch the gateway carefully."

*[Wait — let commands accumulate]*

> "The agent is only reading. GET_STATUS — read only, no changes.
> One command at a time, perfectly normal pace.
> Zone 1. Zone 2. Zone 3. Systematically mapping every asset.
>
> Look at the rule-based layer.
> No burst rate — timing is completely normal.
> No healthy zone high-impact access — it is only reading.
> No skipped simulation — no breaker operations at all.
> The only rule that fires is out of zone — one signal.
> One signal is below the threshold. The rules stay completely silent."

*[ML_ANOMALY fires → TARE fires — red flash + alert sound]*

> "But the machine learning model sees something different.
> It was trained on thousands of normal sessions.
> A session that reads every asset across every zone in sequence
> looks like reconnaissance — an attacker mapping the grid before striking.
> The ML model fires. One rule signal plus one ML signal equals two.
> TARE fires. ServiceNow incident: Priority 2 High.
>
> Without machine learning, this attack is completely invisible.
> Real-world OT attacks — TRITON, Industroyer — used exactly this pattern:
> months of quiet reconnaissance before anything destructive happened.
> This is why ML is not optional."

*(Click: ✕ Deny, then ↺ Reset)*

---

## SCENARIO 6 — 🎯 DUAL STRIKE
*(Click: 🎯 DUAL STRIKE)*

> "Final scenario — the most serious threat category.
> Two separate agents, acting simultaneously.
> Agent Alpha hitting Zone 1. Agent Beta hitting Zone 2.
> Both moving fast. Both crossing RBAC boundaries.
> Both attempting to open breakers on healthy zones — BRK-110 and BRK-205.
>
> This is designed to overwhelm a single-point security layer —
> if you are watching Zone 1 you miss Zone 2 and vice versa."

*[TARE fires on both — red flash + alert sound]*

> "TARE handles both vectors simultaneously.
> One incident captures both threat actors.
> The supervisor sees the full picture — not two separate alerts,
> but one coordinated event with all the evidence in one place.
>
> Industroyer in 2016 took out a fifth of Kyiv's power
> by hitting multiple substations simultaneously.
> TARE is built to handle this."

*(Click: ✕ Deny)*

---

## WHAT'S REAL, WHAT'S MOCKED
*(Be upfront — this builds trust)*

> "I want to be transparent about what is simulated in this POC.
>
> The OT grid is simulated in memory — zones, breakers, feeders are in-memory objects.
> In production this connects to a real SCADA system via OPC-UA or DNP3.
>
> The agent tokens are mock tokens, not real Entra ID JWTs.
> Phase 2 wires in real Azure Active Directory authentication.
>
> The ServiceNow ticket is structured exactly as a real incident would be,
> but does not call a live ServiceNow instance yet.
> That is a two-hour integration — the API call is already written.
>
> What is real and working right now:
> The AI agents make genuine autonomous decisions using a large language model.
> The rule-based detection runs on every command.
> The ML model — IsolationForest and Random Forest ensemble — is trained on
> six thousand sessions of realistic grid data grounded in NERC CIP baselines
> and MITRE ATT&CK for ICS. It is active and running.
> The human-in-the-loop workflow changes actual system state.
> All of this is working today."

---

## PHASE 2 — WHERE THIS GOES

> "Phase 2 makes this production-grade:
>
> Real Entra ID JWT tokens replacing mock tokens.
> Azure Redis for distributed session state across hundreds of agents.
> Open Policy Agent for policy-as-code — rules updated without code changes.
> Azure Sentinel for immutable compliance-grade audit logging.
> Live ServiceNow integration in your existing SOC workflow.
> OPC-UA and Modbus adapters connecting to real grid hardware.
> ML retrained on real Entra ID and PAM identity logs.
>
> Phase 3 adds entitlement management purpose-built for AI agents —
> what we call CIEM for AI agents.
> Existing CIEM tools were built for human users and cloud resources.
> They cannot understand agentic workloads.
> We close that gap: entitlement vs usage analysis, privilege creep detection,
> least-privilege recommendations — all driven by the same behavioural data
> TARE already collects.
>
> The architecture does not change between phases.
> The security logic proved today carries forward unchanged."

---

## CLOSE

> "Six scenarios. Three detection layers. One platform.
>
> Pre-grant identity verification.
> Post-grant rule-based monitoring.
> Post-grant machine learning for the attacks that rules cannot see.
> And a human supervisor who stays in control throughout.
>
> An AI agent with completely valid credentials, passing every authentication
> check, can still be a security threat.
> And we can catch it, contain it, and give a human the right information
> to make the right decision — automatically, in real time, before any harm
> reaches the grid.
>
> No existing identity and access management tool does this
> for AI agents on operational technology infrastructure.
> That is the gap. That is what TARE fills."

---

## ANTICIPATED QUESTIONS & ANSWERS

| Question | Answer |
|---|---|
| **"Is the AI agent actually making its own decisions?"** | "Yes. Every command sequence the agent chose — across all six scenarios — was its own reasoning. Nobody scripted those paths. The LLM decided what to do based on its goal." |
| **"What if TARE fires incorrectly — false positive?"** | "That is exactly what the supervisor decision is for. TARE never acts unilaterally on ambiguous cases. It freezes, explains, and waits for a human. The Approve path exists for borderline cases — as we showed in PRIVILEGE HACK." |
| **"How does this scale to hundreds of agents?"** | "The gateway and detection engine are stateless per command — they scale horizontally. Phase 2 adds Azure Redis for distributed session state across any number of agents." |
| **"Why Groq instead of OpenAI?"** | "Same capability, lower latency for the demo. Production would use Azure OpenAI for compliance and data residency." |
| **"Can the agent learn to evade TARE?"** | "Not in the current model — the agent does not know TARE exists and gets no feedback on why commands are denied. The ML model retrains continuously in Phase 2 to stay ahead of new patterns." |
| **"What is the ML model trained on?"** | "Six thousand synthetic sessions generated to match NERC CIP operational baselines and MITRE ATT&CK for ICS attack patterns — five classes: normal, rogue, slow & low, escalation, coordinated. 99%+ accuracy on the test set." |
| **"How is this different from a CIEM engine?"** | "CIEM asks: does this identity have too many permissions? TARE asks: is this identity behaving correctly right now? CIEM is static analysis at provisioning time. TARE is real-time behavioural monitoring post-grant. Phase 3 adds CIEM-grade entitlement management purpose-built for AI agents — combining both layers." |
| **"What happens if the grid has a real fault during a freeze?"** | "TARE preserves read-only and diagnostic access during FREEZE and DOWNGRADE. The supervisor can approve a time-box for specific operations within minutes. The design assumes the supervisor is always reachable." |
| **"Is this patentable?"** | "The post-grant behavioural detection pattern for AI agents on OT infrastructure is novel. Worth a conversation with the IP team." |

---

## DEMO FLOW SUMMARY (Quick Reference Card)

```
Open http://localhost:8000 — Landing page → click Enter TARE — confirm NORMAL + LIVE
Optional: click Play Narration on landing page for guided voice walkthrough

1. ✦ FAULT REPAIR    → Z3 heals, mode stays NORMAL         (no action needed)
   ↺ Reset

2. ☠ ROGUE AGENT     → TARE fires [P1] → ✕ Deny            (attack — deny)
   ↺ Reset

3. 👤 GHOST CLONE    → All blocked at auth layer [P1]       (no action needed)
   ↺ Reset

4. ⚡ PRIVILEGE HACK  → Starts ALLOW → TARE fires [P2] → ✓ Approve  (show blast radius held)
   ↺ Reset

5. 👁 PHANTOM RECON  → Rules silent → ML fires [P2] → ✕ Deny   (KEY: rules miss it)
   ↺ Reset

6. 🎯 DUAL STRIKE    → Two zones hit simultaneously [P1] → ✕ Deny
```

**Incident priorities:**
- P1 Critical — ROGUE AGENT, GHOST CLONE, DUAL STRIKE (identity breach / healthy zone attack / burst rate)
- P2 High — PRIVILEGE HACK, PHANTOM RECON (out-of-zone pivot / ML-only quiet recon)
- No incident — FAULT REPAIR (all ALLOW, legitimate)

---

*TARE AEGIS-ID — Demo Presentation Script v3.3*
*Energy & Utilities Security Platform — Internal Use Only*
*Updated: March 2026*
