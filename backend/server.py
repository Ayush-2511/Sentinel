"""
SENTINEL — Flask-SocketIO Backend Server
Wraps GridEngine + LLM Agents and streams real-time state to the React frontend.
"""

import os
import sys
import json
import threading
import time
import copy

from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from engine.grid import GridEngine
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar
from agents.voting import VotingEngine

# Search .env in backend dir AND parent Sentinel dir
for _env_path in [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.path.dirname(__file__), "..", ".env"),
    os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
]:
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        print(f"[SENTINEL] Loaded .env from {_env_path}")
        break
else:
    load_dotenv()  # fallback

# ── Flask / SocketIO ───────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "sentinel-secret-2024"
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", logger=False, engineio_logger=False)

# ── Engine & Agents ────────────────────────────────────────────────────────────
engine = GridEngine(size=10)
voter  = VotingEngine()

api_key = os.getenv("GROQ_API_KEY")
agents  = []
MOCK_AI = False

if api_key:
    agents = [Casper(api_key), Melchior(api_key), Balthasar(api_key)]
    print("[SENTINEL] LLM agents loaded (GROQ key found).")
else:
    MOCK_AI = True
    print("[SENTINEL] WARNING: No GROQ_API_KEY — running in MOCK AI mode.")
    print("[SENTINEL] Create backend/.env with GROQ_API_KEY=gsk_... to enable real LLMs.")

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "scenarios")

# ── Simulation State (protected by a lock) ─────────────────────────────────────
_lock = threading.Lock()
sim = {
    "state":       None,
    "is_running":  False,
    "is_thinking": False,
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _load_scenario_file(name: str) -> dict | None:
    """Load a scenario JSON and normalise it into a full state dict."""
    path = os.path.join(SCENARIOS_DIR, f"{name}.json")
    if not os.path.exists(path):
        # Try case-insensitive match
        for fn in os.listdir(SCENARIOS_DIR):
            if fn.lower() == f"{name.lower()}.json":
                path = os.path.join(SCENARIOS_DIR, fn)
                break
        else:
            return None

    with open(path) as f:
        data = json.load(f)

    grid = data.get("grid", [[0] * 10 for _ in range(10)])

    # Build fire_map and building_integrity from grid cell values
    # Grid values: 0=empty, 1=collapsed, 2=fire/flood, 3=civilian, 4=resource
    fire_map   = [[0.0] * 10 for _ in range(10)]
    flood_map  = [[0.0] * 10 for _ in range(10)]
    integrity  = [[0.0] * 10 for _ in range(10)]
    for r in range(10):
        for c in range(10):
            v = grid[r][c]
            if v == 1:                    # collapsed building
                integrity[r][c] = 80.0
            elif v == 2:                  # fire / flood hazard cell
                fire_map[r][c] = 3.0     # medium fire to start

    # Normalise civilians
    civilians = []
    for civ in data.get("civilians", []):
        civilians.append({
            "id":        civ["id"],
            "pos":       civ["pos"],
            "health":    float(civ.get("health", 100)),
            "status":    civ.get("status", "stable"),
            "saved":     bool(civ.get("saved", False)),
            "hurt_rate": float(civ.get("hurt_rate", 0)),
        })

    res = data.get("resources", {})
    state = {
        "name":                data.get("name", name),
        "display_name":        data.get("display_name", name),
        "tick":                0,
        "grid":                grid,
        "civilians":           civilians,
        "resources": {
            "medical_teams":  int(res.get("medical_teams", 3)),
            "rescue_units":   int(res.get("rescue_units", 2)),
            "supply_caches":  int(res.get("supply_caches", 2)),
        },
        "fire_map":            data.get("fire_map", fire_map),
        "flood_map":           data.get("flood_map", flood_map),
        "building_integrity":  data.get("building_integrity", integrity),
        "active_units":        [],
        "is_running":          False,
    }
    return state


def _emit_state():
    """Broadcast the current state to all connected clients (thread-safe copy)."""
    with _lock:
        if sim["state"] is None:
            return
        payload = copy.deepcopy(sim["state"])
    socketio.emit("state_update", payload)


def _serialise_vote_result(result: dict) -> dict:
    """Make sure target_zone lists become serialisable."""
    r = dict(result)
    if isinstance(r.get("winning_target"), list):
        r["winning_target"] = r["winning_target"]
    return r


# ══════════════════════════════════════════════════════════════════════════════
#  SIMULATION LOOP  (runs in a background daemon thread)
# ══════════════════════════════════════════════════════════════════════════════

def _simulation_loop():
    """Tick the grid every 2 seconds while is_running is True."""
    print("[SIM] Loop started.")
    while True:
        time.sleep(2.0)

        with _lock:
            if not sim["is_running"] or sim["state"] is None:
                break

        # Advance physics
        with _lock:
            sim["state"] = engine.tick(sim["state"])
            sim["state"]["is_running"] = True
            tick = sim["state"]["tick"]

        print(f"[SIM] Tick {tick}")
        _emit_state()

        # End-condition check
        with _lock:
            state_snap = copy.deepcopy(sim["state"])
        over, reason = engine.is_simulation_over(state_snap)
        if over:
            with _lock:
                sim["is_running"] = False
                if sim["state"]:
                    sim["state"]["is_running"] = False
            socketio.emit("simulation_over", {"reason": reason})
            _emit_state()
            print(f"[SIM] Over — {reason}")
            break

        # Trigger AI vote (agents OR mock mode)
        with _lock:
            already_thinking = sim["is_thinking"]
            has_unsaved = any(
                not c.get("saved") and c["health"] > 0
                for c in sim["state"]["civilians"]
            ) if sim["state"] else False

        if not already_thinking and has_unsaved:
            with _lock:
                sim["is_thinking"] = True
                snap = copy.deepcopy(sim["state"])
            fn = _mock_ai_vote if MOCK_AI else _ai_vote
            threading.Thread(target=fn, args=(snap,), daemon=True).start()

    print("[SIM] Loop ended.")


# ══════════════════════════════════════════════════════════════════════════════
#  MOCK AI VOTING  (used when no GROQ_API_KEY is set)
# ══════════════════════════════════════════════════════════════════════════════

def _mock_ai_vote(state_snapshot: dict):
    """Simulates realistic LLM deliberation without real API calls."""
    import random
    agent_defs = [
        {"name": "CASPER",    "style": "Prioritise most critical civilian first."},
        {"name": "MELCHIOR",  "style": "Balance resources against long-term survival."},
        {"name": "BALTHASAR", "style": "Act on highest immediate threat."},
    ]

    unsaved = [c for c in state_snapshot["civilians"] if not c.get("saved") and c["health"] > 0]
    votes   = []

    try:
        for a in agent_defs:
            name = a["name"]
            socketio.emit("agent_thinking", {"agent": name, "status": "thinking"})
            print(f"[MOCK-AI] {name} deliberating…")
            time.sleep(1.5)   # simulate LLM latency

            if unsaved and state_snapshot["resources"]["medical_teams"] > 0:
                # Pick the lowest-health civilian
                target = min(unsaved, key=lambda c: c["health"])
                action  = "dispatch_medical"
                civ_id  = target["id"]
                score   = round(0.7 + random.uniform(0, 0.25), 2)
                reason  = f"[MOCK] {a['style']} Civilian #{civ_id} has {int(target['health'])} HP."
            elif state_snapshot["resources"]["supply_caches"] > 0:
                action  = "dispatch_supply"
                civ_id  = None
                score   = round(0.4 + random.uniform(0, 0.2), 2)
                reason  = f"[MOCK] {a['style']} Extinguishing fire to slow damage."
            else:
                action  = "hold"
                civ_id  = None
                score   = 0.1
                reason  = "[MOCK] No resources available."

            vote = {
                "agent":            name,
                "proposed_action":  action,
                "target_zone":      None,
                "target_civilian_id": civ_id,
                "reasoning":        reason,
                "priority_score":   score,
                "tick":             state_snapshot.get("tick", 0),
            }
            votes.append(vote)

            socketio.emit("agent_vote", {
                "agent":            name,
                "proposed_action":  action,
                "target_civilian_id": civ_id,
                "reasoning":        reason,
                "priority_score":   score,
                "tick":             state_snapshot.get("tick", 0),
            })
            socketio.emit("agent_thinking", {"agent": name, "status": "done"})

        result = voter.resolve(votes, state_snapshot)

        action = result["winning_action"]
        civ_id = result.get("winning_target_civilian_id")

        with _lock:
            if sim["state"] is not None:
                sim["state"] = engine.execute_action(sim["state"], action, civ_id)

        _emit_state()
        socketio.emit("vote_result", _serialise_vote_result(result))
        print(f"[MOCK-AI] Resolved — winner: {result['winner']}, action: {action}")

    except Exception as e:
        print(f"[MOCK-AI] Error: {e}")
    finally:
        with _lock:
            sim["is_thinking"] = False


# ══════════════════════════════════════════════════════════════════════════════
#  REAL AI VOTING
# ══════════════════════════════════════════════════════════════════════════════

def _ai_vote(state_snapshot: dict):
    """Query all 3 LLM agents, resolve vote, apply winning action, emit result."""
    agent_names = ["CASPER", "MELCHIOR", "BALTHASAR"]
    votes = []

    try:
        for i, agent in enumerate(agents):
            name = agent_names[i]
            socketio.emit("agent_thinking", {"agent": name, "status": "thinking"})
            print(f"[AI] Asking {name}…")

            try:
                vote = agent.vote(state_snapshot)
                votes.append(vote)
                socketio.emit("agent_vote", {
                    "agent":            vote["agent"],
                    "proposed_action":  vote["proposed_action"],
                    "target_civilian_id": vote.get("target_civilian_id"),
                    "reasoning":        vote["reasoning"],
                    "priority_score":   vote["priority_score"],
                    "tick":             vote["tick"],
                })
                socketio.emit("agent_thinking", {"agent": name, "status": "done"})
            except Exception as agent_err:
                err_str  = str(agent_err)
                err_code = None

                # Try to extract HTTP error code (e.g. 429, 500)
                import re as _re
                m = _re.search(r'\b(4\d\d|5\d\d)\b', err_str)
                if m:
                    err_code = int(m.group(1))

                label = f"Error {err_code}" if err_code else "Error"
                print(f"[AI] {name} failed: {label} — {err_str[:120]}")

                socketio.emit("agent_error_detail", {
                    "agent":   name,
                    "code":    err_code,
                    "message": err_str[:200],
                    "label":   label,
                })
                socketio.emit("agent_thinking", {"agent": name, "status": "error"})

                # Use fallback hold vote so voting can still resolve
                votes.append({
                    "agent":            name,
                    "proposed_action":  "hold",
                    "target_zone":      None,
                    "target_civilian_id": None,
                    "reasoning":        f"[{label}] Agent unavailable.",
                    "priority_score":   0.0,
                    "tick":             state_snapshot.get("tick", 0),
                })
            time.sleep(2.0)   # rate-limit between LLM calls

        result = voter.resolve(votes, state_snapshot)

        # Apply winning action to live state
        action = result["winning_action"]
        civ_id = result.get("winning_target_civilian_id")

        with _lock:
            if sim["state"] is not None:
                sim["state"] = engine.execute_action(sim["state"], action, civ_id)

        _emit_state()
        socketio.emit("vote_result", _serialise_vote_result(result))
        print(f"[AI] Vote resolved — winner: {result['winner']}, action: {action}")

    except Exception as e:
        print(f"[AI] Fatal vote error: {e}")
        socketio.emit("agent_error_detail", {"agent": "ALL", "code": None, "message": str(e)[:200], "label": "Fatal Error"})
    finally:
        with _lock:
            sim["is_thinking"] = False


# ══════════════════════════════════════════════════════════════════════════════
#  SOCKET.IO EVENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@socketio.on("connect")
def handle_connect():
    print("[WS] Client connected")
    # Send current state if one is loaded
    with _lock:
        state = copy.deepcopy(sim["state"]) if sim["state"] else None
    if state:
        emit("state_update", state)


@socketio.on("disconnect")
def handle_disconnect():
    print("[WS] Client disconnected")


@socketio.on("load_scenario")
def handle_load_scenario(data):
    name = data.get("scenario", "earthquake")
    print(f"[WS] load_scenario: {name}")

    state = _load_scenario_file(name)
    if state is None:
        emit("error", {"message": f"Scenario '{name}' not found."})
        return

    with _lock:
        sim["is_running"]  = False
        sim["is_thinking"] = False
        sim["state"]       = state

    emit("scenario_loaded", name)
    _emit_state()


@socketio.on("resume")
def handle_resume():
    print("[WS] resume")
    with _lock:
        if sim["state"] is None or sim["is_running"]:
            return
        sim["is_running"]        = True
        sim["state"]["is_running"] = True

    _emit_state()
    threading.Thread(target=_simulation_loop, daemon=True).start()


@socketio.on("pause")
def handle_pause():
    print("[WS] pause")
    with _lock:
        sim["is_running"] = False
        if sim["state"]:
            sim["state"]["is_running"] = False
    _emit_state()


@socketio.on("reset")
def handle_reset():
    print("[WS] reset")
    with _lock:
        sim["is_running"]  = False
        sim["is_thinking"] = False
        sim["state"]       = None
    socketio.emit("state_update", None)


@socketio.on("trigger_event")
def handle_trigger_event(data):
    event = data.get("event", "")
    print(f"[WS] trigger_event: {event}")
    with _lock:
        if sim["state"] is None:
            return
        import numpy as np
        state = sim["state"]
        fire  = np.array(state["fire_map"], dtype=float)

        if event == "fire_spread":
            # Amplify existing fire
            fire[fire > 0.1] = np.minimum(5.0, fire[fire > 0.1] * 2.0)
            state["fire_map"] = fire.tolist()
        elif event == "aftershock":
            # Knock 20 HP off all unsaved civilians
            for civ in state["civilians"]:
                if not civ.get("saved") and civ["health"] > 0:
                    civ["health"] = max(0, civ["health"] - 20)
                    if civ["health"] <= 0:
                        civ["status"] = "dead"
                    elif civ["health"] < 30:
                        civ["status"] = "critical"
        elif event == "resource_depletion":
            state["resources"]["supply_caches"] = max(0, state["resources"]["supply_caches"] - 1)

    _emit_state()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  SENTINEL SERVER  —  http://localhost:5000")
    print("=" * 55)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
