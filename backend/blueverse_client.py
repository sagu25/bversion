"""
BlueVerse Foundry — Agent API Client

Handles OAuth2 token acquisition and agent invocation.
All credentials and agent IDs are loaded from .env

Usage:
    from blueverse_client import BlueverseClient
    client = BlueverseClient()
    response = client.invoke("KORAL", "What telemetry have you observed?")
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ─── Agent config map (Space_name + flowId per agent) ────────────────────────
AGENT_CONFIG = {
    # Zone 3 — Reef
    "KORAL":    {"space": os.getenv("BV_AGENT_KORAL", ""),    "flow": os.getenv("BV_FLOW_KORAL", "")},
    "MAREA":    {"space": os.getenv("BV_AGENT_MAREA", ""),    "flow": os.getenv("BV_FLOW_MAREA", "")},
    "TASYA":    {"space": os.getenv("BV_AGENT_TASYA", ""),    "flow": os.getenv("BV_FLOW_TASYA", "")},
    "NEREUS":   {"space": os.getenv("BV_AGENT_NEREUS", ""),   "flow": os.getenv("BV_FLOW_NEREUS", "")},
    # Zone 2 — Shelf
    "ECHO":     {"space": os.getenv("BV_AGENT_ECHO", ""),     "flow": os.getenv("BV_FLOW_ECHO", "")},
    "SIMAR":    {"space": os.getenv("BV_AGENT_SIMAR", ""),    "flow": os.getenv("BV_FLOW_SIMAR", "")},
    "NAVIS":    {"space": os.getenv("BV_AGENT_NAVIS", ""),    "flow": os.getenv("BV_FLOW_NAVIS", "")},
    "RISKADOR": {"space": os.getenv("BV_AGENT_RISKADOR", ""), "flow": os.getenv("BV_FLOW_RISKADOR", "")},
    # Zone 1 — Trench
    "TRITON":   {"space": os.getenv("BV_AGENT_TRITON", ""),   "flow": os.getenv("BV_FLOW_TRITON", "")},
    "AEGIS":    {"space": os.getenv("BV_AGENT_AEGIS", ""),    "flow": os.getenv("BV_FLOW_AEGIS", "")},
    "TEMPEST":  {"space": os.getenv("BV_AGENT_TEMPEST", ""),  "flow": os.getenv("BV_FLOW_TEMPEST", "")},
    "LEVIER":   {"space": os.getenv("BV_AGENT_LEVIER", ""),   "flow": os.getenv("BV_FLOW_LEVIER", "")},
    # Zone 4
    "BARRIER":  {"space": os.getenv("BV_AGENT_BARRIER", ""),  "flow": os.getenv("BV_FLOW_BARRIER", "")},
}


class BlueverseClient:
    """
    OAuth2 client for BlueVerse Foundry agent API.
    Token is cached and refreshed automatically on expiry.
    """

    def __init__(self):
        self._token_url     = os.getenv("BLUEVERSE_TOKEN_URL", "")
        self._chat_url      = os.getenv("BLUEVERSE_CHAT_URL", "")
        self._client_id     = os.getenv("BLUEVERSE_CLIENT_ID", "")
        self._client_secret = os.getenv("BLUEVERSE_CLIENT_SECRET", "")
        self._verify_ssl    = os.getenv("BLUEVERSE_VERIFY_SSL", "true").lower() == "true"

        self._access_token  = None
        self._token_expiry  = 0

    # ── Token Management ──────────────────────────────────────────────────────

    def _get_token(self) -> str:
        """Return cached token or fetch a new one if expired."""
        if self._access_token and time.time() < self._token_expiry - 30:
            return self._access_token

        resp = requests.post(
            self._token_url,
            data={
                "grant_type":    "client_credentials",
                "client_id":     self._client_id,
                "client_secret": self._client_secret,
            },
            verify=self._verify_ssl,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)
        return self._access_token

    # ── Agent Invocation ──────────────────────────────────────────────────────

    def invoke(self, agent_name: str, message: str) -> str:
        """
        Send a message to a BlueVerse agent and return its response.

        agent_name : one of the 13 TARE agent names (e.g. "KORAL", "MAREA")
        message    : the prompt/question to send to the agent
        Returns    : agent response as string
        """
        config = AGENT_CONFIG.get(agent_name, {})
        space_name = config.get("space", "")
        flow_id    = config.get("flow", "")

        if not space_name:
            raise ValueError(f"No BlueVerse Space_name configured for {agent_name}. "
                             f"Set BV_AGENT_{agent_name} in .env")

        token = self._get_token()

        # Build request body matching BlueVerse chatservice API format
        body = {
            "query":      message,
            "Space_name": space_name,
        }
        if flow_id:
            body["flowId"] = flow_id

        resp = requests.post(
            self._chat_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json=body,
            verify=self._verify_ssl,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        result = (
            data.get("response")
            or data.get("content")
            or data.get("message")
            or data.get("answer")
            or data.get("output")
            or str(data)
        )
        print(f"[BlueVerse ✓] {agent_name} responded via GPT-4o mini")
        return result

    def invoke_safe(self, agent_name: str, message: str, fallback: str = "") -> str:
        """
        Same as invoke() but returns fallback string on any error.
        Use this in agent classes so a BlueVerse outage doesn't crash TARE.
        """
        try:
            return self.invoke(agent_name, message)
        except Exception as e:
            print(f"[BlueverseClient] {agent_name} invoke failed: {e}")
            return fallback


# ─── Singleton ────────────────────────────────────────────────────────────────
_client = None

def get_client() -> BlueverseClient:
    """Return shared BlueverseClient instance."""
    global _client
    if _client is None:
        _client = BlueverseClient()
    return _client
