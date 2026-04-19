"""
SENTINEL — Event Engine
Triggers dynamic events (aftershock, fire spread, resource depletion) on sectors.
"""

import random
import copy


class EventEngine:

    def trigger(self, state: dict, event_name: str) -> dict:
        state = copy.deepcopy(state)
        active_sectors = [s for s in state["sectors"] if s["infrastructure"] != "destroyed"]

        if event_name == "aftershock":
            targets = random.sample(active_sectors, min(2, len(active_sectors)))
            for s in targets:
                if s["infrastructure"] == "intact":
                    s["infrastructure"] = "damaged"
                elif s["infrastructure"] == "damaged":
                    s["infrastructure"] = "destroyed"
                if "structural_collapse" not in s["hazards"]:
                    s["hazards"].append("structural_collapse")
                new_critical = random.randint(2, 5)
                s["civilians"]["critical"] = min(s["civilians"]["total"], s["civilians"]["critical"] + new_critical)
                s["civilians"]["stable"] = max(0, s["civilians"]["stable"] - new_critical)
                s["severity_score"] = self._severity(s)
                s["color"] = "#2D0A15"
            state["events"].append("aftershock")

        elif event_name == "fire_spread":
            targets = [s for s in active_sectors if "fire" not in s["hazards"]]
            if targets:
                t = random.choice(targets)
                t["hazards"].append("fire")
                t["severity_score"] = min(1.0, t["severity_score"] + 0.2)
                t["color"] = "#3D0A15"
            state["events"].append("fire_spread")

        elif event_name == "resource_depletion":
            deployed = [s for s in state["sectors"] if any(v > 0 for v in s["resources_deployed"].values())]
            if deployed:
                t = random.choice(deployed)
                for rtype in ["medical_teams", "rescue_units", "supply_caches"]:
                    if t["resources_deployed"][rtype] > 0:
                        t["resources_deployed"][rtype] -= 1
                        state["global_resources"][rtype] += 1
                        break
            state["events"].append("resource_depletion")

        return state

    def _severity(self, sector) -> float:
        civ = sector["civilians"]
        total = max(civ["total"], 1)
        score = (civ["critical"] / total) * 0.6
        score += len(sector["hazards"]) * 0.12
        if sector["infrastructure"] == "destroyed":
            score += 0.15
        if sector["infrastructure"] == "damaged":
            score += 0.07
        return round(min(1.0, score), 3)
