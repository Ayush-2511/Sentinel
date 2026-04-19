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

    def vote(self, state: dict, previous_votes: list = None) -> dict:
        """Query LLM for a vote on this city state."""
        try:
            prompt = self._build_prompt(state, previous_votes)
            
            # Prepend common mission context to system prompt
            mission_context = (
                "ACTION GUIDE:\n"
                "- dispatch_medical: Stabilizes 'Critical' civilians (C). Most effective on medical emergencies.\n"
                "- dispatch_rescue: Required for 'Collapsed' hazards. Extracts civilians. Provides secondary fire aid.\n"
                "- dispatch_supply: PRIMARY FIRE SUPPRESSION. Aggressively lowers fire intensity.\n"
            )
            
            response = self.llm.invoke([
                SystemMessage(content=f"{self.SYSTEM_PROMPT}\n\n{mission_context}"),
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

    def _build_prompt(self, state: dict, previous_votes: list = None) -> str:
        """Build a high-density, filtered prompt for the LLM."""
        sectors = state["sectors"]
        
        # Filter for Impacted Sectors only (Severity > 1% or active hazards/units)
        active_sectors = []
        stable_count = 0
        for s in sectors:
            is_active = (
                s["severity_score"] > 0.01 or 
                s.get("fire_intensity", 0) > 0 or 
                any(v > 0 for v in s["resources_deployed"].values())
            )
            if is_active:
                active_sectors.append(s)
            else:
                stable_count += 1

        sector_lines = []
        for s in sorted(active_sectors, key=lambda x: x["severity_score"], reverse=True):
            civ = s["civilians"]
            hz = ",".join(s["hazards"]) if s["hazards"] else "-"
            dep = ",".join(f"{v}{k[0].upper()}" for k, v in s["resources_deployed"].items() if v > 0) or "-"
            
            fire_i = s.get("fire_intensity", 0)
            f_str = f" 🔥{fire_i:.0%}" if fire_i > 0 else ""
            risk  = s.get("risk_index", 0.0)
            conf  = s.get("_confidence_tier", "LOW")
            
            # COMPACT FORMAT: ID (Name) [Crit/Stbl/Resc] | Infra | Hazards | Deployed | Sev | Risk | Conf
            sector_lines.append(
                f"  {s['id']} ({s['name']}): [{civ['critical']}C/{civ['stable']}S/{civ['rescued']}R] "
                f"| INF:{s['infrastructure'][:3]} | HZ:{hz} | DEP:{dep} | SEV:{s['severity_score']:.2f}{f_str}"
                f" | RISK:{risk:.2f} | CONF:{conf}"
            )

        res = state["global_resources"]
        tc = state["total_civilians"]

        return f"""TICK {state['tick']} — {state.get('city_name', 'City')} STATE
CITY STATUS:
- Survival: {state['survival_rate'] * 100:.1f}% | Availability: {res['medical_teams']}M, {res['rescue_units']}R, {res['supply_caches']}S
{f"⚠️ EPICENTER active (Dur: {state['epicenter']['duration'] - state['tick']} ticks)" if state.get("epicenter") and state["tick"] <= state["epicenter"]["duration"] else ""}

IMPACTED SECTORS:
{chr(10).join(sector_lines)}
{f"  (+ {stable_count} other sectors are INTACT and SECURE)" if stable_count > 0 else ""}

TOTALS: {tc['critical']}C | {tc['stable']}S | {tc['rescued']}R
SURVIVAL RATE: {state['survival_rate'] * 100:.0f}%

IMPORTANT: Fire spreads to adjacent sectors. ANY UNIT dispatched to a burning sector provides CONTAINMENT, reducing outward spread by 70%. Saving all civilians allows the area to be secured, causing fire to decay naturally even at 100% intensity.

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
