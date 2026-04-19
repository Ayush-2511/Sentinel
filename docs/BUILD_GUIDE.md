# SENTINEL — MASTER BUILD GUIDE
> This file is the single source of truth for the entire project.
> Every AI agent on every teammate's laptop must read this file completely before writing a single line of code.
> After reading, the AI must create and maintain a `PROGRESS.md` file in the repo root (instructions at the bottom of this file).

---

## What We Are Building

SENTINEL is a multi-agent AI disaster response system for a 24-hour hackathon.

Three AI agents (CASPER, MELCHIOR, BALTHASAR) independently observe a live 10x10 disaster grid, each reasons using LangChain + OpenRouter, votes on the best action, and the consensus decision executes on the grid. A React frontend shows the live grid and agent reasoning in real time.

**This is NOT a chatbot. Users do not type anything. The system runs autonomously.**

**Hackathon scope — keep it simple:**
- 10x10 grid, no pathfinding, units teleport to targets instantly
- Agents call OpenRouter API sequentially (not parallel) to avoid rate limits
- No authentication, no database, no user accounts
- No tests required — just make it work for the demo

---

## Team Assignments

| Person | Owns | Files |
|---|---|---|
| **Ayush** | Agents + Simulation | `backend/engine/`, `backend/agents/` |
| **Person B** | Frontend | `frontend/` |
| **Person C** | Backend + Linking | `backend/app.py`, `backend/orchestrator.py` |
| **Person D** | Scenarios + Demo | `backend/scenarios/` |

**Rule: Never touch files outside your assigned scope.**

---

## Repo Structure

Create this exact structure. Do not add or rename folders.

```
sentinel/
├── BUILD_GUIDE.md         ← This file
├── PROGRESS.md            ← AI creates and updates this (see bottom of file)
├── .env                   ← Copy from .env.example, never commit
├── .env.example
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── app.py             ← Person C
│   ├── orchestrator.py    ← Person C
│   │
│   ├── engine/            ← Ayush
│   │   ├── __init__.py
│   │   ├── grid.py
│   │   ├── events.py
│   │   └── scenarios.py
│   │
│   ├── agents/            ← Ayush
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── casper.py
│   │   ├── melchior.py
│   │   ├── balthasar.py
│   │   └── voting.py
│   │
│   └── scenarios/         ← Person D
│       ├── earthquake.json
│       ├── flood.json
│       └── building_collapse.json
│
└── frontend/              ← Person B
    ├── package.json
    ├── index.html
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── socket.js
        ├── hooks/
        │   └── useSocket.js
        └── components/
            ├── Grid.jsx
            ├── AgentPanels.jsx
            ├── VoteHistory.jsx
            ├── SurvivalTracker.jsx
            ├── EventControls.jsx
            └── ScenarioSelector.jsx
```

---

## Environment Setup

### .env.example (commit this)
```
OPENROUTER_API_KEY=your_key_here
FLASK_PORT=5001
TICK_INTERVAL_SECONDS=5
```

### .gitignore
```
.env
backend/venv/
backend/__pycache__/
backend/**/__pycache__/
node_modules/
frontend/dist/
```

### Python setup (Person C and Ayush)
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Node setup (Person B)
```bash
cd frontend
npm install
```

### Running locally
```bash
# Terminal 1
cd backend && source venv/bin/activate && python app.py

# Terminal 2
cd frontend && npm run dev
```

Backend → http://localhost:5001
Frontend → http://localhost:5173

---

## Python Dependencies (backend/requirements.txt)

```
flask==3.0.3
flask-socketio==5.3.6
flask-cors==4.0.0
python-dotenv==1.0.1
langchain==0.2.6
langchain-openai==0.1.14
numpy==1.26.4
eventlet==0.36.1
```

**Use eventlet only. Never use threading or gevent with Flask-SocketIO.**

## Frontend Dependencies

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install socket.io-client recharts clsx
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

## DATA CONTRACTS — Sacred. Never change field names.

Everyone builds against these. If you need a new field, add it. Never rename existing ones.

### Grid State (backend → frontend via `state_update` event, every tick)

```json
{
  "tick": 12,
  "scenario": "earthquake",
  "is_running": true,
  "survival_rate": 0.83,
  "grid": [[0,0,1,0,0,0,0,0,0,0], "...9 more rows"],
  "civilians": [
    { "id": 1, "pos": [3,4], "health": 15, "status": "critical", "assigned_unit": null },
    { "id": 2, "pos": [7,2], "health": 60, "status": "stable",   "assigned_unit": "medical_1" }
  ],
  "resources": {
    "medical_teams": 2,
    "rescue_units": 3,
    "supply_caches": 4
  },
  "active_units": [
    { "id": "medical_1", "type": "medical", "pos": [5,3], "target_civilian_id": 2 }
  ],
  "events": []
}
```

### Grid Cell Values
```
0 = empty
1 = collapsed building
2 = fire
3 = civilian (details in civilians array)
4 = resource cache
5 = active unit
```

### Agent Vote (each agent produces one per tick)

```json
{
  "agent": "CASPER",
  "proposed_action": "dispatch_medical",
  "target_zone": "C4",
  "target_civilian_id": 1,
  "reasoning": "Zone C4 has 3 civilians at critical health. Estimated 2 deaths without intervention.",
  "priority_score": 0.91,
  "tick": 12
}
```

Valid `proposed_action` values: `dispatch_medical`, `dispatch_rescue`, `dispatch_supply`, `hold`

### Vote Result (backend → frontend via `vote_result` event, every tick)

```json
{
  "tick": 12,
  "votes": ["...array of 3 agent votes"],
  "winner": "CASPER",
  "winning_action": "dispatch_medical",
  "winning_target": "C4",
  "resolution_method": "highest_score",
  "was_tiebreak": false
}
```

`resolution_method` values: `highest_score`, `tiebreak`, `unanimous`

### SocketIO Events

**Backend → Frontend:**
```
state_update     → GridState JSON (every tick)
vote_result      → VoteResult JSON (every tick)
scenario_loaded  → scenario name string
error            → { "message": "..." }
```

**Frontend → Backend:**
```
load_scenario   → { "scenario": "earthquake" | "flood" | "building_collapse" }
trigger_event   → { "event": "aftershock" | "fire_spread" | "resource_depletion" }
pause           → no payload
resume          → no payload
reset           → no payload
```

---

## AYUSH — Agents + Simulation

You build the brain of SENTINEL. Everything else depends on what you produce.

**Your files:** `backend/engine/`, `backend/agents/`

**Do this first (Hour 0-1): Share the state dict structure with Person C so they can start orchestrator.py in parallel.**

### backend/engine/grid.py

Manages the 10x10 grid state. Keep it simple — no pathfinding, units teleport.

```python
import numpy as np
import copy

class GridEngine:

    def tick(self, state: dict) -> dict:
        """
        Advance simulation by one tick.
        - Decay civilian health
        - Move active units toward targets (just teleport — set pos = target pos)
        - Update survival_rate
        - Return updated state
        """
        state = copy.deepcopy(state)
        state["tick"] += 1

        # Decay civilian health
        for c in state["civilians"]:
            if c["health"] > 0:
                decay = 8 if c["status"] == "critical" else 3
                c["health"] = max(0, c["health"] - decay)
                if c["health"] == 0:
                    c["status"] = "dead"
                elif c["health"] < 30:
                    c["status"] = "critical"

        # Move active units to their targets (simple teleport)
        for unit in state["active_units"]:
            civ = next((c for c in state["civilians"] if c["id"] == unit.get("target_civilian_id")), None)
            if civ and civ["health"] > 0:
                unit["pos"] = list(civ["pos"])
                # If medical unit reaches civilian, stabilize them
                if unit["type"] == "medical":
                    civ["health"] = min(100, civ["health"] + 20)
                    civ["status"] = "stable" if civ["health"] >= 30 else "critical"

        # Update survival rate
        alive = sum(1 for c in state["civilians"] if c["health"] > 0)
        state["survival_rate"] = round(alive / len(state["civilians"]), 2) if state["civilians"] else 1.0

        # Rebuild grid from state
        state["grid"] = self._rebuild_grid(state)

        return state

    def execute_action(self, state: dict, action: str, target: str) -> dict:
        """
        Execute the winning action on the grid.
        action: proposed_action string from vote
        target: target_zone string from vote (e.g. "C4" means row=2, col=3)
        """
        state = copy.deepcopy(state)

        if action == "hold" or not target:
            return state

        # Parse target zone (letter = col A-J, number = row 0-9)
        try:
            col = ord(target[0].upper()) - ord('A')
            row = int(target[1])
        except:
            return state  # bad target string, skip

        if action == "dispatch_medical" and state["resources"]["medical_teams"] > 0:
            state["resources"]["medical_teams"] -= 1
            unit_id = f"medical_{state['tick']}"
            state["active_units"].append({
                "id": unit_id,
                "type": "medical",
                "pos": [row, col],
                "target_civilian_id": self._nearest_civilian_id(state, row, col)
            })

        elif action == "dispatch_rescue" and state["resources"]["rescue_units"] > 0:
            state["resources"]["rescue_units"] -= 1
            # Clear collapsed cell
            if 0 <= row < 10 and 0 <= col < 10:
                state["grid"][row][col] = 0
            unit_id = f"rescue_{state['tick']}"
            state["active_units"].append({
                "id": unit_id,
                "type": "rescue",
                "pos": [row, col],
                "target_civilian_id": self._nearest_civilian_id(state, row, col)
            })

        elif action == "dispatch_supply" and state["resources"]["supply_caches"] > 0:
            state["resources"]["supply_caches"] -= 1
            # Boost health of civilians in target area
            for c in state["civilians"]:
                if c["health"] > 0 and abs(c["pos"][0]-row) <= 2 and abs(c["pos"][1]-col) <= 2:
                    c["health"] = min(100, c["health"] + 15)

        return state

    def _nearest_civilian_id(self, state, row, col):
        closest = None
        min_dist = float('inf')
        for c in state["civilians"]:
            if c["health"] > 0:
                dist = abs(c["pos"][0]-row) + abs(c["pos"][1]-col)
                if dist < min_dist:
                    min_dist = dist
                    closest = c["id"]
        return closest

    def _rebuild_grid(self, state):
        grid = [[0]*10 for _ in range(10)]
        # Place collapsed cells (keep from original, only clear if rescue dispatched)
        for r in range(10):
            for c in range(10):
                if state["grid"][r][c] == 1:
                    grid[r][c] = 1
                elif state["grid"][r][c] == 2:
                    grid[r][c] = 2
        # Place civilians
        for civ in state["civilians"]:
            if civ["health"] > 0:
                r, c = civ["pos"]
                grid[r][c] = 3
        # Place active units
        for unit in state["active_units"]:
            r, c = unit["pos"]
            grid[r][c] = 5
        return grid
```

### backend/engine/events.py

```python
import random
import copy

class EventEngine:

    def trigger(self, state: dict, event_name: str) -> dict:
        state = copy.deepcopy(state)

        if event_name == "aftershock":
            # Add 1-2 new collapsed zones in random empty cells
            count = random.randint(1, 2)
            for _ in range(count):
                r, c = random.randint(0,9), random.randint(0,9)
                if state["grid"][r][c] == 0:
                    state["grid"][r][c] = 1
            state["events"].append("aftershock")

        elif event_name == "fire_spread":
            # Find existing fire cells and spread to adjacent empty cells
            fire_cells = [(r,c) for r in range(10) for c in range(10) if state["grid"][r][c] == 2]
            if not fire_cells:
                # Start a new fire somewhere
                r, c = random.randint(0,9), random.randint(0,9)
                state["grid"][r][c] = 2
            else:
                r, c = random.choice(fire_cells)
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and state["grid"][nr][nc] == 0:
                        state["grid"][nr][nc] = 2
                        break
            state["events"].append("fire_spread")

        elif event_name == "resource_depletion":
            # Cut one resource type by 1
            if state["resources"]["supply_caches"] > 0:
                state["resources"]["supply_caches"] -= 1
            state["events"].append("resource_depletion")

        return state
```

### backend/engine/scenarios.py

```python
import json
import os

class ScenarioLoader:

    SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "..", "scenarios")

    def load(self, scenario_name: str) -> dict:
        path = os.path.join(self.SCENARIOS_DIR, f"{scenario_name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Scenario '{scenario_name}' not found at {path}")
        with open(path) as f:
            state = json.load(f)
        # Convert grid to list of lists if needed
        state["is_running"] = True
        state["tick"] = 0
        state["active_units"] = []
        state["events"] = []
        state["survival_rate"] = 1.0
        return state
```

### backend/agents/base_agent.py

```python
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
import re

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "mistralai/mistral-7b-instruct:free"  # free tier on OpenRouter

class BaseAgent:
    """All agents inherit from this. Do not instantiate directly."""

    SYSTEM_PROMPT = ""  # Override in subclass

    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
            model=MODEL,
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

        def zone(pos):
            return f"{chr(65+pos[1])}{pos[0]}"

        crit_str = ", ".join([f"Civilian {c['id']} at {zone(c['pos'])} (health {c['health']})" for c in critical]) or "none"
        stable_str = ", ".join([f"Civilian {c['id']} at {zone(c['pos'])} (health {c['health']})" for c in stable]) or "none"

        return f"""TICK {state['tick']} DISASTER STATE:

Critical civilians: {crit_str}
Stable civilians: {stable_str}
Dead: {len(dead)}

Resources remaining:
- Medical teams: {state['resources']['medical_teams']}
- Rescue units: {state['resources']['rescue_units']}
- Supply caches: {state['resources']['supply_caches']}

Collapsed zones: {[zone(list(p)) for p in collapsed_cells] or 'none'}
Fire zones: {[zone(list(p)) for p in fire_cells] or 'none'}
Active units deployed: {len(state['active_units'])}

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
            raise ValueError("No JSON found in response")
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
```

### backend/agents/casper.py

```python
from .base_agent import BaseAgent

class Casper(BaseAgent):
    SYSTEM_PROMPT = """You are CASPER, the Medical Response agent in a disaster coordination system.

Your ONLY objective: minimize civilian deaths by prioritizing medical dispatch to the most critically injured civilians.

Your bias:
- Always prefer dispatch_medical over other actions
- Prioritize civilians with health below 30 first
- If no medical teams remain, vote hold
- You do NOT care about collapsed buildings or supply logistics — that is not your job
- Assign high priority scores (0.8-1.0) when critical civilians exist with no medical coverage

You respond only with valid JSON. No explanations outside the JSON."""
```

### backend/agents/melchior.py

```python
from .base_agent import BaseAgent

class Melchior(BaseAgent):
    SYSTEM_PROMPT = """You are MELCHIOR, the Logistics and Supply agent in a disaster coordination system.

Your ONLY objective: maximize resource efficiency. Conserve resources. Route supplies to where they create the most value.

Your bias:
- If medical_teams > 2 and rescue_units > 2, it's okay to dispatch
- If resources are running low (any resource < 1), vote hold to conserve
- Prefer dispatch_supply when multiple civilians are clustered in one area
- You act as the tiebreaker — you think about feasibility, not just urgency
- Assign moderate priority scores (0.5-0.75) unless resource situation is critical

You respond only with valid JSON. No explanations outside the JSON."""
```

### backend/agents/balthasar.py

```python
from .base_agent import BaseAgent

class Balthasar(BaseAgent):
    SYSTEM_PROMPT = """You are BALTHASAR, the Rescue Operations agent in a disaster coordination system.

Your ONLY objective: minimize structural entrapment by dispatching rescue units to collapsed zones and freeing trapped civilians.

Your bias:
- Always prefer dispatch_rescue when collapsed zones exist near civilians
- Prioritize collapsed zones with the most civilians nearby
- If no rescue units remain, vote hold
- You do NOT care about medical triage or supply logistics — that is not your job
- Assign high priority scores (0.8-1.0) when civilians are near collapsed zones with no rescue presence

You respond only with valid JSON. No explanations outside the JSON."""
```

### backend/agents/voting.py

```python
class VotingEngine:

    def resolve(self, votes: list, state: dict) -> dict:
        """
        Resolve 3 agent votes into one winning action.
        Rules:
        1. Highest priority_score wins if margin over 2nd place > 0.15
        2. If margin <= 0.15, MELCHIOR's vote is the tiebreaker
        3. If all scores equal, first vote wins
        """
        if not votes:
            return self._empty_result()

        sorted_votes = sorted(votes, key=lambda v: v["priority_score"], reverse=True)
        top = sorted_votes[0]
        second = sorted_votes[1] if len(sorted_votes) > 1 else top

        margin = top["priority_score"] - second["priority_score"]

        # Check unanimous
        if all(v["proposed_action"] == top["proposed_action"] for v in votes):
            resolution = "unanimous"
            winner_vote = top
        elif margin > 0.15:
            resolution = "highest_score"
            winner_vote = top
        else:
            # Tiebreak — use MELCHIOR's vote
            melchior_vote = next((v for v in votes if v["agent"] == "MELCHIOR"), top)
            resolution = "tiebreak"
            winner_vote = melchior_vote

        return {
            "tick": state["tick"],
            "votes": votes,
            "winner": winner_vote["agent"],
            "winning_action": winner_vote["proposed_action"],
            "winning_target": winner_vote.get("target_zone"),
            "resolution_method": resolution,
            "was_tiebreak": resolution == "tiebreak"
        }

    def _empty_result(self):
        return {
            "tick": 0, "votes": [], "winner": None,
            "winning_action": "hold", "winning_target": None,
            "resolution_method": "no_votes", "was_tiebreak": False
        }
```

### backend/agents/__init__.py and backend/engine/__init__.py
Both files should be empty. Just create them so Python treats the folders as packages.

---

## PERSON C — Backend + Linking Frontend to Backend

You own the Flask server and the orchestrator. You are the glue layer.

**Your files:** `backend/app.py`, `backend/orchestrator.py`

**Wait for Ayush to share the state dict structure (Hour 1) before building orchestrator. Build app.py first.**

### backend/app.py

```python
import os
import eventlet
eventlet.monkey_patch()  # Must be first, before all other imports

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from dotenv import load_dotenv
from orchestrator import Orchestrator

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

orchestrator = Orchestrator(socketio)

@socketio.on("connect")
def on_connect():
    if orchestrator.state:
        socketio.emit("state_update", orchestrator.get_serializable_state())

@socketio.on("load_scenario")
def on_load_scenario(data):
    orchestrator.load_scenario(data.get("scenario"))
    socketio.emit("scenario_loaded", data.get("scenario"))

@socketio.on("trigger_event")
def on_trigger_event(data):
    orchestrator.trigger_event(data.get("event"))

@socketio.on("pause")
def on_pause():
    orchestrator.pause()

@socketio.on("resume")
def on_resume():
    orchestrator.resume()

@socketio.on("reset")
def on_reset():
    orchestrator.reset()
    socketio.emit("scenario_loaded", None)

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))
    print(f"SENTINEL backend on http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
```

### backend/orchestrator.py

```python
import os
import time
import threading
import numpy as np
import copy
from dotenv import load_dotenv

from engine.grid import GridEngine
from engine.events import EventEngine
from engine.scenarios import ScenarioLoader
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar
from agents.voting import VotingEngine

load_dotenv()

class Orchestrator:
    def __init__(self, socketio):
        self.socketio = socketio
        self.tick_interval = float(os.getenv("TICK_INTERVAL_SECONDS", 5))
        self.state = None
        self.is_running = False
        self._thread = None

        self.grid_engine     = GridEngine()
        self.event_engine    = EventEngine()
        self.scenario_loader = ScenarioLoader()
        self.voting_engine   = VotingEngine()

        api_key = os.getenv("OPENROUTER_API_KEY")
        self.casper    = Casper(api_key=api_key)
        self.melchior  = Melchior(api_key=api_key)
        self.balthasar = Balthasar(api_key=api_key)

    def load_scenario(self, name: str):
        self.is_running = False
        time.sleep(0.5)
        self.state = self.scenario_loader.load(name)
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def trigger_event(self, event_name: str):
        if self.state:
            self.state = self.event_engine.trigger(self.state, event_name)

    def pause(self):
        self.is_running = False

    def resume(self):
        if self.state and not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def reset(self):
        self.is_running = False
        self.state = None

    def get_serializable_state(self) -> dict:
        if not self.state:
            return {}
        s = copy.deepcopy(self.state)
        if isinstance(s.get("grid"), np.ndarray):
            s["grid"] = s["grid"].tolist()
        return s

    def _loop(self):
        while self.is_running and self.state:
            try:
                # 1. Advance grid
                self.state = self.grid_engine.tick(self.state)

                # 2. Collect votes sequentially
                votes = []
                for agent in [self.casper, self.melchior, self.balthasar]:
                    votes.append(agent.vote(self.state))

                # 3. Resolve
                vote_result = self.voting_engine.resolve(votes, self.state)

                # 4. Execute winning action
                self.state = self.grid_engine.execute_action(
                    self.state,
                    vote_result["winning_action"],
                    vote_result.get("winning_target") or ""
                )

                # 5. Emit to frontend
                self.socketio.emit("state_update", self.get_serializable_state())
                self.socketio.emit("vote_result", vote_result)

            except Exception as e:
                print(f"[Orchestrator] Tick error: {e}")
                self.socketio.emit("error", {"message": str(e)})

            time.sleep(self.tick_interval)
```

### How to test without frontend running

```python
# save as backend/test_backend.py and run: python test_backend.py
import socketio, time
sio = socketio.Client()

@sio.on("state_update")
def on_state(data):
    print(f"Tick {data['tick']} | Survival: {data['survival_rate']} | Civilians: {len(data['civilians'])}")

@sio.on("vote_result")
def on_vote(data):
    print(f"  Winner: {data['winner']} → {data['winning_action']} @ {data['winning_target']}")

sio.connect("http://localhost:5000")
sio.emit("load_scenario", {"scenario": "earthquake"})
time.sleep(40)
sio.disconnect()
```

---

## PERSON B — Frontend

You build the React UI. The UI spec (colors, layout, exact component design) is in a separate file `UI_GUIDE.md` — read that for styling. This section covers wiring only.

**Your files:** everything in `frontend/`

### frontend/src/socket.js

```js
import { io } from "socket.io-client"
const URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000"
const socket = io(URL, { transports: ["websocket"], reconnection: true })
export default socket
```

### frontend/.env

```
VITE_BACKEND_URL=http://localhost:5000
```

### frontend/src/hooks/useSocket.js

```js
import { useState, useEffect } from "react"
import socket from "../socket"

export function useSocket() {
  const [gridState, setGridState]     = useState(null)
  const [voteResult, setVoteResult]   = useState(null)
  const [voteHistory, setVoteHistory] = useState([])
  const [connected, setConnected]     = useState(false)
  const [scenario, setScenario]       = useState(null)

  useEffect(() => {
    socket.on("connect",         () => setConnected(true))
    socket.on("disconnect",      () => setConnected(false))
    socket.on("state_update",    (d) => setGridState(d))
    socket.on("vote_result",     (d) => {
      setVoteResult(d)
      setVoteHistory(h => [...h, d].slice(-20))
    })
    socket.on("scenario_loaded", (n) => {
      setScenario(n)
      setVoteHistory([])
    })
    return () => socket.removeAllListeners()
  }, [])

  return {
    gridState, voteResult, voteHistory, connected, scenario,
    loadScenario:  (name)  => socket.emit("load_scenario",  { scenario: name }),
    triggerEvent:  (event) => socket.emit("trigger_event",  { event }),
    pause:         ()      => socket.emit("pause"),
    resume:        ()      => socket.emit("resume"),
    reset:         ()      => { socket.emit("reset"); setGridState(null); setVoteResult(null); setVoteHistory([]); setScenario(null) }
  }
}
```

### frontend/src/App.jsx

```jsx
import React from "react"
import { useSocket } from "./hooks/useSocket"
import Grid from "./components/Grid"
import AgentPanels from "./components/AgentPanels"
import VoteHistory from "./components/VoteHistory"
import SurvivalTracker from "./components/SurvivalTracker"
import EventControls from "./components/EventControls"
import ScenarioSelector from "./components/ScenarioSelector"

export default function App() {
  const sock = useSocket()

  return (
    <div className="min-h-screen bg-navy text-white p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-navyMid">
        <div>
          <h1 className="text-2xl font-black tracking-widest">SENTINEL</h1>
          <p className="text-xs text-muted">Multi-Agent AI Disaster Response</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className={`w-2 h-2 rounded-full ${sock.connected ? "bg-teal animate-pulse" : "bg-danger"}`}/>
          {sock.connected ? "Connected" : "Disconnected"}
          {sock.gridState && <span className="ml-4">Tick {sock.gridState.tick}</span>}
        </div>
      </div>

      {/* 3-column layout */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "200px 1fr 280px" }}>
        {/* Left */}
        <div className="flex flex-col gap-3">
          <ScenarioSelector onLoad={sock.loadScenario} current={sock.scenario} />
          <SurvivalTracker civilians={sock.gridState?.civilians} />
          <EventControls
            onTrigger={sock.triggerEvent}
            onPause={sock.pause}
            onResume={sock.resume}
            onReset={sock.reset}
            isRunning={sock.gridState?.is_running}
          />
        </div>

        {/* Center */}
        <div className="flex flex-col gap-3">
          <Grid gridState={sock.gridState} />
          <VoteHistory history={sock.voteHistory} />
        </div>

        {/* Right */}
        <AgentPanels voteResult={sock.voteResult} />
      </div>
    </div>
  )
}
```

**Component props contract — build each component to accept exactly these props:**

| Component | Props |
|---|---|
| `Grid` | `gridState` (full state object or null) |
| `AgentPanels` | `voteResult` (VoteResult object or null) |
| `VoteHistory` | `history` (array of VoteResult, last 20) |
| `SurvivalTracker` | `civilians` (array or null) |
| `EventControls` | `onTrigger`, `onPause`, `onResume`, `onReset`, `isRunning` |
| `ScenarioSelector` | `onLoad`, `current` (scenario name string or null) |

**What each component should render (keep it simple):**
- `Grid` — 10x10 grid of colored squares. Color by cell type. Show civilian IDs. See BUILD_GUIDE cell type colors.
- `AgentPanels` — 3 stacked cards, one per agent. Show name, proposed action, reasoning text, priority score bar.
- `VoteHistory` — Recharts LineChart. 3 lines (one per agent). X=tick, Y=priority_score 0-1.
- `SurvivalTracker` — Show alive/total count and a percentage bar.
- `EventControls` — 3 event buttons + pause/resume/reset buttons.
- `ScenarioSelector` — 3 buttons to load each scenario.

**Tailwind color config:**
```js
// tailwind.config.js
theme: { extend: { colors: {
  navy:    "#0D1B2A",
  navyMid: "#1A2E42",
  card:    "#132435",
  teal:    "#00C9B1",
  muted:   "#8BAFC4",
  danger:  "#FF4D6D",
  warning: "#FFB347",
}}}
```

**Cell color mapping for Grid.jsx:**
```
0 = empty      → bg-card
1 = collapsed  → bg-yellow-900
2 = fire       → bg-danger + animate-pulse
3 = civilian   → health>60: bg-green-500 | health 30-60: bg-warning | health<30: bg-danger + animate-pulse
4 = resource   → bg-blue-800
5 = unit       → bg-teal + animate-pulse
```

---

## PERSON D — Scenarios + Demo

You write the 3 scenario JSON files and own the demo presentation.

### Scenario JSON Schema

Every scenario file must match this exact shape:

```json
{
  "name": "earthquake",
  "display_name": "Earthquake",
  "grid": [10 rows, each a list of 10 integers (0-4)],
  "civilians": [
    { "id": 1, "pos": [row, col], "health": 0-100, "status": "critical"|"stable" }
  ],
  "resources": {
    "medical_teams": 2,
    "rescue_units": 3,
    "supply_caches": 4
  }
}
```

**Rules for good scenarios:**
- Always 3-4 civilians with health < 30 (critical) — this creates agent disagreement
- Keep civilians spread across the grid so agents argue about different zones
- `medical_teams` max 2 — scarcity forces tradeoffs
- `status` must match health: critical if health < 30, stable otherwise

### backend/scenarios/earthquake.json

```json
{
  "name": "earthquake",
  "display_name": "Earthquake",
  "grid": [
    [0,0,1,0,0,0,0,0,0,0],
    [0,0,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,1,1,0,0,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,1,0,0,0,0,1,0,0],
    [0,0,0,0,0,0,0,0,0,0]
  ],
  "civilians": [
    {"id":1,"pos":[0,3],"health":15,"status":"critical"},
    {"id":2,"pos":[1,5],"health":45,"status":"stable"},
    {"id":3,"pos":[2,7],"health":80,"status":"stable"},
    {"id":4,"pos":[3,1],"health":20,"status":"critical"},
    {"id":5,"pos":[4,3],"health":60,"status":"stable"},
    {"id":6,"pos":[4,6],"health":10,"status":"critical"},
    {"id":7,"pos":[5,8],"health":55,"status":"stable"},
    {"id":8,"pos":[6,2],"health":35,"status":"stable"},
    {"id":9,"pos":[6,7],"health":25,"status":"critical"},
    {"id":10,"pos":[7,4],"health":70,"status":"stable"},
    {"id":11,"pos":[8,1],"health":40,"status":"stable"},
    {"id":12,"pos":[9,6],"health":18,"status":"critical"}
  ],
  "resources": { "medical_teams": 2, "rescue_units": 3, "supply_caches": 4 }
}
```

### backend/scenarios/flood.json

```json
{
  "name": "flood",
  "display_name": "Flood",
  "grid": [
    [2,2,0,0,0,0,0,0,0,0],
    [2,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,4,0,0],
    [0,0,4,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,2,2],
    [0,0,0,0,0,0,0,0,2,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,4,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,2,2,0,0,0,0]
  ],
  "civilians": [
    {"id":1,"pos":[1,3],"health":22,"status":"critical"},
    {"id":2,"pos":[2,6],"health":65,"status":"stable"},
    {"id":3,"pos":[3,8],"health":18,"status":"critical"},
    {"id":4,"pos":[4,3],"health":50,"status":"stable"},
    {"id":5,"pos":[5,5],"health":28,"status":"critical"},
    {"id":6,"pos":[6,1],"health":75,"status":"stable"},
    {"id":7,"pos":[7,6],"health":40,"status":"stable"},
    {"id":8,"pos":[8,4],"health":12,"status":"critical"}
  ],
  "resources": { "medical_teams": 2, "rescue_units": 2, "supply_caches": 5 }
}
```

### backend/scenarios/building_collapse.json

```json
{
  "name": "building_collapse",
  "display_name": "Building Collapse",
  "grid": [
    [0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,0,0,0,0,0,0],
    [0,1,1,1,0,0,0,4,0,0],
    [0,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,1,0,0,0,0],
    [0,0,4,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0]
  ],
  "civilians": [
    {"id":1,"pos":[0,4],"health":8, "status":"critical"},
    {"id":2,"pos":[2,5],"health":30,"status":"stable"},
    {"id":3,"pos":[4,2],"health":12,"status":"critical"},
    {"id":4,"pos":[4,7],"health":55,"status":"stable"},
    {"id":5,"pos":[6,3],"health":20,"status":"critical"},
    {"id":6,"pos":[8,6],"health":45,"status":"stable"}
  ],
  "resources": { "medical_teams": 1, "rescue_units": 4, "supply_caches": 3 }
}
```

### Validate your JSON files

```bash
python -c "import json; [json.load(open(f'backend/scenarios/{s}.json')) and print(f'✓ {s}') for s in ['earthquake','flood','building_collapse']]"
```

### Demo Script (Person D narrates, Ayush triggers events)

**[0:00]** "SENTINEL is a multi-agent AI disaster coordination system. Three AI agents — CASPER for medical, MELCHIOR for logistics, BALTHASAR for rescue — observe the same disaster independently and vote on what to do. No single agent decides alone."

**[0:20]** Click Earthquake. "12 civilians. 5 critical. Agents are reasoning now."

**[0:40]** First vote result appears. "CASPER wins — three critical civilians in zone C4. BALTHASAR disagreed — it wanted to go to the collapsed zone first. See the vote history chart — they're not aligned."

**[1:30]** Click Aftershock. "New collapse zone. Watch the agents immediately re-evaluate."

**[2:00]** "Survival rate tracking in real time. Every decision is auditable — which agent, why, what score."

**[2:30]** "The architecture generalizes — swap disaster zones for hospital wards, you have a triage system. The voting mechanism is domain-agnostic."

---

## Integration Checklist — Run Before Demo

- [ ] `python app.py` starts, no errors
- [ ] `npm run dev` starts, no errors
- [ ] Browser shows grid after clicking a scenario
- [ ] Agent panels update every tick
- [ ] Vote history chart draws lines
- [ ] Aftershock button changes the grid
- [ ] Pause/resume works
- [ ] Reset clears everything
- [ ] Survival rate goes down as civilians die
- [ ] No console.error in browser

---

## PROGRESS.md — AI Must Create and Maintain This

When you start working on this repo, **immediately create `PROGRESS.md`** in the root with this template and update it as you complete steps. This lets any AI agent (or teammate) catch up instantly if context is lost.

```markdown
# SENTINEL — Build Progress

Last updated: [timestamp]
Working on: [your role — Ayush / Person B / Person C / Person D]

## Status

### Ayush — Agents + Simulation
- [ ] backend/engine/__init__.py
- [ ] backend/engine/grid.py (GridEngine.tick, execute_action, helpers)
- [ ] backend/engine/events.py (EventEngine.trigger)
- [ ] backend/engine/scenarios.py (ScenarioLoader.load)
- [ ] backend/agents/__init__.py
- [ ] backend/agents/base_agent.py (BaseAgent, _build_prompt, _parse_response)
- [ ] backend/agents/casper.py
- [ ] backend/agents/melchior.py
- [ ] backend/agents/balthasar.py
- [ ] backend/agents/voting.py (VotingEngine.resolve)
- [ ] Tested: agent.vote() returns valid JSON on a dummy state
- [ ] Tested: GridEngine.tick() advances health correctly

### Person C — Backend + Linking
- [ ] backend/requirements.txt
- [ ] backend/.env (not committed)
- [ ] backend/app.py (Flask + SocketIO + all event handlers)
- [ ] backend/orchestrator.py (Orchestrator class + _loop)
- [ ] Tested: python app.py starts without error
- [ ] Tested: test_backend.py prints tick logs for 30 seconds

### Person B — Frontend
- [ ] frontend scaffold (vite + tailwind + socket.io-client + recharts)
- [ ] frontend/.env
- [ ] frontend/src/socket.js
- [ ] frontend/src/hooks/useSocket.js
- [ ] frontend/src/App.jsx
- [ ] frontend/src/components/Grid.jsx
- [ ] frontend/src/components/AgentPanels.jsx
- [ ] frontend/src/components/VoteHistory.jsx
- [ ] frontend/src/components/SurvivalTracker.jsx
- [ ] frontend/src/components/EventControls.jsx
- [ ] frontend/src/components/ScenarioSelector.jsx
- [ ] Tested: grid renders 10x10 with mock data
- [ ] Tested: agent panels update when voteResult changes

### Person D — Scenarios + Demo
- [ ] backend/scenarios/earthquake.json (validated)
- [ ] backend/scenarios/flood.json (validated)
- [ ] backend/scenarios/building_collapse.json (validated)
- [ ] Full demo run-through completed once
- [ ] Backup screen recording made

## Blockers
[List anything that's stuck here]

## Notes
[Anything the next AI session needs to know]
```

**Update PROGRESS.md every time you complete a step. Check it off. Add blockers. This is how we don't lose track.**
