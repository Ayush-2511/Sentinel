import os
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import json
import re

MODEL = "llama-3.3-70b-versatile"

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
                HumanMessage(content=prompt)
            ])
            return self._parse_response(response.content, state["tick"])
        except Exception as e:
            return {
                "agent": self.__class__.__name__.upper(),
                "proposed_action": "hold",
                "target_zone": None,
                "target_civilian_id": None,
                "reasoning": f"Agent error: {str(e)[:100]}",
                "priority_score": 0.0,
                "tick": state["tick"]
            }

    def _build_prompt(self, state: dict) -> str:
        """Build a clean, concise prompt with only unsaved civilian data."""
        
        # Only include unsaved, living civilians
        unsaved = [c for c in state["civilians"] if c["health"] > 0 and not c.get("saved")]
        saved = [c for c in state["civilians"] if c.get("saved")]
        dead = [c for c in state["civilians"] if c["health"] <= 0]
        
        # Build civilian status lines
        civ_lines = []
        for c in unsaved:
            hurt_rate = c.get("hurt_rate", 0)
            civ_lines.append(
                f"  - Civilian #{c['id']} at position [{c['pos'][0]},{c['pos'][1]}], "
                f"HP: {c['health']}, Status: {c['status']}, "
                f"Losing {hurt_rate} HP/tick"
            )
        
        civ_str = "\n".join(civ_lines) if civ_lines else "  None — all civilians accounted for"
        
        return f"""DISASTER SITUATION — Tick {state['tick']}

FIRE is spreading on a 10x10 grid. Civilians are losing health based on their proximity to fire.
Closer civilians lose health FASTER.

CIVILIANS STILL IN DANGER:
{civ_str}

ALREADY SAVED: {len(saved)} civilian(s)
DEAD: {len(dead)} civilian(s)

AVAILABLE RESOURCES:
- Medical teams: {state['resources']['medical_teams']} (use dispatch_medical to SAVE a civilian)
- Supply caches: {state['resources']['supply_caches']} (use dispatch_supply to extinguish fire)

RULES:
- dispatch_medical saves a civilian permanently (removes them from danger)
- dispatch_supply extinguishes fire in a 3x3 area around the worst blaze
- You MUST specify target_civilian_id when using dispatch_medical
- Choose the civilian who needs help MOST URGENTLY

Respond with ONLY this JSON:
{{
  "proposed_action": "dispatch_medical" | "dispatch_supply" | "hold",
  "target_civilian_id": <civilian id number or null>,
  "reasoning": "one sentence",
  "priority_score": 0.0 to 1.0
}}"""

    def _parse_response(self, text: str, tick: int) -> dict:
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if not match:
            try:
                data = json.loads(text)
            except:
                raise ValueError("No JSON found in response")
        else:
            data = json.loads(match.group())
            
        return {
            "agent": self.__class__.__name__.upper(),
            "proposed_action": data.get("proposed_action", "hold"),
            "target_zone": data.get("target_zone"),
            "target_civilian_id": data.get("target_civilian_id"),
            "reasoning": data.get("reasoning", "No reasoning provided"),
            "priority_score": float(data.get("priority_score", 0.0)),
            "tick": tick
        }
