# SENTINEL — MAP ARCHITECTURE GUIDE
> This file replaces the grid system described in BUILD_GUIDE.md.
> Read BUILD_GUIDE.md first for the overall project structure, team assignments, socket events, and setup.
> This file covers ONLY the changes introduced by switching from a 10x10 grid to a city map with sectors.
> After reading, update PROGRESS.md with new tasks.

---

## What Changed and Why

The original design tracked individual civilians on a 10x10 pixel grid. This is replaced with a **city map divided into named sectors**. Agents now dispatch help to entire sectors rather than individual coordinates.

**Why this is better:**
- More realistic — real disaster response operates at zone/sector level, not individual GPS coordinates
- Visually cleaner — judges see a city map, not a pixel grid
- Simpler agent prompts — "Sector B2 has 8 critical civilians" is cleaner than listing 8 coordinates
- Faster ticks — less data to process per agent call

**What is NOT changing:**
- 3 agents (CASPER, MELCHIOR, BALTHASAR) — same roles, same voting logic
- Flask + SocketIO backend — same server structure
- Frontend socket hooks — same events, just different payload shape
- Voting mechanism — identical logic in `voting.py`

---

## City Map Structure

The city is divided into **12 sectors** arranged in a 4-column × 3-row grid.

```
┌──────────┬──────────┬──────────┬──────────┐
│          │          │          │          │
│    A1    │    B1    │    C1    │    D1    │
│          │          │          │          │
├──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │
│    A2    │    B2    │    C2    │    D2    │
│          │          │          │          │
├──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │
│    A3    │    B3    │    C3    │    D3    │
│          │          │          │          │
└──────────┴──────────┴──────────┴──────────┘
```

Each sector has:
- A name (A1–D3)
- A type (residential, commercial, industrial, hospital, school)
- Civilian count + severity breakdown
- Infrastructure status (intact, damaged, destroyed)
- Active resource units deployed
- Hazards present (fire, structural collapse, flooding)

---

## New Data Contracts

Replace the old grid/civilians schema with this. **Tell Person C and Person B about this change immediately.**

### Sector Object

```json
{
  "id": "B2",
  "name": "Riverside District",
  "type": "residential",
  "row": 1,
  "col": 1,
  "civilians": {
    "total": 24,
    "critical": 8,
    "stable": 12,
    "rescued": 4
  },
  "infrastructure": "damaged",
  "hazards": ["structural_collapse", "fire"],
  "resources_deployed": {
    "medical_teams": 1,
    "rescue_units": 0,
    "supply_caches": 0
  },
  "severity_score": 0.82,
  "color": "#FF3D5A"
}
```

**`infrastructure` values:** `"intact"`, `"damaged"`, `"destroyed"`

**`type` values:** `"residential"`, `"commercial"`, `"industrial"`, `"hospital"`, `"school"`

**`hazards` values (array, can have multiple):** `"structural_collapse"`, `"fire"`, `"flooding"`, `"gas_leak"`

**`severity_score`:** 0.0–1.0, computed by backend each tick. Formula:
```python
severity = (critical / max(total, 1)) * 0.6 + (len(hazards) * 0.15) + (0 if infrastructure != "destroyed" else 0.1)
severity = min(1.0, severity)
```

**`color`:** computed by backend based on severity_score, sent directly to frontend:
```python
def sector_color(severity_score, infrastructure):
    if infrastructure == "destroyed":
        return "#3D1A0A"   # dark brown — destroyed
    if severity_score >= 0.7:
        return "#2D0A15"   # dark red — critical
    if severity_score >= 0.4:
        return "#251800"   # dark amber — moderate
    if severity_score > 0.0:
        return "#0A2010"   # dark green — low severity
    return "#0A1520"       # near black — clear
```

Frontend receives this color and applies it as the sector background. **No color logic on frontend.**

### Full Grid State (replaces old state schema)

```json
{
  "tick": 14,
  "scenario": "earthquake",
  "is_running": true,
  "city_name": "Lucknow Metro Area",
  "sectors": [
    {
      "id": "A1", "name": "Central Business District", "type": "commercial",
      "row": 0, "col": 0,
      "civilians": { "total": 12, "critical": 0, "stable": 10, "rescued": 2 },
      "infrastructure": "intact",
      "hazards": [],
      "resources_deployed": { "medical_teams": 0, "rescue_units": 0, "supply_caches": 1 },
      "severity_score": 0.05,
      "color": "#0A1520"
    },
    {
      "id": "B2", "name": "Riverside District", "type": "residential",
      "row": 1, "col": 1,
      "civilians": { "total": 24, "critical": 8, "stable": 12, "rescued": 4 },
      "infrastructure": "damaged",
      "hazards": ["structural_collapse"],
      "resources_deployed": { "medical_teams": 1, "rescue_units": 0, "supply_caches": 0 },
      "severity_score": 0.72,
      "color": "#2D0A15"
    }
  ],
  "global_resources": {
    "medical_teams": 2,
    "rescue_units": 3,
    "supply_caches": 4
  },
  "total_civilians": {
    "total": 180,
    "critical": 32,
    "stable": 98,
    "rescued": 50
  },
  "survival_rate": 0.82,
  "events": []
}
```

### Agent Vote (updated target field)

```json
{
  "agent": "CASPER",
  "proposed_action": "dispatch_medical",
  "target_sector": "B2",
  "reasoning": "Sector B2 (Riverside District) has 8 critical civilians with only 1 medical team. Mortality risk is highest here.",
  "priority_score": 0.91,
  "tick": 14
}
```

`target_sector` replaces `target_zone` and `target_civilian_id`.

**Valid `proposed_action` values (unchanged):**
`dispatch_medical`, `dispatch_rescue`, `dispatch_supply`, `hold`

### Vote Result (unchanged structure, `winning_target` is now a sector ID)

```json
{
  "tick": 14,
  "votes": ["...3 agent votes"],
  "winner": "CASPER",
  "winning_action": "dispatch_medical",
  "winning_target": "B2",
  "resolution_method": "highest_score",
  "was_tiebreak": false
}
```

### SocketIO Events (unchanged — same event names, new payload shape)

Frontend → Backend (unchanged):
```
load_scenario   → { "scenario": "earthquake" }
trigger_event   → { "event": "aftershock" | "fire_spread" | "resource_depletion" }
pause / resume / reset → no payload
```

Backend → Frontend (unchanged names, new data):
```
state_update    → full state JSON above (every tick)
vote_result     → VoteResult JSON (every tick)
scenario_loaded → scenario name string
error           → { "message": "..." }
```

---

## AYUSH — Changes to engine/ and agents/

### backend/engine/grid.py → rename to backend/engine/city.py

Replace `GridEngine` with `CityEngine`. No more 10x10 numpy array.

```python
import copy

class CityEngine:

    def tick(self, state: dict) -> dict:
        """Advance simulation by one tick."""
        state = copy.deepcopy(state)
        state["tick"] += 1

        for sector in state["sectors"]:
            # Decay civilians each tick based on infrastructure + hazards
            decay_rate = self._decay_rate(sector)

            # Move some critical civilians toward death if no medical present
            med_present = sector["resources_deployed"]["medical_teams"] > 0
            if not med_present and sector["civilians"]["critical"] > 0:
                # Some critical civilians worsen each tick
                worsening = max(1, sector["civilians"]["critical"] // 4)
                sector["civilians"]["critical"] = max(0, sector["civilians"]["critical"] - worsening)
                # They don't die instantly — they move to a "rescued" count only when a unit arrives
            
            # If medical team present, stabilize critical civilians
            if med_present:
                stabilized = min(sector["civilians"]["critical"], 3)
                sector["civilians"]["critical"] -= stabilized
                sector["civilians"]["stable"] += stabilized
                sector["civilians"]["rescued"] += 0  # rescued when fully clear

            # If rescue unit present, rescue civilians from collapsed structures
            rescue_present = sector["resources_deployed"]["rescue_units"] > 0
            if rescue_present and "structural_collapse" in sector["hazards"]:
                rescued = min(sector["civilians"]["stable"], 4)
                sector["civilians"]["stable"] -= rescued
                sector["civilians"]["rescued"] += rescued
                # Remove hazard if rescue has been here a while
                if state["tick"] % 3 == 0:
                    sector["hazards"] = [h for h in sector["hazards"] if h != "structural_collapse"]

            # Recompute severity score
            sector["severity_score"] = self._severity(sector)
            sector["color"] = self._color(sector["severity_score"], sector["infrastructure"])

        # Recompute totals
        state["total_civilians"] = self._total_civilians(state["sectors"])
        alive = state["total_civilians"]["critical"] + state["total_civilians"]["stable"] + state["total_civilians"]["rescued"]
        total = state["total_civilians"]["total"]
        state["survival_rate"] = round(alive / max(total, 1), 2)

        return state

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
            # Immediately downgrade infrastructure one level
            if sector["infrastructure"] == "destroyed":
                sector["infrastructure"] = "damaged"
            elif sector["infrastructure"] == "damaged":
                sector["infrastructure"] = "intact"

        elif action == "dispatch_supply" and res["supply_caches"] > 0:
            res["supply_caches"] -= 1
            sector["resources_deployed"]["supply_caches"] += 1
            # Stabilize some civilians immediately
            boosted = min(sector["civilians"]["critical"], 5)
            sector["civilians"]["critical"] -= boosted
            sector["civilians"]["stable"] += boosted

        # Recompute after action
        sector["severity_score"] = self._severity(sector)
        sector["color"] = self._color(sector["severity_score"], sector["infrastructure"])

        return state

    def _decay_rate(self, sector) -> float:
        base = 0.05
        if sector["infrastructure"] == "destroyed": base += 0.1
        if sector["infrastructure"] == "damaged":   base += 0.05
        base += len(sector["hazards"]) * 0.05
        return base

    def _severity(self, sector) -> float:
        civ = sector["civilians"]
        total = max(civ["total"], 1)
        score = (civ["critical"] / total) * 0.6
        score += len(sector["hazards"]) * 0.12
        if sector["infrastructure"] == "destroyed": score += 0.15
        if sector["infrastructure"] == "damaged":   score += 0.07
        return round(min(1.0, score), 3)

    def _color(self, severity: float, infrastructure: str) -> str:
        if infrastructure == "destroyed":  return "#3D1A0A"
        if severity >= 0.7:                return "#2D0A15"
        if severity >= 0.4:                return "#251800"
        if severity > 0.05:                return "#0A2010"
        return "#0A1520"

    def _total_civilians(self, sectors) -> dict:
        totals = {"total": 0, "critical": 0, "stable": 0, "rescued": 0}
        for s in sectors:
            for k in totals:
                totals[k] += s["civilians"].get(k, 0)
        return totals
```

### backend/engine/events.py (updated for sectors)

```python
import random
import copy

class EventEngine:

    def trigger(self, state: dict, event_name: str) -> dict:
        state = copy.deepcopy(state)
        active_sectors = [s for s in state["sectors"] if s["infrastructure"] != "destroyed"]

        if event_name == "aftershock":
            # Damage 1-2 random sectors
            targets = random.sample(active_sectors, min(2, len(active_sectors)))
            for s in targets:
                if s["infrastructure"] == "intact":
                    s["infrastructure"] = "damaged"
                elif s["infrastructure"] == "damaged":
                    s["infrastructure"] = "destroyed"
                if "structural_collapse" not in s["hazards"]:
                    s["hazards"].append("structural_collapse")
                # Increase critical count
                new_critical = random.randint(2, 5)
                s["civilians"]["critical"] = min(s["civilians"]["total"], s["civilians"]["critical"] + new_critical)
                s["civilians"]["stable"] = max(0, s["civilians"]["stable"] - new_critical)
                s["severity_score"] = self._severity(s)
                s["color"] = "#2D0A15"
            state["events"].append("aftershock")

        elif event_name == "fire_spread":
            # Add fire hazard to 1 sector
            targets = [s for s in active_sectors if "fire" not in s["hazards"]]
            if targets:
                t = random.choice(targets)
                t["hazards"].append("fire")
                t["severity_score"] = min(1.0, t["severity_score"] + 0.2)
                t["color"] = "#3D0A15"
            state["events"].append("fire_spread")

        elif event_name == "resource_depletion":
            # Remove one deployed resource from a random sector
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
        if sector["infrastructure"] == "destroyed": score += 0.15
        if sector["infrastructure"] == "damaged":   score += 0.07
        return round(min(1.0, score), 3)
```

### backend/engine/scenarios.py (unchanged — still loads JSON files)

No changes needed. Scenario JSON format changes (see Person D section), but the loader just reads and returns whatever JSON it finds.

### backend/agents/base_agent.py (updated prompt)

Only `_build_prompt` changes. Everything else stays the same.

```python
def _build_prompt(self, state: dict) -> str:
    sectors = state["sectors"]

    # Build sector summary for prompt
    sector_lines = []
    for s in sorted(sectors, key=lambda x: x["severity_score"], reverse=True):
        civ = s["civilians"]
        hazard_str = ", ".join(s["hazards"]) if s["hazards"] else "none"
        deployed_str = ", ".join(
            f"{v} {k.replace('_',' ')}" for k, v in s["resources_deployed"].items() if v > 0
        ) or "none"
        sector_lines.append(
            f"  {s['id']} ({s['name']}, {s['type']}): "
            f"{civ['critical']} critical / {civ['stable']} stable / {civ['rescued']} rescued "
            f"| infra: {s['infrastructure']} | hazards: {hazard_str} | deployed: {deployed_str} "
            f"| severity: {s['severity_score']:.2f}"
        )

    res = state["global_resources"]
    return f"""TICK {state['tick']} — {state.get('city_name','City')} DISASTER STATE

SECTORS BY SEVERITY:
{chr(10).join(sector_lines)}

GLOBAL RESOURCES AVAILABLE:
  Medical teams:  {res['medical_teams']}
  Rescue units:   {res['rescue_units']}
  Supply caches:  {res['supply_caches']}

TOTALS: {state['total_civilians']['critical']} critical | {state['total_civilians']['stable']} stable | {state['total_civilians']['rescued']} rescued
SURVIVAL RATE: {state['survival_rate']*100:.0f}%

Respond ONLY with this exact JSON, no other text:
{{
  "proposed_action": "dispatch_medical" | "dispatch_rescue" | "dispatch_supply" | "hold",
  "target_sector": "A1" through "D3" or null,
  "reasoning": "one sentence, max 20 words",
  "priority_score": 0.0 to 1.0
}}"""
```

### backend/agents/voting.py — No changes needed.

### backend/orchestrator.py — One line change

Replace `grid_engine` with `city_engine`:

```python
# Change this import:
from engine.city import CityEngine   # was: from engine.grid import GridEngine

# Change this line in __init__:
self.city_engine = CityEngine()      # was: self.grid_engine = GridEngine()

# Change these lines in _run_tick:
self.state = self.city_engine.tick(self.state)
# ...
self.state = self.city_engine.execute_action(
    self.state,
    vote_result["winning_action"],
    vote_result.get("winning_target") or ""
)
```

Everything else in orchestrator.py stays the same.

---

## PERSON D — Updated Scenario JSON Format

Scenarios no longer have a grid array or individual civilians. Replace all 3 scenario files.

### Schema

```json
{
  "name": "earthquake",
  "display_name": "Earthquake",
  "city_name": "Lucknow Metro Area",
  "description": "7.2 magnitude earthquake. Multiple building collapses across northern sectors.",
  "sectors": [
    {
      "id": "A1",
      "name": "Central Business District",
      "type": "commercial",
      "row": 0, "col": 0,
      "civilians": { "total": 15, "critical": 0, "stable": 14, "rescued": 1 },
      "infrastructure": "intact",
      "hazards": [],
      "resources_deployed": { "medical_teams": 0, "rescue_units": 0, "supply_caches": 0 }
    }
  ],
  "global_resources": {
    "medical_teams": 3,
    "rescue_units": 4,
    "supply_caches": 5
  }
}
```

**Rules for designing good scenarios:**
- 12 sectors total, arranged 4 columns × 3 rows (A–D, 1–3)
- At least 3 sectors with `critical > 5` — forces agent disagreement
- At least 2 sectors with `infrastructure: "destroyed"` or `"damaged"`
- Keep `global_resources` limited — scarcity forces tradeoffs
- Vary sector types (mix residential, hospital, school) — hospital with critical civilians = obvious CASPER target, creates drama
- `resources_deployed` always starts as all zeros

### backend/scenarios/earthquake.json

```json
{
  "name": "earthquake",
  "display_name": "Earthquake",
  "city_name": "Lucknow Metro Area",
  "description": "7.2 magnitude earthquake. Building collapses across northern and central sectors.",
  "sectors": [
    { "id":"A1","name":"Old City Market","type":"commercial","row":0,"col":0,
      "civilians":{"total":20,"critical":2,"stable":16,"rescued":2},"infrastructure":"damaged","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B1","name":"Central Hospital","type":"hospital","row":0,"col":1,
      "civilians":{"total":45,"critical":12,"stable":30,"rescued":3},"infrastructure":"damaged","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C1","name":"University Zone","type":"school","row":0,"col":2,
      "civilians":{"total":60,"critical":18,"stable":38,"rescued":4},"infrastructure":"destroyed","hazards":["structural_collapse","fire"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D1","name":"Industrial North","type":"industrial","row":0,"col":3,
      "civilians":{"total":10,"critical":0,"stable":8,"rescued":2},"infrastructure":"damaged","hazards":["gas_leak"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"A2","name":"Riverside District","type":"residential","row":1,"col":0,
      "civilians":{"total":35,"critical":8,"stable":24,"rescued":3},"infrastructure":"damaged","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B2","name":"City Centre","type":"commercial","row":1,"col":1,
      "civilians":{"total":25,"critical":3,"stable":20,"rescued":2},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C2","name":"Hazratganj","type":"residential","row":1,"col":2,
      "civilians":{"total":40,"critical":10,"stable":26,"rescued":4},"infrastructure":"damaged","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D2","name":"Railway Colony","type":"residential","row":1,"col":3,
      "civilians":{"total":30,"critical":5,"stable":22,"rescued":3},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"A3","name":"Cantonment Area","type":"industrial","row":2,"col":0,
      "civilians":{"total":12,"critical":0,"stable":11,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B3","name":"Gomti Nagar","type":"residential","row":2,"col":1,
      "civilians":{"total":50,"critical":6,"stable":38,"rescued":6},"infrastructure":"damaged","hazards":["flooding"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C3","name":"Alambagh","type":"residential","row":2,"col":2,
      "civilians":{"total":28,"critical":4,"stable":22,"rescued":2},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D3","name":"Amausi Zone","type":"industrial","row":2,"col":3,
      "civilians":{"total":15,"critical":0,"stable":14,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} }
  ],
  "global_resources": { "medical_teams": 3, "rescue_units": 4, "supply_caches": 5 }
}
```

### backend/scenarios/flood.json

```json
{
  "name": "flood",
  "display_name": "Flood",
  "city_name": "Lucknow Metro Area",
  "description": "Flash flood from Gomti river overflow. Southern sectors inundated.",
  "sectors": [
    { "id":"A1","name":"Old City Market","type":"commercial","row":0,"col":0,
      "civilians":{"total":20,"critical":0,"stable":19,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B1","name":"Central Hospital","type":"hospital","row":0,"col":1,
      "civilians":{"total":45,"critical":5,"stable":36,"rescued":4},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C1","name":"University Zone","type":"school","row":0,"col":2,
      "civilians":{"total":60,"critical":3,"stable":54,"rescued":3},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D1","name":"Industrial North","type":"industrial","row":0,"col":3,
      "civilians":{"total":10,"critical":0,"stable":10,"rescued":0},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"A2","name":"Riverside District","type":"residential","row":1,"col":0,
      "civilians":{"total":35,"critical":14,"stable":18,"rescued":3},"infrastructure":"damaged","hazards":["flooding"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B2","name":"City Centre","type":"commercial","row":1,"col":1,
      "civilians":{"total":25,"critical":8,"stable":15,"rescued":2},"infrastructure":"damaged","hazards":["flooding"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C2","name":"Hazratganj","type":"residential","row":1,"col":2,
      "civilians":{"total":40,"critical":2,"stable":36,"rescued":2},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D2","name":"Railway Colony","type":"residential","row":1,"col":3,
      "civilians":{"total":30,"critical":0,"stable":28,"rescued":2},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"A3","name":"Cantonment Area","type":"industrial","row":2,"col":0,
      "civilians":{"total":12,"critical":4,"stable":7,"rescued":1},"infrastructure":"destroyed","hazards":["flooding","structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B3","name":"Gomti Nagar","type":"residential","row":2,"col":1,
      "civilians":{"total":50,"critical":20,"stable":24,"rescued":6},"infrastructure":"destroyed","hazards":["flooding"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C3","name":"Alambagh","type":"residential","row":2,"col":2,
      "civilians":{"total":28,"critical":10,"stable":16,"rescued":2},"infrastructure":"damaged","hazards":["flooding"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D3","name":"Amausi Zone","type":"industrial","row":2,"col":3,
      "civilians":{"total":15,"critical":2,"stable":12,"rescued":1},"infrastructure":"damaged","hazards":["flooding"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} }
  ],
  "global_resources": { "medical_teams": 3, "rescue_units": 3, "supply_caches": 6 }
}
```

### backend/scenarios/building_collapse.json

```json
{
  "name": "building_collapse",
  "display_name": "Building Collapse",
  "city_name": "Lucknow Metro Area",
  "description": "Multi-story residential complex collapse. High rescue demand, limited medical.",
  "sectors": [
    { "id":"A1","name":"Old City Market","type":"commercial","row":0,"col":0,
      "civilians":{"total":20,"critical":0,"stable":19,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B1","name":"Central Hospital","type":"hospital","row":0,"col":1,
      "civilians":{"total":45,"critical":20,"stable":22,"rescued":3},"infrastructure":"damaged","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C1","name":"University Zone","type":"school","row":0,"col":2,
      "civilians":{"total":60,"critical":25,"stable":30,"rescued":5},"infrastructure":"destroyed","hazards":["structural_collapse","fire"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D1","name":"Industrial North","type":"industrial","row":0,"col":3,
      "civilians":{"total":10,"critical":0,"stable":10,"rescued":0},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"A2","name":"Riverside District","type":"residential","row":1,"col":0,
      "civilians":{"total":35,"critical":15,"stable":18,"rescued":2},"infrastructure":"destroyed","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B2","name":"City Centre","type":"commercial","row":1,"col":1,
      "civilians":{"total":25,"critical":0,"stable":24,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C2","name":"Hazratganj","type":"residential","row":1,"col":2,
      "civilians":{"total":40,"critical":12,"stable":26,"rescued":2},"infrastructure":"damaged","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D2","name":"Railway Colony","type":"residential","row":1,"col":3,
      "civilians":{"total":30,"critical":8,"stable":20,"rescued":2},"infrastructure":"damaged","hazards":["structural_collapse"],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"A3","name":"Cantonment Area","type":"industrial","row":2,"col":0,
      "civilians":{"total":12,"critical":0,"stable":11,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"B3","name":"Gomti Nagar","type":"residential","row":2,"col":1,
      "civilians":{"total":50,"critical":5,"stable":40,"rescued":5},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"C3","name":"Alambagh","type":"residential","row":2,"col":2,
      "civilians":{"total":28,"critical":0,"stable":26,"rescued":2},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} },
    { "id":"D3","name":"Amausi Zone","type":"industrial","row":2,"col":3,
      "civilians":{"total":15,"critical":0,"stable":14,"rescued":1},"infrastructure":"intact","hazards":[],
      "resources_deployed":{"medical_teams":0,"rescue_units":0,"supply_caches":0} }
  ],
  "global_resources": { "medical_teams": 2, "rescue_units": 5, "supply_caches": 4 }
}
```

### Validate all 3 files:

```bash
python -c "
import json
for s in ['earthquake','flood','building_collapse']:
    data = json.load(open(f'backend/scenarios/{s}.json'))
    assert len(data['sectors']) == 12, f'{s}: need 12 sectors'
    assert all(k in data['global_resources'] for k in ['medical_teams','rescue_units','supply_caches'])
    print(f'✓ {s}.json valid — {len(data[\"sectors\"])} sectors')
"
```

---

## PERSON B — Frontend Map Component

Replace `Grid.jsx` with `CityMap.jsx`. Everything else (AgentPanels, VoteHistory, SurvivalTracker, EventControls, ScenarioSelector) stays the same.

### What CityMap renders

A 4×3 grid of sector cards. Each sector card shows:
- Sector ID (A1, B2...) top-left in mono
- Sector name below it
- Civilian counts: `12 CRIT / 24 STABLE` in small text
- Hazard icons (🔥 for fire, 🏚 for collapse, 🌊 for flood)
- Infrastructure badge (INTACT / DAMAGED / DESTROYED)
- Resource units deployed (+ icons for medical, rescue icons for rescue)
- Background color from `sector.color` — sent directly by backend, no frontend logic
- Highlighted border if this sector was the last vote winner

### CityMap.jsx

```jsx
import React from "react"
import clsx from "clsx"

const HAZARD_ICONS = {
  structural_collapse: "🏚",
  fire: "🔥",
  flooding: "🌊",
  gas_leak: "⚠️",
}

const INFRA_STYLE = {
  intact:    { label: "INTACT",    color: "text-green-400  border-green-900" },
  damaged:   { label: "DAMAGED",   color: "text-amber-400  border-amber-900" },
  destroyed: { label: "DESTROYED", color: "text-red-400    border-red-900"   },
}

export default function CityMap({ gridState, lastWinnerSector }) {
  if (!gridState) {
    return (
      <div className="flex items-center justify-center h-full text-muted text-xs font-mono tracking-widest">
        SELECT A SCENARIO TO BEGIN
      </div>
    )
  }

  const sectors = gridState.sectors
  // Build 4x3 layout: rows 0-2, cols 0-3
  const rows = [0, 1, 2]
  const cols = [0, 1, 2, 3]

  return (
    <div className="p-3 h-full flex flex-col gap-1">
      {rows.map(r => (
        <div key={r} className="flex gap-1 flex-1">
          {cols.map(c => {
            const sector = sectors.find(s => s.row === r && s.col === c)
            if (!sector) return <div key={c} className="flex-1" />
            return (
              <SectorCard
                key={sector.id}
                sector={sector}
                isWinner={lastWinnerSector === sector.id}
              />
            )
          })}
        </div>
      ))}
    </div>
  )
}

function SectorCard({ sector, isWinner }) {
  const infra = INFRA_STYLE[sector.infrastructure] || INFRA_STYLE.intact
  const civ = sector.civilians
  const dep = sector.resources_deployed

  return (
    <div
      className={clsx(
        "flex-1 rounded-sm border p-2 flex flex-col justify-between transition-all duration-500 cursor-default relative overflow-hidden",
        isWinner ? "border-teal shadow-[0_0_10px_rgba(0,212,184,0.3)]" : "border-[#1A3045]"
      )}
      style={{ backgroundColor: sector.color }}
    >
      {/* Winner pulse ring */}
      {isWinner && (
        <div className="absolute inset-0 rounded-sm border border-teal opacity-60 animate-ping pointer-events-none" />
      )}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="font-mono text-[10px] text-teal font-bold tracking-widest leading-none">
            {sector.id}
          </div>
          <div className="font-ui text-[11px] text-white font-semibold leading-tight mt-0.5 tracking-wide">
            {sector.name}
          </div>
        </div>
        <div className={clsx("font-mono text-[8px] px-1 py-0.5 rounded border tracking-wider leading-none mt-0.5", infra.color)}>
          {infra.label}
        </div>
      </div>

      {/* Civilian counts */}
      <div className="flex gap-2 mt-1">
        {civ.critical > 0 && (
          <span className="font-mono text-[9px] text-red-400 font-bold">{civ.critical} CRIT</span>
        )}
        {civ.stable > 0 && (
          <span className="font-mono text-[9px] text-amber-400">{civ.stable} STBL</span>
        )}
        {civ.rescued > 0 && (
          <span className="font-mono text-[9px] text-green-400">{civ.rescued} RESC</span>
        )}
      </div>

      {/* Hazard icons */}
      {sector.hazards.length > 0 && (
        <div className="flex gap-1 mt-1">
          {sector.hazards.map(h => (
            <span key={h} className="text-[11px]" title={h.replace(/_/g,' ')}>
              {HAZARD_ICONS[h] || "⚠️"}
            </span>
          ))}
        </div>
      )}

      {/* Deployed resources */}
      {(dep.medical_teams > 0 || dep.rescue_units > 0 || dep.supply_caches > 0) && (
        <div className="flex gap-1 mt-1 flex-wrap">
          {Array(dep.medical_teams).fill(0).map((_,i) => (
            <span key={`m${i}`} className="font-mono text-[9px] text-teal border border-teal/40 px-1 rounded-sm">+MED</span>
          ))}
          {Array(dep.rescue_units).fill(0).map((_,i) => (
            <span key={`r${i}`} className="font-mono text-[9px] text-amber-400 border border-amber-400/40 px-1 rounded-sm">RESC</span>
          ))}
          {Array(dep.supply_caches).fill(0).map((_,i) => (
            <span key={`s${i}`} className="font-mono text-[9px] text-blue-400 border border-blue-400/40 px-1 rounded-sm">SUP</span>
          ))}
        </div>
      )}
    </div>
  )
}
```

### Update App.jsx

Replace `Grid` import and usage:

```jsx
// Replace:
import Grid from "./components/Grid"
// With:
import CityMap from "./components/CityMap"

// Track last winner sector in App.jsx:
const [lastWinnerSector, setLastWinnerSector] = useState(null)

// In useSocket or App, when voteResult updates:
useEffect(() => {
  if (voteResult?.winning_target) {
    setLastWinnerSector(voteResult.winning_target)
  }
}, [voteResult])

// In JSX, replace <Grid gridState={sock.gridState} /> with:
<CityMap gridState={sock.gridState} lastWinnerSector={lastWinnerSector} />
```

### Update Decision Log entries

Log text format changes to reference sector names:

```
T-14  CASPER     Dispatched medical to B2 (Riverside District). 8 critical civilians.
T-13  BALTHASAR  Rescue to C1 (University Zone). Structural collapse cleared.
```

Get the sector name from `gridState.sectors.find(s => s.id === vote.target_sector)?.name`.

---

## PROGRESS.md — Add These New Tasks

Add this section to your PROGRESS.md when you start:

```markdown
### Map Architecture Migration (from grid to city map)

#### Ayush
- [ ] Created backend/engine/city.py (CityEngine replacing GridEngine)
- [ ] Updated backend/engine/events.py for sector-based events
- [ ] Updated backend/agents/base_agent.py _build_prompt for sector state
- [ ] Updated backend/orchestrator.py imports (city not grid)
- [ ] Tested: city_engine.tick() updates sector civilian counts correctly
- [ ] Tested: city_engine.execute_action("dispatch_medical","B2") deploys unit

#### Person C
- [ ] Updated orchestrator.py import from grid to city
- [ ] Verified state_update emits sectors array not grid array
- [ ] Tested: full tick loop works with new sector state shape

#### Person B
- [ ] Created frontend/src/components/CityMap.jsx
- [ ] Updated App.jsx to use CityMap instead of Grid
- [ ] Tested: 4x3 sector grid renders with backend colors
- [ ] Tested: winner sector gets teal border highlight
- [ ] Tested: hazard icons appear correctly

#### Person D
- [ ] Updated earthquake.json to sector format (12 sectors)
- [ ] Updated flood.json to sector format (12 sectors)
- [ ] Updated building_collapse.json to sector format (12 sectors)
- [ ] Ran validation script — all 3 pass
```
