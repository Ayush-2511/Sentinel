# SENTINEL 2.0 — MASTER PLAN
> This is the single source of truth for the Sentinel City disaster response system.
> It documents the transition from abstract grids to sector-based city simulation.

---

## 1. Project Vision
SENTINEL 2.0 is a tactical, multi-agent AI coordination system designed to manage urban disasters. It uses a **Sector-Based City Model** to simulate life-and-death scenarios (fire, flood, collapse) where three autonomous AI agents (Casper, Melchior, Balthasar) must deliberate and deploy limited resources to save civilians.

---

## 2. Directory Structure
```
sentinel/
├── backend/
│   ├── app.py             ← Entry point (SocketIO + Eventlet)
│   ├── requirements.txt   ← Python dependencies
│   ├── engine/
│   │   ├── city.py        ← Physics Engine (Fire spread, casualties)
│   │   └── events.py      ← Scenario trigger logic
│   ├── agents/
│   │   ├── base_agent.py  ← Prompt engineering & LLM wrapper
│   │   ├── casper.py      ← Medical specialist
│   │   ├── melchior.py    ← Logistics specialist
│   │   ├── balthasar.py   ← Rescue specialist
│   │   └── voting.py      ← Conflict resolution engine
│   └── scenarios/         ← JSON scenario definitions (Lucknow themed)
│       ├── city_fire.json
│       ├── earthquake.json
│       └── flood.json
│
└── frontend/
    ├── src/
    │   ├── App.jsx        ← Main Dashboard
    │   ├── socket.js      ← SocketIO client (polling fallback)
    │   ├── components/
    │   │   ├── CityMap.jsx          ← Leaflet Integration
    │   │   ├── AgentPanels.jsx      ← AI reasoning dashboard
    │   │   ├── SurvivalTracker.jsx  ← Live casualty stats
    │   │   └── ScenarioSelector.jsx ← Mission control
    │   └── hooks/
    │       └── useSocket.js         ← State management hook
```

---

## 3. Core Mechanics

### 3.1 The City Map (Lucknow)
The simulation world is divided into **12 Sectors** (A1 to D3) based on real-world Lucknow coordinates.
- **Sectors**: Named areas like "Hazratganj" or "Gomti Nagar".
- **Types**: Commercial, Residential, Industrial, University.
- **Hazards**: `fire`, `structural_collapse`, `flooding`, `gas_leak`.

### 3.2 Physics Engine (CityEngine)
- **Fire Spread**: Fires grow in intensity and spread to **adjacent** sectors (N/S/E/W) based on intensity.
- **Casualty Logic**: High fire intensity causes `stable` civilians to become `critical`. Critical civilians die without medical intervention.
- **Suppression**:
    - **Supply Caches**: Primary fire fighting (Reduces intensity by 15-30%).
    - **Rescue Units**: Secondary suppression (Reduces intensity by 5%).
    - **Saved Areas**: If a sector is cleared of all at-risk civilians, fire naturally decays (Secured Area Bonus).

### 3.3 Agent Intelligence
- **Sequential Deliberation**: Agents think one-by-one to avoid rate limits.
- **Situational Awareness**: Agents receive raw JSON snapshots of city sectors, fire spread rates, and resource statuses.
- **The Vote**:
    1. Agents propose an action (`dispatch_medical`, `dispatch_rescue`, `dispatch_supply`).
    2. Agents target a specific **Sector ID** (e.g., `B2`).
    3. **VotingEngine** resolves the winner based on `priority_score` (0-1.0), with Melchior serving as the tiebreaker.

---

## 4. Technical Data Contracts

### 4.1 City State Update (Backend → Frontend)
```json
{
  "tick": 42,
  "city_name": "Lucknow",
  "is_running": true,
  "sectors": [
    {
      "id": "A1",
      "name": "Hazratganj",
      "fire_intensity": 0.45,
      "civilians": { "total": 20, "critical": 2, "stable": 15, "rescued": 3 },
      "resources_deployed": { "medical_teams": 1, "rescue_units": 0, "supply_caches": 0 }
    }
  ],
  "global_resources": { "medical_teams": 2, "rescue_units": 2, "supply_caches": 4 }
}
```

### 4.2 Agent Vote (Agent → Backend)
```json
{
  "agent": "BALTHASAR",
  "proposed_action": "dispatch_rescue",
  "target_sector": "B2",
  "reasoning": "High collapse threat in Gomti Nagar residential zone.",
  "priority_score": 0.95
}
```

---

## 5. Development & Startup

### Prerequisites
- Groq API Key (added to `backend/.env` as `GROQ_API_KEY`)
- Node.js (v18+) and Python (3.10+)

### Running the System
1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev -- --port 5173
   ```

---

## 6. Key Files Checklist
- [x] `backend/engine/city.py`: The heart of simulation logic.
- [x] `frontend/src/components/CityMap.jsx`: The Leaflet visualisation layer.
- [x] `backend/agents/base_agent.py`: The prompt engine.
- [x] `backend/server.py`: The SocketIO hub.
- [x] `backend/scenarios/city_fire.json`: The new 6-block fire scenario.

---
*Created by Sentinels for the 24h Hackathon.*
