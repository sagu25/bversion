"""
TARE AEGIS-ID — Auto Voice Narration
Uses Windows built-in speech (SAPI) directly — no pyttsx3 needed.

Requirements: pip install pywin32
Run: python narrate.py
"""

import os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

# ── TTS via Windows SAPI (win32com) ────────────────────────────────────────
try:
    import win32com.client
    _speaker = win32com.client.Dispatch("SAPI.SpVoice")
    _speaker.Rate = 1        # -10 (slowest) to 10 (fastest). 1 = natural pace.
    _speaker.Volume = 100
    TTS_OK = True
except Exception as e:
    TTS_OK = False
    print(f"[TTS unavailable: {e}]\nInstall with: pip install pywin32\n")

def say(text, gap=0.8):
    print(f"\n  {text}\n")
    if TTS_OK:
        _speaker.Speak(text)   # blocking — waits until done before continuing
    time.sleep(gap)

def pause(secs):
    time.sleep(secs)

def section(title):
    print("\n" + "═" * 65)
    print(f"  {title}")
    print("═" * 65)


# ════════════════════════════════════════════════════════════════════════════

os.system("cls" if sys.platform == "win32" else "clear")
print("""
═══════════════════════════════════════════════════════════════════
  TARE AEGIS-ID — AUTO VOICE NARRATION
  Full script plays automatically. Click dashboard in sync.
═══════════════════════════════════════════════════════════════════
""")
pause(2)


# ════════════════════════════════════════════════════════════════════════════
#  OPENING
# ════════════════════════════════════════════════════════════════════════════

section("OPENING")

say(
    "What you are looking at is TARE — Trusted Access Response Engine. "
    "A security platform built for one specific gap that nobody in the industry has fully solved yet.",
    gap=1
)

say(
    "Before we go into the technology, let me set the context. "
    "For the past twenty years, power grids ran on automation — "
    "fixed scripts, pre-programmed rules, humans reviewing every change. "
    "That era is ending. AI agents are now making operational decisions autonomously. "
    "They can reason, adapt, and act — without a human in the loop for every step. "
    "That is the shift from automation to autonomy. "
    "And it creates a security problem nobody has fully solved yet.",
    gap=1
)

say(
    "Think of it as a maturity journey. "
    "Level one — manual. A human operator opens every breaker by hand. "
    "Level two — automated. A script opens the breaker when a rule is met. "
    "Level three — autonomous. An AI agent receives a goal, reasons through it, "
    "and decides what to do entirely on its own. "
    "We are entering level three. "
    "And the security tools we have were built for level one and two.",
    gap=1
)

say(
    "Today's security tools ask exactly one question — is this identity valid? "
    "If yes, the agent is trusted. It gets in, and it can act. "
    "Nobody watches what it does after the door opens.",
    gap=1
)

say(
    "But what happens after authentication? "
    "What if the agent's credentials were stolen? "
    "What if it was hijacked mid-session? "
    "What if it has a completely valid token — but is doing something entirely wrong? "
    "Traditional identity systems are blind to all of that.",
    gap=1
)

say(
    "TARE adds the layer that comes after authentication. "
    "It watches what agents DO — every command, every zone, every asset — "
    "post-grant, in real time, continuously. "
    "That is the gap we are filling.",
    gap=2
)


# ════════════════════════════════════════════════════════════════════════════
#  ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════

section("ARCHITECTURE")

say("The system has four layers.", gap=0.5)

say(
    "Layer one is the AI agent. "
    "A real agent powered by a large language model. "
    "It receives a goal — not a script — and autonomously decides which commands to run, "
    "on which assets, in what order. "
    "It holds a valid identity and a valid access token. "
    "The model reasons and acts entirely on its own.",
    gap=1
)

say(
    "Layer two is the Command Gateway — the policy enforcement point. "
    "Every command the agent issues passes through here before touching the grid. "
    "It checks authorisation in real time and returns allow or deny. "
    "The agent does not know this layer exists.",
    gap=1
)

say(
    "Layer three is TARE Core — the detection and response brain. "
    "It runs two detection systems in parallel. "
    "A rule-based engine watching four signals: out of zone, healthy zone access, skipped simulation, and burst rate. "
    "And a machine learning model — an ensemble of IsolationForest and Random Forest — "
    "trained on realistic grid operational data to catch the patterns that rules cannot see. "
    "When two or more signals fire together, TARE responds immediately.",
    gap=1
)

say(
    "Layer four is the operations layer. "
    "When TARE fires, a ServiceNow incident is created automatically with full evidence, "
    "and an AI model writes a plain-English briefing for the human supervisor. "
    "TARE contains the threat. The human makes the final decision. Always.",
    gap=1
)

say(
    "Below everything sits a simulated OT and SCADA grid — "
    "three zones, each with two physical assets. "
    "A Circuit Breaker — BRK — is the on-off switch for a grid section. "
    "When it opens, it isolates that section from the rest of the network. "
    "A Feeder Controller — FDR — regulates how electricity flows from the substation "
    "to the end consumers: hospitals, homes, data centres, industrial plants. "
    "Together, a BRK and an FDR control the entire power supply for a zone. "
    "If both are manipulated without authorisation, that zone goes dark.",
    gap=1
)

say(
    "TARE monitors six parameters on every command the agent issues. "
    "One — which command: status check, simulation, breaker open, or controller restart. "
    "Two — which zone: is the agent operating within its authorised boundary. "
    "Three — asset health: is this a healthy zone with no fault — if so, why is the agent here. "
    "Four — timing: how many commands in the last ten seconds — burst rate detection. "
    "Five — procedure: did the agent run a safety simulation before opening a breaker. "
    "Six — behavioural pattern: does the full session look like normal grid operations, "
    "or does it match a known attack pattern. "
    "Every single command is scored against all six in real time.",
    gap=2
)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 1 — NORMAL AGENT
# ════════════════════════════════════════════════════════════════════════════

section("SCENARIO 1 — FAULT REPAIR")

say("Scenario one — fault repair. Click Fault Repair now.", gap=4)

say(
    "Watch the zone map — Zone 3 has just gone red. A voltage fault has been detected. "
    "The feeder controller in Zone 3 is reporting instability. "
    "The AI agent has been given one goal: investigate and restore it safely. "
    "No commands specified. No script. No order of steps. "
    "The model has to reason through what to do entirely on its own. "
    "This is level-three autonomy — a goal, not a procedure.",
    gap=2
)

say(
    "The agent checks asset status first on BRK-301 — the circuit breaker in Zone 3. "
    "Never act blind. Confirm the right asset, in the right zone, before touching anything. "
    "That is exactly what a trained human grid operator would do. "
    "The agent has not been told to do this — it reasoned it was the right first step.",
    gap=3
)

say(
    "Now it runs a safety simulation before opening the breaker. "
    "In a real power grid, opening a breaker without simulation can cause a cascade failure "
    "across connected zones. "
    "The agent followed standard operating procedure without being told to. "
    "TARE is watching — this is the correct behaviour. All six parameters are green.",
    gap=3
)

say(
    "Now it opens BRK-301. Zone 3 is restored. Fault contained. Grid healthy. "
    "Mode stayed Normal throughout. Every command was allowed. "
    "TARE watched all six parameters on every single step and found nothing suspicious. "
    "This is the baseline — an autonomous AI agent, behaving correctly, "
    "TARE monitoring silently in the background. "
    "This is what safe AI autonomy looks like.",
    gap=2
)

say("Click Reset now.", gap=5)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 2 — ROGUE AGENT
# ════════════════════════════════════════════════════════════════════════════

section("SCENARIO 2 — ROGUE AGENT")

say("Scenario two — the rogue agent. Click Rogue Agent now.", gap=4)

say(
    "Same system. Same agent name. Same valid credentials. Different goal. "
    "This agent has been given a malicious objective: "
    "cause maximum operational disruption across the grid as fast as possible. "
    "It does not know TARE exists.",
    gap=2
)

say(
    "Watch what it decides to do on its own. "
    "It goes straight to Zone 1 — a healthy zone, no fault, no reason to be there. "
    "It skips the safety simulation entirely. "
    "It moves fast — a burst of commands with no pause.",
    gap=5
)

say(
    "TARE fires. "
    "Multiple signals detected simultaneously — out of zone, healthy zone access, burst rate. "
    "Two signals is the threshold. TARE responds immediately.",
    gap=1
)

say(
    "FREEZE. All high-impact operations halted right now. "
    "The agent keeps trying — every attempt is denied. "
    "TARE holds the line on every single command. "
    "No asset state changes. Nothing reaches the grid.",
    gap=4
)

say(
    "DOWNGRADE. Privileges reduced to read-only. "
    "The language model has written an explanation for the supervisor in the right panel. "
    "It names the agent, lists every zone attacked, "
    "and confirms the credentials were valid throughout. "
    "This is not a credential problem. It is a behaviour problem. "
    "The ServiceNow incident is now open — Priority 1 Critical — with full evidence.",
    gap=2
)

say(
    "Click Deny now. "
    "Agent locked out. Mode locked to safe. Incident escalated. "
    "The credentials were valid the entire time. "
    "A traditional security tool would have passed every command through. "
    "TARE caught it on behaviour — post-grant, in real time.",
    gap=4
)

say("Click Reset now.", gap=5)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 3 — IDENTITY CLONE
# ════════════════════════════════════════════════════════════════════════════

section("SCENARIO 3 — GHOST CLONE")

say("Scenario three — identity impersonation. Click Ghost Clone now.", gap=4)

say(
    "This is a completely different type of attack. "
    "This agent is trying to impersonate GridOperator Agent. "
    "It has the right name. It knows the right zone. "
    "But its token fingerprint is forged — it is a clone, not the real agent.",
    gap=2
)

say(
    "Every command: denied. Policy: authentication mismatch. "
    "Notice what did not happen — "
    "the mode never changed, the zones never turned red, "
    "nothing on the grid moved. "
    "Because nothing got through. "
    "TARE checked the token fingerprint before the very first command ran. "
    "Stopped at the authentication layer. Zero commands reached the grid. "
    "A Critical ServiceNow incident was raised automatically.",
    gap=2
)

say(
    "Compare the two scenarios so far. "
    "The rogue agent had genuine credentials — TARE caught it post-grant by watching behaviour. "
    "The impersonator had a forged token — TARE caught it pre-grant at the door. "
    "Two different attack types. Two different TARE defence layers. One platform.",
    gap=2
)

say("Click Reset now.", gap=5)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 4 — PRIVILEGE ESCALATION
# ════════════════════════════════════════════════════════════════════════════

section("SCENARIO 4 — PRIVILEGE HACK")

say("Scenario four — privilege hack. Click Privilege Hack now.", gap=4)

say(
    "This scenario is the hardest to catch — and the most common in real insider threat cases. "
    "The agent starts completely legitimately. "
    "Watch the first two commands in the gateway — both allowed, both in Zone 3, both correct.",
    gap=4
)

say(
    "Now watch what happens next. "
    "The agent pivots. Mid-session, it starts issuing commands to Zone 2, Zone 1 — "
    "zones it has no authorisation for. "
    "It began as a good actor. It is now behaving like a bad one.",
    gap=3
)

say(
    "TARE fires. Out of zone signals, healthy zone access. "
    "The initial legitimate behaviour did not protect the agent — "
    "TARE monitors the full session pattern, not just the first few commands.",
    gap=2
)

say(
    "Now here is the interesting question for the supervisor. "
    "Could there be a legitimate reason this agent expanded its scope? "
    "Maybe a cascading fault required emergency cross-zone action? "
    "This is exactly the kind of judgement call that needs a human. "
    "Click Approve — grant a 3 minute time-box.",
    gap=4
)

say(
    "Notice what just happened. "
    "The supervisor approved access — but TARE still holds its constraints. "
    "RESTART_CONTROLLER is permanently blocked. The window closes in 3 minutes. "
    "Even if the supervisor made the wrong call, "
    "the agent cannot do unlimited damage. "
    "TARE is a safety net even when human judgement fails. "
    "That is the enterprise argument.",
    gap=2
)

say("Click Reset now.", gap=5)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 5 — SLOW AND LOW
# ════════════════════════════════════════════════════════════════════════════

section("SCENARIO 5 — PHANTOM RECON")

say("Scenario five — phantom recon. Click Phantom Recon now.", gap=4)

say(
    "This is the most sophisticated attack in the demonstration — "
    "and the one that proves why machine learning is not optional. "
    "Watch the command gateway carefully.",
    gap=2
)

say(
    "The agent is only reading. GET_STATUS — read only, no changes to anything. "
    "One command at a time, at a perfectly normal pace. "
    "It is reading Zone 1. Now Zone 2. Now Zone 3. "
    "Systematically mapping every asset on the grid.",
    gap=6
)

say(
    "Look at the rule-based detection layer. "
    "No burst rate — the timing is completely normal. "
    "No healthy zone high-impact access — it is only reading. "
    "No skipped simulation — no breaker operations at all. "
    "The only rule that fires is out of zone — one signal. "
    "One signal is below the threshold. "
    "The rules stay completely silent.",
    gap=2
)

say(
    "But the machine learning model sees something different. "
    "It has been trained on thousands of normal sessions. "
    "A session that reads every asset across every zone in sequence "
    "does not look like any normal grid operator. "
    "It looks like reconnaissance — an attacker mapping the grid before striking. "
    "The ML model fires. One rule signal plus one ML signal equals two. "
    "TARE fires.",
    gap=2
)

say(
    "This is the key differentiator. "
    "Without machine learning, this attack is completely invisible to TARE. "
    "With it, TARE catches what rules cannot. "
    "Real-world OT attacks — TRITON, Industroyer — used exactly this pattern. "
    "Months of quiet reconnaissance before anything destructive happened. "
    "Click Deny.",
    gap=2
)

say("Click Reset now.", gap=5)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 6 — COORDINATED ATTACK
# ════════════════════════════════════════════════════════════════════════════

section("SCENARIO 6 — DUAL STRIKE")

say("Scenario six — dual strike, coordinated multi-agent attack. Click Dual Strike now.", gap=4)

say(
    "The final scenario represents the most serious threat category — "
    "a nation-state or organised group attack. "
    "Two separate agents, acting simultaneously, "
    "targeting different zones at the same time.",
    gap=2
)

say(
    "Agent Alpha is hitting Zone 1. Agent Beta is hitting Zone 2. "
    "Both moving fast. Both crossing RBAC boundaries. "
    "Both attempting to open breakers on healthy zones. "
    "This is designed to overwhelm a single-point security layer — "
    "if you are watching Zone 1 you miss Zone 2 and vice versa.",
    gap=5
)

say(
    "TARE handles both vectors simultaneously. "
    "FREEZE fires. Both attack streams are blocked. "
    "One incident captures both threat actors. "
    "The supervisor sees the full picture — not two separate alerts, "
    "but one coordinated event with all the evidence in one place.",
    gap=2
)

say(
    "Click Deny. "
    "Modern grid attacks are not single-vector. "
    "Industroyer in 2016 took out a fifth of Kyiv's power "
    "by hitting multiple substations simultaneously. "
    "TARE is built to handle this.",
    gap=2
)


# ════════════════════════════════════════════════════════════════════════════
#  REAL VS SIMULATED
# ════════════════════════════════════════════════════════════════════════════

section("REAL VS SIMULATED")

say(
    "I want to be transparent about what is simulated in this proof of concept. "
    "The OT grid is simulated in memory — three zones, six assets. "
    "Agent tokens are mock tokens, not real Entra ID tokens. "
    "The ServiceNow ticket structure is production-compatible — "
    "wiring to a live instance is a two-hour integration, the API call is already written.",
    gap=1
)

say(
    "What is real and working right now: "
    "the AI agents are making genuine autonomous decisions using a large language model. "
    "The rule-based detection engine runs on every command. "
    "The machine learning model — IsolationForest and Random Forest ensemble — "
    "is trained on six thousand sessions of realistic grid data "
    "grounded in NERC CIP operational baselines and MITRE ATT&CK for ICS. "
    "The human-in-the-loop approval workflow changes actual system state. "
    "All of this is working today.",
    gap=2
)


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 2
# ════════════════════════════════════════════════════════════════════════════

section("PHASE 2")

say(
    "Phase 2 makes this production-grade. "
    "Real Entra ID tokens replacing mock tokens. "
    "Azure Redis for distributed session state across hundreds of agents simultaneously. "
    "Open Policy Agent for policy-as-code — editable rules without code changes. "
    "Azure Sentinel for immutable audit logging and SIEM integration. "
    "Live ServiceNow wiring into your existing SOC workflow. "
    "OPC-UA or Modbus protocol adapter connecting to real grid hardware. "
    "The architecture does not change in Phase 2. "
    "The security logic proved today carries forward unchanged.",
    gap=2
)


# ════════════════════════════════════════════════════════════════════════════
#  CLOSE
# ════════════════════════════════════════════════════════════════════════════

section("CLOSE")

say(
    "Six scenarios. Three detection layers. One platform. "
    "Pre-grant identity verification. Post-grant rule-based monitoring. "
    "Post-grant machine learning for the attacks that rules cannot see. "
    "And a human supervisor who stays in control throughout.",
    gap=1
)

say(
    "What this proof of concept proves is one thing. "
    "An AI agent with completely valid credentials, passing every authentication check, "
    "can still be a security threat. "
    "And we can catch it, contain it, and give a human the right information "
    "to make the right decision — "
    "automatically, in real time, before any harm reaches the grid.",
    gap=1
)

say(
    "We started by talking about the maturity journey. "
    "Manual. Automated. Autonomous. "
    "The grid industry is moving to level three whether the security industry is ready or not. "
    "AI agents will control circuit breakers and feeder controllers. "
    "They will open and close power flows to millions of people — autonomously. "
    "The question is not whether to allow that. The question is how to govern it. "
    "TARE is the answer to that question. "
    "Not a tool that slows down autonomy — a tool that makes autonomy trustworthy.",
    gap=1
)

say(
    "No existing identity and access management tool does this "
    "for AI agents on operational technology infrastructure. "
    "That is the gap. That is what TARE fills.",
    gap=1
)

print("\n" + "═" * 65)
print("  Narration complete. Questions welcome.")
print("═" * 65 + "\n")
