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
            # Fallback vote — never crash the tick loop
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
        critical = [c for c in state["civilians"] if c["status"] == "critical" and c["health"] > 0]
        stable   = [c for c in state["civilians"] if c["status"] == "stable"   and c["health"] > 0]
        dead     = [c for c in state["civilians"] if c["health"] <= 0]

        collapsed_cells = [(r,c) for r in range(10) for c in range(10) if state["grid"][r][c] == 1]
        fire_cells      = [(r,c) for r in range(10) for c in range(10) if state["grid"][r][c] == 2]
        cache_cells     = [(r,c) for r in range(10) for c in range(10) if state["grid"][r][c] == 4]

        def zone(pos):
            return f"{chr(65+pos[1])}{pos[0]}"

        crit_str = ", ".join([f"Civilian {c['id']} at {zone(c['pos'])} (health {c['health']})" for c in critical]) or "none"
        stable_str = ", ".join([f"Civilian {c['id']} at {zone(c['pos'])} (health {c['health']})" for c in stable]) or "none"
        
        display_name = state.get("display_name", state.get("name", "Unknown Scenario"))

        return f"""SCENARIO: {display_name}
TICK {state['tick']} DISASTER STATE:

Critical civilians: {crit_str}
Stable civilians: {stable_str}
Dead: {len(dead)}

Resources remaining (in HQ):
- Medical teams: {state['resources']['medical_teams']}
- Rescue units: {state['resources']['rescue_units']}
- Supply caches (ready to drop): {state['resources']['supply_caches']}

GRID LANDMARKS:
- Collapsed zones: {[zone(list(p)) for p in collapsed_cells] or 'none'}
- Fire zones: {[zone(list(p)) for p in fire_cells] or 'none'}
- Resource Caches (on the ground): {[zone(list(p)) for p in cache_cells] or 'none'}
- Active units deployed: {len(state['active_units'])}

GRID VALUE LEGEND:
0=empty, 1=collapsed, 2=fire, 3=civilian, 4=resource cache, 5=active unit

You must respond with ONLY a JSON object, no other text:
{{
  "proposed_action": "dispatch_medical" | "dispatch_rescue" | "dispatch_supply" | "hold",
  "target_zone": "A0" to "J9" or null,
  "target_civilian_id": number or null,
  "reasoning": "one sentence explanation",
  "priority_score": 0.0 to 1.0
}}"""

    def _parse_response(self, text: str, tick: int) -> dict:
        # Extract JSON from response
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if not match:
            # Try to see if it's just raw JSON without markdown
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
