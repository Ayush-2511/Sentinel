"""
SENTINEL — Base Agent
All agents inherit from this. Handles LLM communication and response parsing.
"""

import json
import re
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class BaseAgent:
    """All agents inherit from this. Do not instantiate directly."""

    SYSTEM_PROMPT = ""  # Override in subclass

    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=MODEL,
            temperature=0.3,
            max_tokens=300,
        )

    def vote(self, state: dict) -> dict:
        """Call the LLM and return a structured vote dict."""
        prompt = self._build_prompt(state)
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            return self._parse_response(response.content, state["tick"])
        except Exception as e:
            return {
                "agent": self.__class__.__name__.upper(),
                "proposed_action": "hold",
                "target_sector": None,
                "reasoning": f"Agent error: {str(e)[:100]}",
                "priority_score": 0.0,
                "tick": state["tick"],
            }

    def _build_prompt(self, state: dict) -> str:
        """Build a sector-based prompt for the LLM."""
        sectors = state["sectors"]

        sector_lines = []
        for s in sorted(sectors, key=lambda x: x["severity_score"], reverse=True):
            civ = s["civilians"]
            hazard_str = ", ".join(s["hazards"]) if s["hazards"] else "none"
            deployed_str = ", ".join(
                f"{v} {k.replace('_', ' ')}" for k, v in s["resources_deployed"].items() if v > 0
            ) or "none"
            fire_str = ""
            fire_i = s.get("fire_intensity", 0)
            spread = s.get("fire_spread_rate", 0)
            if fire_i > 0:
                fire_str = f" | FIRE: {fire_i:.0%} intensity"
            elif spread > 0:
                fire_str = f" | fire threat: {spread:.0%}"
            sector_lines.append(
                f"  {s['id']} ({s['name']}, {s['type']}): "
                f"{civ['critical']} critical / {civ['stable']} stable / {civ['rescued']} rescued "
                f"| infra: {s['infrastructure']} | hazards: {hazard_str} | deployed: {deployed_str} "
                f"| severity: {s['severity_score']:.2f}{fire_str}"
            )

        res = state["global_resources"]
        tc = state["total_civilians"]

        return f"""TICK {state['tick']} — {state.get('city_name', 'City')} DISASTER STATE

SECTORS BY SEVERITY:
{chr(10).join(sector_lines)}

GLOBAL RESOURCES AVAILABLE:
  Medical teams:  {res['medical_teams']} (saves critical civilians in a sector)
  Rescue units:   {res['rescue_units']} (clears collapse, rescues stable civilians, and provides secondary fire suppression)
  Supply caches:  {res['supply_caches']} (PRIMARY FIRE FIGHTING — strongly reduces fire intensity)

TOTALS: {tc['critical']} critical | {tc['stable']} stable | {tc['rescued']} rescued
SURVIVAL RATE: {state['survival_rate'] * 100:.0f}%

IMPORTANT: Fire spreads to adjacent sectors. Higher intensity = more casualties. Saving all civilians in a sector allows the area to be secured, causing fire to decay naturally.

Respond ONLY with this exact JSON, no other text:
{{
  "proposed_action": "dispatch_medical" | "dispatch_rescue" | "dispatch_supply" | "hold",
  "target_sector": sector ID like "A1" or "B2" or null,
  "reasoning": "one sentence, max 20 words",
  "priority_score": 0.0 to 1.0
}}"""

    def _parse_response(self, text: str, tick: int) -> dict:
        """Extract structured vote from LLM response text."""
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if not match:
            try:
                data = json.loads(text)
            except Exception:
                raise ValueError("No JSON found in response")
        else:
            data = json.loads(match.group())

        return {
            "agent": self.__class__.__name__.upper(),
            "proposed_action": data.get("proposed_action", "hold"),
            "target_sector": data.get("target_sector"),
            "reasoning": data.get("reasoning", "No reasoning provided"),
            "priority_score": float(data.get("priority_score", 0.0)),
            "tick": tick,
        }
