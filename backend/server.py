import eventlet
eventlet.monkey_patch()

import os
import sys
import json
import random
import threading
import time
import copy

from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from engine.city import CityEngine
from engine.events import EventEngine
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar
from agents.voting import VotingEngine
from agents.intel_tracker import IntelTracker

# Search .env in backend dir AND parent Sentinel dir
for _env_path in [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.path.dirname(__file__), "..", ".env"),
]:
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        print(f"[SENTINEL] Loaded .env from {_env_path}")
        break
else:
    load_dotenv()

# ── Flask / SocketIO ───────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "sentinel-secret-2024"
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(
    app, cors_allowed_origins="*", 
    logger=False, engineio_logger=False,
)

# ── Engine & Agents ────────────────────────────────────────────────────────────
city_engine = CityEngine()
event_engine = EventEngine()
intel_tracker = IntelTracker(window=10)
voter = VotingEngine(intel_tracker=intel_tracker)

api_key = os.getenv("GROQ_API_KEY")
agents = []
MOCK_AI = False

if api_key:
    agents = [Casper(api_key), Melchior(api_key), Balthasar(api_key)]
    print("[SENTINEL] LLM agents loaded (GROQ key found).")
else:
    MOCK_AI = True
    print("[SENTINEL] WARNING: No GROQ_API_KEY — running in MOCK AI mode.")

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "scenarios")

# ── Simulation State (protected by a lock) ─────────────────────────────────────
_lock = threading.RLock() # Changed to RLock for re-entrant safety
sim = {
    "state": None,
    "is_running": False,
    "is_thinking": False,
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _load_scenario_file(name: str) -> dict | None:
    """Load a sector-format scenario JSON and initialise runtime fields."""
    path = os.path.join(SCENARIOS_DIR, f"{name}.json")
    if not os.path.exists(path):
        for fn in os.listdir(SCENARIOS_DIR):
            if fn.lower() == f"{name.lower()}.json":
                path = os.path.join(SCENARIOS_DIR, fn)
                break
        else:
            return None

    with open(path) as f:
        data = json.load(f)

    # Compute initial severity + color for each sector
    for sector in data["sectors"]:
        sector["severity_score"] = city_engine._severity(sector)
        sector["color"] = city_engine._color(sector)

    state = {
        "name": data.get("name", name),
        "display_name": data.get("display_name", name),
        "city_name": data.get("city_name", "Unknown City"),
        "description": data.get("description", ""),
        "tick": 0,
        "scenario": name,
        "is_running": False,
        "sectors": data["sectors"],
        "global_resources": data.get("global_resources", {
            "medical_teams": 3, "rescue_units": 3, "supply_caches": 5,
        }),
        "total_civilians": city_engine._total_civilians(data["sectors"]),
        "survival_rate": 1.0,
        "events": [],
        "epicenter": data.get("epicenter"),
    }
    return state


def _emit_state():
    """Broadcast the current state to all connected clients."""
    with _lock:
        if sim["state"] is None:
            return
        payload = copy.deepcopy(sim["state"])
    socketio.emit("state_update", payload)


# ══════════════════════════════════════════════════════════════════════════════
#  SIMULATION LOOP  (background daemon thread)
# ══════════════════════════════════════════════════════════════════════════════

def _simulation_loop():
    """Tick the city every 2 seconds while is_running is True."""
    print("[SIM] Loop started.")
    while True:
        time.sleep(2.0)

        with _lock:
            if not sim["is_running"] or sim["state"] is None:
                break

        # Advance simulation
        with _lock:
            # ── 1. Update Intel Signals (SOS & News Simulation) ──
            if sim["state"] is not None:
                for sector in sim["state"]["sectors"]:
                    # Bug Fix: Initialize intel_signals if first tick hasn't run city.py yet
                    if "intel_signals" not in sector:
                        sector["intel_signals"] = {
                            "sos_count": 0,
                            "news_confirmed": False,
                            "infrastructure_alert": sector["infrastructure"] != "intact"
                        }

                    fire = sector.get("fire_intensity", 0.0)
                    infra_bad = sector["infrastructure"] != "intact"

                    if fire > 0.1 or infra_bad:
                        # ── SOS Simulator (Filtered) ──
                        # Raw citizen noise filtered down to 80% (removes spam/DDoS)
                        raw_noise = random.randint(5, 30) if fire > 0.4 else random.randint(1, 10)
                        sector["intel_signals"]["sos_count"] = int(raw_noise * 0.8)

                        # ── News Monitor ──
                        # 20% chance per tick that a major fire gets media coverage
                        if fire > 0.6 and not sector["intel_signals"]["news_confirmed"]:
                            if random.random() < 0.20:
                                sector["intel_signals"]["news_confirmed"] = True
                                print(f"[NEWS] Flash Report: Large blaze confirmed in {sector['id']}")
                    else:
                        # Safe area — clear all signals
                        sector["intel_signals"]["sos_count"] = 0
                        sector["intel_signals"]["news_confirmed"] = False

            # ── 2. Tick the engine ──
            sim["state"] = city_engine.tick(sim["state"])
            sim["state"]["is_running"] = True
            tick = sim["state"]["tick"]
            
            # ── 3. Escalation Loop: Field Verification ──
            for sector in sim["state"]["sectors"]:
                # If units are present and there is a hazard, escalate to HIGH confidence
                units_present = sum(sector["resources_deployed"].values())
                if units_present > 0 and (sector["fire_intensity"] > 0 or sector["infrastructure"] != "intact"):
                    if not sector.get("_probe_verified", False):
                        sector["_probe_verified"] = True
                        print(f"[INTEL] Sector {sector['id']} ESCALATED to HIGH (Confirmed by Field Units)")

        print(f"[SIM] Tick {tick}")
        _emit_state()

        # End-condition check
        with _lock:
            state_snap = copy.deepcopy(sim["state"])
        over, reason = city_engine.is_simulation_over(state_snap)
        if over:
            with _lock:
                sim["is_running"] = False
                if sim["state"]:
                    sim["state"]["is_running"] = False
            socketio.emit("simulation_over", {"reason": reason})
            _emit_state()
            print(f"[SIM] Over — {reason}")
            break

        # Trigger AI vote
        with _lock:
            already_thinking = sim["is_thinking"]

        if not already_thinking:
            with _lock:
                sim["is_thinking"] = True
                snap = copy.deepcopy(sim["state"])
            fn = _mock_ai_vote if MOCK_AI else _ai_vote
            threading.Thread(target=fn, args=(snap,), daemon=True).start()

    print("[SIM] Loop ended.")


# ══════════════════════════════════════════════════════════════════════════════
#  MOCK AI VOTING
# ══════════════════════════════════════════════════════════════════════════════

def _mock_ai_vote(state_snapshot: dict):
    """Simulates LLM deliberation without real API calls."""
    import random
    agent_defs = [
        {"name": "CASPER", "style": "Prioritise most critical sector first."},
        {"name": "MELCHIOR", "style": "Balance resources for long-term survival."},
        {"name": "BALTHASAR", "style": "Act on highest immediate structural threat."},
    ]

    votes = []
    try:
        # Find sectors that need help
        critical_sectors = sorted(
            state_snapshot["sectors"],
            key=lambda s: s["severity_score"],
            reverse=True,
        )

        for a in agent_defs:
            name = a["name"]
            socketio.emit("agent_thinking", {"agent": name, "status": "thinking"})
            print(f"[MOCK-AI] {name} deliberating…")
            time.sleep(1.5)

            res = state_snapshot["global_resources"]
            top_sector = critical_sectors[0] if critical_sectors else None

            if top_sector and top_sector["civilians"]["critical"] > 0 and res["medical_teams"] > 0:
                action = "dispatch_medical"
                target = top_sector["id"]
                score = round(0.7 + random.uniform(0, 0.25), 2)
                reason = f"[MOCK] {a['style']} {top_sector['name']} has {top_sector['civilians']['critical']} critical."
            elif top_sector and "structural_collapse" in top_sector.get("hazards", []) and res["rescue_units"] > 0:
                action = "dispatch_rescue"
                target = top_sector["id"]
                score = round(0.6 + random.uniform(0, 0.2), 2)
                reason = f"[MOCK] {a['style']} Collapse in {top_sector['name']}."
            elif res["supply_caches"] > 0:
                action = "dispatch_supply"
                target = top_sector["id"] if top_sector else None
                score = round(0.4 + random.uniform(0, 0.2), 2)
                reason = f"[MOCK] {a['style']} Supplying relief."
            else:
                action = "hold"
                target = None
                score = 0.1
                reason = "[MOCK] No resources available."

            vote = {
                "agent": name,
                "proposed_action": action,
                "target_sector": target,
                "reasoning": reason,
                "priority_score": score,
                "tick": state_snapshot.get("tick", 0),
            }
            votes.append(vote)
            socketio.emit("agent_vote", vote)
            socketio.emit("agent_thinking", {"agent": name, "status": "done"})

        result = voter.resolve(votes, state_snapshot)

        # Bug Fix: MOCK mode now uses the same tiered dispatch as REAL mode
        for res in result["resolutions"]:
            action = res["action"]
            target = res["target"]
            fraction = result.get("dispatch_fraction", 1.0)
            pool_map = {"dispatch_medical": "medical_teams", "dispatch_rescue": "rescue_units", "dispatch_supply": "supply_caches"}
            resource_key = pool_map.get(action)
            with _lock:
                total_avail = sim["state"]["global_resources"].get(resource_key, 0) if resource_key and sim["state"] else 0
            units_to_send = 3 if fraction >= 0.8 else 1
            units_to_send = min(max(units_to_send, 1 if action != "hold" else 0), total_avail)
            for _ in range(units_to_send):
                with _lock:
                    if sim["state"]:
                        sim["state"] = city_engine.execute_action(sim["state"], action, target)
                _emit_state()
                time.sleep(0.5)

        socketio.emit("vote_result", result)
        
        if result["resolutions"]:
            actions_str = ", ".join([f"{r['agent']}->{r['action']}" for r in result["resolutions"]])
            print(f"[MOCK-AI] Resolved — {result['method']} | {actions_str}")
        else:
            print(f"[MOCK-AI] Resolved — No Action")

    except Exception as e:
        print(f"[MOCK-AI] Error: {e}")
    finally:
        with _lock:
            sim["is_thinking"] = False


# ══════════════════════════════════════════════════════════════════════════════
#  REAL AI VOTING
# ══════════════════════════════════════════════════════════════════════════════

def _ai_vote(state_snapshot: dict):
    """Query all 3 LLM agents sequentially, resolve vote, apply action."""
    agent_names = ["CASPER", "MELCHIOR", "BALTHASAR"]
    votes = []

    try:
        for i, agent in enumerate(agents):
            name = agent_names[i]
            
            # Check if simulation is still running before each agent thinks
            with _lock:
                if not sim["is_running"]:
                    print(f"[AI] Deliberation halted - Simulation PAUSED.")
                    return

            socketio.emit("agent_thinking", {"agent": name, "status": "thinking"})
            print(f"[AI] Asking {name}…")

            try:
                # pass previous votes for sequential awareness
                vote = agent.vote(state_snapshot, previous_votes=votes)
                votes.append(vote)
                socketio.emit("agent_vote", vote)
                socketio.emit("agent_thinking", {"agent": name, "status": "done"})
            except Exception as agent_err:
                err_str = str(agent_err)
                import re as _re
                m = _re.search(r'\b(4\d\d|5\d\d)\b', err_str)
                err_code = int(m.group(1)) if m else None
                label = f"Error {err_code}" if err_code else "Error"

                print(f"[AI] {name} failed: {label} — {err_str[:120]}")
                socketio.emit("agent_error_detail", {
                    "agent": name, "code": err_code,
                    "message": err_str[:200], "label": label,
                })
                socketio.emit("agent_thinking", {"agent": name, "status": "error"})

                votes.append({
                    "agent": name,
                    "proposed_action": "hold",
                    "target_sector": None,
                    "reasoning": f"[{label}] Agent unavailable.",
                    "priority_score": 0.0,
                    "tick": state_snapshot.get("tick", 0),
                })

            time.sleep(3.0)  # Rate limit: 3s between LLM calls

        result = voter.resolve(votes, state_snapshot)

        # Apply winning resolutions with tiered dispatch
        for res in result["resolutions"]:
            action = res["action"]
            target = res["target"]
            fraction = result.get("dispatch_fraction", 1.0)
            
            # Find available tactical pool
            pool_map = {"dispatch_medical": "medical_teams", "dispatch_rescue": "rescue_units", "dispatch_supply": "supply_caches"}
            resource_key = pool_map.get(action)
            
            with _lock:
                total_avail = sim["state"]["global_resources"].get(resource_key, 0) if resource_key and sim["state"] else 0
            
            # 100% = 3 units, 45% = 1 unit, 15% = 1 unit
            if fraction >= 0.8: units_to_send = 3
            else: units_to_send = 1
            
            units_to_send = min(units_to_send, total_avail)
            if units_to_send < 1 and action != "hold": units_to_send = 1

            for _ in range(units_to_send):
                with _lock:
                    if sim["state"]:
                        sim["state"] = city_engine.execute_action(sim["state"], action, target)
                _emit_state()
                time.sleep(0.5)

        _emit_state()
        socketio.emit("vote_result", result)

        if result["resolutions"]:
            actions_str = ", ".join([f"{r['agent']}->{r['action']}" for r in result["resolutions"]])
            print(f"[AI] Vote resolved — {result['method']} | {actions_str}")
        else:
            print(f"[AI] Vote resolved — No Action")

    except Exception as e:
        print(f"[AI] Fatal vote error: {e}")
        socketio.emit("agent_error_detail", {
            "agent": "ALL", "code": None, "message": str(e)[:200], "label": "Fatal Error",
        })
    finally:
        with _lock:
            sim["is_thinking"] = False


# ══════════════════════════════════════════════════════════════════════════════
#  SOCKET.IO EVENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@socketio.on("connect")
def handle_connect():
    print("[WS] Client connected")
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

    # Bug Fix: Reset all intel state on every scenario load to prevent bleed-over
    intel_tracker.reset()
    for sector in state.get("sectors", []):
        sector.pop("_probe_verified",  None)
        sector.pop("_confidence_tier", None)
        sector["intel_signals"] = {
            "sos_count": 0,
            "news_confirmed": False,
            "infrastructure_alert": sector["infrastructure"] != "intact"
        }

    with _lock:
        sim["is_running"] = False
        sim["is_thinking"] = False
        sim["state"] = state

    emit("scenario_loaded", name)
    _emit_state()


@socketio.on("resume")
def handle_resume():
    print("[WS] resume")
    with _lock:
        if sim["state"] is None or sim["is_running"]:
            return
        sim["is_running"] = True
        sim["state"]["is_running"] = True

    _emit_state()
    # Restart loop (eventlet for monkeypatch compatibility)
    import eventlet
    eventlet.spawn(_simulation_loop)


@socketio.on("pause")
def handle_pause():
    print("[WS] pause")
    with _lock:
        sim["is_running"] = False
        if sim["state"]:
            sim["state"]["is_running"] = False
        sim["is_thinking"] = False
    _emit_state()


@socketio.on("reset")
def handle_reset():
    print("[WS] reset")
    with _lock:
        sim["is_running"] = False
        sim["is_thinking"] = False
        sim["state"] = None
    socketio.emit("state_update", None)


@socketio.on("trigger_event")
def handle_trigger_event(data):
    event = data.get("event", "")
    print(f"[WS] trigger_event: {event}")
    with _lock:
        if sim["state"] is None:
            return
        sim["state"] = event_engine.trigger(sim["state"], event)
    _emit_state()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  SENTINEL SERVER  —  http://localhost:5001")
    print("=" * 55)
    socketio.run(app, host="0.0.0.0", port=5001, debug=False, allow_unsafe_werkzeug=True)
