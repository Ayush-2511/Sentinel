"""
SENTINEL — City Engine
Sector-based simulation engine with dynamic fire spread.
Each tick: fire grows + spreads to neighbors, civilians hurt by fire, resources stabilize.
"""

import copy
import random


class CityEngine:

    def tick(self, state: dict) -> dict:
        """Advance simulation by one tick."""
        state = copy.deepcopy(state)
        state["tick"] += 1
        
        # Initialize global intel feeds if missing
        if "intel_feed" not in state:
            state["intel_feed"] = []

        sectors = state["sectors"]
        epicenter = state.get("epicenter")

        # ── Phase 0: Seismic Shockwaves (Transient) ──
        if epicenter and state["tick"] <= epicenter.get("duration", 0):
            self._apply_seismic_force(sectors, epicenter, state["tick"])

        # ── Phase 1: Fire spread between adjacent sectors ──
        self._spread_fire(sectors)

        # ── Phase 2: Per-sector simulation ──
        for sector in sectors:
            # Initialize Intel Signals if missing
            if "intel_signals" not in sector:
                sector["intel_signals"] = {
                    "sos_count": 0,
                    "news_confirmed": False,
                    "infrastructure_alert": sector["infrastructure"] != "intact"
                }
            
            # Auto-update infrastructure alert signal
            sector["intel_signals"]["infrastructure_alert"] = sector["infrastructure"] != "intact"
            
            # Derive confidence tier for this tick
            sector["_confidence_tier"] = self._derive_confidence(sector)

            # Compute Zone Risk Index (0.0 – 1.0)
            # A normalized composite score used by agents to rank sectors by urgency.
            sector["risk_index"] = self._compute_risk_index(sector)
            
            fire = sector.get("fire_intensity", 0.0)

            # Fire grows each tick in burning sectors
            if fire > 0:
                sector["fire_intensity"] = min(1.0, fire + 0.03)
                if "fire" not in sector["hazards"]:
                    sector["hazards"].append("fire")
                # Fire damages infrastructure
                if fire > 0.5 and sector["infrastructure"] == "intact":
                    sector["infrastructure"] = "damaged"
                if fire > 0.8 and sector["infrastructure"] == "damaged":
                    sector["infrastructure"] = "destroyed"

            # Fire hurts civilians: more intense fire = more casualties
            if fire > 0 and sector["civilians"]["stable"] > 0:
                # Casualties proportional to fire intensity
                casualties = max(1, int(fire * 4))
                casualties = min(casualties, sector["civilians"]["stable"])
                sector["civilians"]["stable"] -= casualties
                sector["civilians"]["critical"] += casualties

            # Fire suppression: supply caches (primary) and rescue units (secondary)
            fire_fighting_power = 0
            if sector["resources_deployed"]["supply_caches"] > 0:
                fire_fighting_power += 0.15
            if sector["resources_deployed"]["rescue_units"] > 0:
                fire_fighting_power += 0.05
            
            # If the area is cleared of vulnerable civilians, decay is very slow (0.01)
            is_cleared = sector["civilians"]["critical"] == 0 and sector["civilians"]["stable"] == 0
            if is_cleared and fire > 0:
                fire_fighting_power += 0.01
            
            if fire_fighting_power > 0 and fire > 0:
                # Actual suppression logic
                reduction = fire_fighting_power 
                sector["fire_intensity"] = max(0, sector["fire_intensity"] - reduction)
                if sector["fire_intensity"] <= 0:
                    sector["hazards"] = [h for h in sector["hazards"] if h != "fire"]
                    sector["fire_intensity"] = 0

            # Medical teams stabilize critical civilians
            if sector["resources_deployed"]["medical_teams"] > 0:
                stabilized = min(sector["civilians"]["critical"], 3)
                sector["civilians"]["critical"] -= stabilized
                sector["civilians"]["stable"] += stabilized

            # No medical = critical worsen (die)
            if sector["resources_deployed"]["medical_teams"] == 0 and sector["civilians"]["critical"] > 0:
                dying = max(1, sector["civilians"]["critical"] // 4)
                sector["civilians"]["critical"] = max(0, sector["civilians"]["critical"] - dying)
                sector["civilians"]["total"] = max(0, sector["civilians"]["total"] - dying)

            # Rescue units help with structural collapse
            if sector["resources_deployed"]["rescue_units"] > 0 and "structural_collapse" in sector["hazards"]:
                rescued = min(sector["civilians"]["stable"], 4)
                sector["civilians"]["stable"] -= rescued
                sector["civilians"]["rescued"] += rescued
                if state["tick"] % 3 == 0:
                    sector["hazards"] = [h for h in sector["hazards"] if h != "structural_collapse"]

            # Compute per-sector spread rate for AI context
            sector["fire_spread_rate"] = round(self._spread_rate(sector, sectors), 2)

            # Recompute severity + color
            sector["severity_score"] = self._severity(sector)
            sector["color"] = self._color(sector)

        # Recompute global totals
        state["total_civilians"] = self._total_civilians(sectors)
        alive = state["total_civilians"]["critical"] + state["total_civilians"]["stable"] + state["total_civilians"]["rescued"]
        total = state["total_civilians"]["total"]
        state["survival_rate"] = round(alive / max(total, 1), 2)

        return state

    def _spread_fire(self, sectors):
        """Fire spreads from burning sectors to adjacent ones (by row/col proximity)."""
        new_fires = []
        for sector in sectors:
            fire = sector.get("fire_intensity", 0.0)
            if fire < 0.5:
                continue  # Fire needs to be significant to jump sectors

            # Find adjacent sectors (differ by 1 in row OR col, not both)
            for other in sectors:
                if other["id"] == sector["id"]:
                    continue
                dr = abs(other["row"] - sector["row"])
                dc = abs(other["col"] - sector["col"])
                if (dr + dc) == 1:  # Adjacent (not diagonal)
                    other_fire = other.get("fire_intensity", 0.0)
                    if other_fire == 0:
                        # NEW: Strict Containment (1-2% spread rate if contained)
                        # cont = 0.15 if units are present, combined with 0.06 base = ~0.9% max
                        cont = 0.15 if sum(sector["resources_deployed"].values()) > 0 else 0.8
                        
                        # Base spread probability lowered from 0.08 to 0.06
                        if random.random() < (fire * 0.06 * cont):
                            new_fires.append((other["id"], fire * 0.15))

        for sector_id, intensity in new_fires:
            s = next((s for s in sectors if s["id"] == sector_id), None)
            if s:
                s["fire_intensity"] = intensity
                if "fire" not in s["hazards"]:
                    s["hazards"].append("fire")

    def _spread_rate(self, sector, all_sectors):
        """Compute how fast fire is spreading toward this sector."""
        fire = sector.get("fire_intensity", 0.0)
        if fire > 0:
            return fire * 0.1  # Already burning, report growth rate

        # Check if any neighbor is burning
        threat = 0.0
        for other in all_sectors:
            if other["id"] == sector["id"]:
                continue
            dr = abs(other["row"] - sector["row"])
            dc = abs(other["col"] - sector["col"])
            if (dr + dc) == 1:
                other_fire = other.get("fire_intensity", 0.0)
                # Apply containment factor to threat awareness
                cont = 0.3 if sum(other["resources_deployed"].values()) > 0 else 1.0
                threat += (other_fire * 0.15 * cont)
        return threat

    def execute_action(self, state: dict, action: str, target_sector_id: str) -> dict:
        """Execute the winning agent vote on the city."""
        state = copy.deepcopy(state)

        if action == "hold" or not target_sector_id:
            return state

        sector = next((s for s in state["sectors"] if s["id"] == target_sector_id), None)
        if not sector:
            return state

        res = state["global_resources"]

        if action == "dispatch_medical" and res["medical_teams"] > 0:
            res["medical_teams"] -= 1
            sector["resources_deployed"]["medical_teams"] += 1

        elif action == "dispatch_rescue" and res["rescue_units"] > 0:
            res["rescue_units"] -= 1
            sector["resources_deployed"]["rescue_units"] += 1
            if sector["infrastructure"] == "destroyed":
                sector["infrastructure"] = "damaged"
            elif sector["infrastructure"] == "damaged":
                sector["infrastructure"] = "intact"

        elif action == "dispatch_supply" and res["supply_caches"] > 0:
            res["supply_caches"] -= 1
            sector["resources_deployed"]["supply_caches"] += 1
            # Supplies also fight fire if active
            if sector.get("fire_intensity", 0) > 0:
                sector["fire_intensity"] = max(0, sector["fire_intensity"] - 0.3)
                if sector["fire_intensity"] <= 0:
                    sector["hazards"] = [h for h in sector["hazards"] if h != "fire"]
                    sector["fire_intensity"] = 0
            else:
                # No fire = supplies stabilize civilians
                boosted = min(sector["civilians"]["critical"], 5)
                sector["civilians"]["critical"] -= boosted
                sector["civilians"]["stable"] += boosted

        # Recompute after action
        sector["severity_score"] = self._severity(sector)
        sector["color"] = self._color(sector)

        return state

    def is_simulation_over(self, state: dict) -> tuple:
        """Check if the simulation should end."""
        total = state["total_civilians"]
        if total["critical"] == 0 and total["stable"] == 0:
            return True, "MISSION COMPLETE: ALL CIVILIANS SECURED"
        
        # New Condition: Global Severity below 6%
        sectors = state["sectors"]
        avg_severity = sum(s["severity_score"] for s in sectors) / len(sectors)
        if avg_severity < 0.06:
            return True, "MISSION SUCCESS: DISASTER CONTAINED (Severity < 6%)"

        res = state["global_resources"]
        if res["medical_teams"] <= 0 and res["rescue_units"] <= 0 and res["supply_caches"] <= 0:
            any_deployed = any(
                any(v > 0 for v in s["resources_deployed"].values())
                for s in sectors
            )
            if not any_deployed:
                return True, "MISSION FAILED: RESOURCES EXHAUSTED"
        return False, ""

    # ── Internal helpers ──

    def _compute_risk_index(self, sector) -> float:
        """
        Zone Risk Index (0.0 – 1.0): A 3-factor composite urgency score.

        Factor 1 — Civilian Factor (weight 0.45):
            Ratio of critical civilians to total. Peaks at 1.0 when everyone is critical.

        Factor 2 — Hazard Factor (weight 0.35):
            Combines fire intensity and infrastructure damage level.

        Factor 3 — Resource Coverage Deficit (weight 0.20):
            Inverse of current unit presence. High score = no units deployed yet.
        """
        civ   = sector["civilians"]
        total = max(civ.get("total", 1), 1)
        fire  = sector.get("fire_intensity", 0.0)
        infra = sector.get("infrastructure", "intact")
        dep   = sum(sector.get("resources_deployed", {}).values())

        # Factor 1: Civilian criticality ratio
        civilian_factor = civ.get("critical", 0) / total

        # Factor 2: Combined hazard (fire + infrastructure damage)
        infra_score = {"intact": 0.0, "damaged": 0.5, "destroyed": 1.0}.get(infra, 0.0)
        hazard_factor = min(1.0, (fire * 0.7) + (infra_score * 0.3))

        # Factor 3: Resource coverage deficit (no units = max urgency)
        resource_factor = 1.0 if dep == 0 else max(0.0, 1.0 - (dep * 0.25))

        risk = (civilian_factor * 0.45) + (hazard_factor * 0.35) + (resource_factor * 0.20)
        return round(min(1.0, risk), 3)

    def _derive_confidence(self, sector) -> str:
        """Determines the surety level of a disaster based on ground signals."""
        signals = sector.get("intel_signals", {})
        sos = signals.get("sos_count", 0)
        news = signals.get("news_confirmed", False)
        infra = signals.get("infrastructure_alert", False)
        
        # HIGH: Verified by multi-factor (News + SOS + Power/Infra failure)
        # OR confirmed by a physical probe unit (Escalation)
        if sector.get("_probe_verified", False):
            return "HIGH"
            
        if news and (sos > 5 or infra):
            return "HIGH"
            
        # MEDIUM: News confirmed OR significant citizen reports
        if news or sos >= 10:
            return "MEDIUM"
            
        # LOW: Sparse reports or no news (Unverified Rumor)
        if sos > 0 or infra:
            return "LOW"
            
        return "LOW"

    def _severity(self, sector) -> float:
        civ = sector["civilians"]
        total = max(civ["total"], 1)
        score = (civ["critical"] / total) * 0.5
        fire = sector.get("fire_intensity", 0.0)
        score += fire * 0.3  # Fire intensity directly affects severity
        score += len(sector["hazards"]) * 0.08
        if sector["infrastructure"] == "destroyed":
            score += 0.15
        if sector["infrastructure"] == "damaged":
            score += 0.07
        return round(min(1.0, score), 3)

    def _color(self, sector) -> str:
        severity = sector["severity_score"]
        fire = sector.get("fire_intensity", 0.0)
        infra = sector["infrastructure"]

        if infra == "destroyed":
            return "#3D1A0A"
        if fire > 0.6:
            return "#5C1010"  # Bright fire red
        if fire > 0.3:
            return "#4A1E0A"  # Amber fire
        if severity >= 0.7:
            return "#2D0A15"
        if severity >= 0.4:
            return "#251800"
        if severity > 0.05:
            return "#0A2010"
        return "#0A1520"

    def _apply_seismic_force(self, sectors, epicenter, tick):
        """Apply dynamic damage based on proximity to epicenter during the quake (transient)."""
        epi_lat = epicenter["lat"]
        epi_lng = epicenter["lng"]
        mag = epicenter["magnitude"]
        duration = epicenter["duration"]

        # Time decay: shaking is strongest at the start and tapers off
        time_factor = max(0.1, (duration - tick + 1) / duration)

        for sector in sectors:
            # Calculate distance (simple Euclidean for simulation speeds)
            # Find center of polygon
            poly = sector["polygon"]
            lat_sum = sum(p[0] for p in poly)
            lng_sum = sum(p[1] for p in poly)
            s_lat = lat_sum / len(poly)
            s_lng = lng_sum / len(poly)

            # Distance in "degrees" (approximate for Lucknow)
            dist = max(0.005, ((s_lat - epi_lat)**2 + (s_lng - epi_lng)**2)**0.5)
            
            # Recalibrated Force Table
            # Higher base sensitivity for global attenuation
            force = (mag * 0.02 * time_factor) / (dist * 12.0)
            
            # ── 1. Infrastructure Damage (Lower thresholds for global effect) ──
            if force > 0.15 and sector["infrastructure"] == "intact":
                if random.random() < force * 0.4:
                    sector["infrastructure"] = "damaged"
            if force > 0.5 and sector["infrastructure"] == "damaged":
                if random.random() < force * 0.2:
                    sector["infrastructure"] = "destroyed"
            
            # ── 2. Structural Collapse Hazards ──
            if sector["infrastructure"] != "intact" and "structural_collapse" not in sector["hazards"]:
                if random.random() < force * 0.4:
                    sector["hazards"].append("structural_collapse")

            # ── 3. Casualties (Stable -> Critical) ──
            if sector["civilians"]["stable"] > 0:
                # Up to 15% of stable civilians become critical per tick near the epicenter
                base_casualty_rate = 0.15 * force
                casualties = int(sector["civilians"]["stable"] * base_casualty_rate)
                if casualties == 0 and random.random() < base_casualty_rate:
                    casualties = 1
                
                casualties = min(casualties, sector["civilians"]["stable"])
                sector["civilians"]["stable"] -= casualties
                sector["civilians"]["critical"] += casualties

            # ── 4. Secondary Fires (Broken Gas/Electric) ──
            # Lower ignition chance (2% max) as requested
            if "fire" not in sector["hazards"] and sector["infrastructure"] != "intact":
                fire_prob = min(0.02, force * 0.05)
                if random.random() < fire_prob:
                    sector["hazards"].append("fire")
                    sector["fire_intensity"] = 0.2

    def _total_civilians(self, sectors) -> dict:
        totals = {"total": 0, "critical": 0, "stable": 0, "rescued": 0}
        for s in sectors:
            for k in totals:
                totals[k] += s["civilians"].get(k, 0)
        return totals
