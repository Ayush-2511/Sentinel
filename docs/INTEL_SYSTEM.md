# Sentinel Intel System — Technical Documentation

**File**: `docs/INTEL_SYSTEM.md`  
**Version**: 2.0  
**Last Updated**: April 2026  

---

## Table of Contents

1. [Overview & Core Philosophy](#1-overview--core-philosophy)
2. [The Asymmetry Problem](#2-the-asymmetry-problem)
3. [Intel Signal Architecture](#3-intel-signal-architecture)
4. [The Filtration Pipeline](#4-the-filtration-pipeline)
5. [Confidence Tier Derivation](#5-confidence-tier-derivation)
6. [Zone Risk Index](#6-zone-risk-index)
7. [Agent Priority Scoring](#7-agent-priority-scoring)
8. [Asymmetric Resource Dispatch](#8-asymmetric-resource-dispatch)
9. [Cross-Agent Adjustment Rules](#9-cross-agent-adjustment-rules)
10. [The Escalation Loop](#10-the-escalation-loop)
11. [Real-World India Context](#11-real-world-india-context)
12. [File-by-File Implementation Reference](#12-file-by-file-implementation-reference)
13. [Data Flow Diagram](#13-data-flow-diagram)
14. [Terminal Log Reference](#14-terminal-log-reference)

---

## 1. Overview & Core Philosophy

The Sentinel Intel System transforms the simulation from a "Full Vision" environment (where all agents know everything) into a **"Verified Intelligence"** environment where agents must reason under uncertainty.

This mirrors real-world disaster management, where the response team never has complete information in the first few minutes. The key innovation is:

> **Resources are never gated on confidence. They are *scaled* by confidence.**

This means the system never sends nothing (waiting for perfect information) and never sends everything (wasting scarce resources on a rumor). Every disaster signal gets *some* response, proportional to how verified it is.

---

## 2. The Asymmetry Problem

Under-response and over-response are **not symmetric** in disasters:

| Response Type | Consequence | Severity |
| :--- | :--- | :--- |
| **Under-response** (sent too little) | People die while resources sit idle | **CATASTROPHIC** |
| **Over-response** (sent too much) | Resources unavailable for other sectors | **RECOVERABLE** |

**Key Insight**: The cost of inaction at a real disaster is categorically higher than the cost of acting on a false alarm. Standard confidence-gating systems get this wrong by treating them equally.

**Sentinel's Solution**: Always send a **probe**. If the probe confirms the disaster, send the full force. If it finds nothing, release resources back to the pool.

---

## 3. Intel Signal Architecture

Each sector in the city state carries an `intel_signals` object, initialized by `city.py` on the first tick:

```json
{
  "intel_signals": {
    "sos_count": 12,
    "news_confirmed": false,
    "infrastructure_alert": true
  },
  "_confidence_tier": "LOW",
  "_probe_verified": false
}
```

### Signal Descriptions

| Field | Type | Source | Description |
| :--- | :--- | :--- | :--- |
| `sos_count` | `int` | Citizen SOS Simulator (server.py) | Number of *filtered* SOS signals from this sector per tick |
| `news_confirmed` | `bool` | News Monitor (server.py) | True if a media outlet has confirmed the event |
| `infrastructure_alert` | `bool` | City Engine (city.py) | True if power/buildings are damaged/destroyed |
| `_confidence_tier` | `str` | City Engine (city.py) | Derived tier: `"LOW"`, `"MEDIUM"`, or `"HIGH"` |
| `_probe_verified` | `bool` | Escalation Loop (server.py) | True once a field unit physically confirms the disaster |

---

## 4. The Filtration Pipeline

### Stage 1: Raw Citizen SOS Generation

Every tick, a burning or structurally damaged sector generates a random volume of incoming SOS signals. This simulates the real-world behavior of people calling emergency lines, sending WhatsApp messages, or triggering panic buttons.

```python
# From server.py — _simulation_loop()
raw_noise = random.randint(5, 30) if fire > 0.4 else random.randint(1, 10)
```

### Stage 2: The Spam / DDoS Filter

Real emergency systems receive enormous noise. The Sentinel filter simulates:
- **Duplicate device rejection** (same phone calling twice)
- **GPS spoofing detection** (signal origin doesn't match claimed location)
- **Bot/DDoS pattern removal** (mass automated triggers)

This is modelled by retaining only **80%** of the raw signal volume:

```python
# 20% of signals are discarded as spam
sector["intel_signals"]["sos_count"] = int(raw_noise * 0.8)
```

### Stage 3: News Monitor

The system monitors a simulated news feed (representing ANI, NDTV, or local outlets). A major fire (`fire_intensity > 0.6`) has a **20% chance per tick** of being picked up by media. Once confirmed, this is a permanent, sticky upgrade:

```python
# From server.py — _simulation_loop()
if fire > 0.6 and not sector["intel_signals"]["news_confirmed"]:
    if random.random() < 0.20:
        sector["intel_signals"]["news_confirmed"] = True
        print(f"[NEWS] Flash Report: Large blaze confirmed in {sector['id']}")
```

Once `news_confirmed = True`, it stays True until the sector is safe and signals are cleared.

### Stage 4: Infrastructure Alert (Automatic)

The infrastructure alert requires no human reporting at all. It is a **digital pulse** — if a sector's buildings are damaged or destroyed, the Smart City grid detects the anomaly automatically:

```python
# From city.py — tick()
sector["intel_signals"]["infrastructure_alert"] = sector["infrastructure"] != "intact"
```

---

## 5. Confidence Tier Derivation

After all signals are updated, `city.py`'s `_derive_confidence()` method evaluates them every tick using a **Sensor Fusion** algorithm:

```python
# From city.py — _derive_confidence()
def _derive_confidence(self, sector) -> str:
    sos   = signals.get("sos_count", 0)
    news  = signals.get("news_confirmed", False)
    infra = signals.get("infrastructure_alert", False)

    # Tier 1: Physical field verification (highest authority)
    if sector.get("_probe_verified", False):
        return "HIGH"

    # Tier 2: Multi-factor confirmation (News + Signals)
    if news and (sos > 5 or infra):
        return "HIGH"

    # Tier 3: Single strong source
    if news or sos >= 10:
        return "MEDIUM"

    # Tier 4: Sparse or unverified rumors
    if sos > 0 or infra:
        return "LOW"

    return "LOW"
```

### Decision Matrix

| `news_confirmed` | `sos_count` | `infrastructure_alert` | `_probe_verified` | Result |
| :---: | :---: | :---: | :---: | :---: |
| ✅ | > 5 | any | any | **HIGH** |
| ✅ | any | ✅ | any | **HIGH** |
| any | any | any | ✅ | **HIGH** |
| ✅ | any | any | ❌ | **MEDIUM** |
| ❌ | ≥ 10 | any | ❌ | **MEDIUM** |
| ❌ | 1–9 | any | ❌ | **LOW** |
| ❌ | 0 | ✅ | ❌ | **LOW** |

---

## 6. Zone Risk Index

Each sector carries a `risk_index` (0.0 – 1.0), computed **every tick** by `city.py`'s `_compute_risk_index()`. This is a **composite urgency score** combining three orthogonal signals into one number agents can directly compare:

```python
# From city.py — _compute_risk_index()
risk = (civilian_factor * 0.45) + (hazard_factor * 0.35) + (resource_factor * 0.20)
```

### Factor Breakdown

| Factor | Weight | Formula | Meaning |
| :--- | :---: | :--- | :--- |
| **Civilian Factor** | 45% | `critical / total` | Ratio of critical-to-total civilians. Max when all are critical. |
| **Hazard Factor** | 35% | `(fire × 0.7) + (infra_score × 0.3)` | `infra_score`: intact=0, damaged=0.5, destroyed=1.0 |
| **Resource Coverage Deficit** | 20% | `1.0 if no units; max(0, 1 - units×0.25)` | High score = no help present yet |

### Why Risk Index is Better Than Severity Alone

`severity_score` measures how bad a sector *currently is*.  
`risk_index` measures how **urgent it is to act**. A sector with 5 critical civilians and no units deployed will score higher on `risk_index` than a sector with 10 stable civilians and 3 units already there, even if severity is equal. This is the key distinction: `risk_index` accounts for whether the system has already responded.

### Visibility to Agents

`risk_index` and `_confidence_tier` are both now included in every sector line of the agent prompt:

```
A1 (Market): [8C/2S/0R] | INF:dam | HZ:fire | DEP:1M | SEV:0.72🔥45% | RISK:0.81 | CONF:HIGH
```

---

## 7. Agent Priority Scoring

Each LLM agent generates a `priority_score` (0.0 – 1.0) as part of its JSON vote. This is **not computed by the engine** — it is the agent's own self-assessed confidence in its action. The system prompts bias each agent toward a different scoring band:

### CASPER (Medical Response)
```
Bias:    dispatch_medical > all others
Scoring: 0.8 – 1.0 when critical civilians exist with no medical coverage
Focus:   Civilians with health < 30 first
Veto:    Votes hold only when medical_teams = 0
```
*CASPER scores high on sectors where `civilian_factor` is high and no medical units are deployed.*

### MELCHIOR (Logistics & Supply — Incident Commander)
```
Bias:    Resource efficiency and geographic spread
Scoring: 0.6 – 0.85 for resource-efficient, non-duplicated actions
Focus:   Avoids sending a 4th unit to a covered sector when 3 uncovered sectors exist
Veto:    Only holds when all resources are 0, or all other agents also hold
Special: Tiebreaker — its vote wins when margin ≤ 0.05
```
*MELCHIOR acts as a penalty on wasteful stacking. Its moderate scores force the VotingEngine to consider coverage over pile-on.*

### BALTHASAR (Rescue Operations)
```
Bias:    dispatch_rescue to structural collapse hazards
Scoring: 0.8 – 1.0 when civilians are near collapsed zones with no rescue presence
Focus:   Entrapment risk — sectors with structural_collapse in hazards
Veto:    Votes hold only when rescue_units = 0
```
*BALTHASAR scores high on sectors where `risk_index` is elevated by both hazard_factor (destroyed infra) and resource_factor (no rescue deployed).*

### How `priority_score` and `risk_index` Interact

`risk_index` is objective — computed deterministically by the engine.  
`priority_score` is subjective — self-reported by the LLM based on its mandate.  
They are not the same number. A sector might have `risk_index = 0.9` but CASPER gives `priority_score = 0.3` because it has no medical mandate for a fire sector. This tension is intentional: it forces the VotingEngine to arbitrate between specialist perspectives.

---

## 8. Asymmetric Resource Dispatch

The `VotingEngine` (in `voting.py`) maps each confidence tier to a specific **dispatch fraction** and **unit batch size**:

```python
# From voting.py — _CONFIDENCE_DISPATCH
_CONFIDENCE_DISPATCH = {
    "HIGH":   1.0,   # Fully Verified — commit full tactical batch
    "MEDIUM": 0.45,  # News or Mass Reports — commit significant probe
    "LOW":    0.15,  # Unverified Rumor — commit minimum scout
}
```

This fraction is then translated into a physical unit count by `server.py`:

```python
# From server.py — _ai_vote()
if fraction >= 0.8:
    units_to_send = 3   # Full Squad (HIGH confidence)
else:
    units_to_send = 1   # Probe (MEDIUM or LOW confidence)
```

### Dispatch Summary Table

| Tier | Fraction | Unit Batch | Reserve Held | Use Case |
| :--- | :---: | :---: | :---: | :--- |
| **HIGH** | 100% | 3 Units | 0% | Field-verified or multi-source confirmed |
| **MEDIUM** | 45% | 1 Unit | 55% | News report or 10+ citizen SOS |
| **LOW** | 15% | 1 Scout | 85% | Sparse SOS or infrastructure failure only |

Units in a batch are dispatched **sequentially with a 0.5s delay** between each, allowing the map UI to show them populating the sector one by one.

The `vote_result` payload broadcast to the frontend includes:
- `dispatch_fraction` — the exact fraction used
- `intel_confidence` — the tier that determined it
- `held_in_reserve` — what percentage was deliberately withheld

---

## 9. Cross-Agent Adjustment Rules

The `VotingEngine.resolve()` applies **three cross-agent rules** *before* selecting the winner. These run on the pre-resolution vote pool and can modify, redirect, or override votes to prevent systemic failures.

### Rule 1: All-Hold Override

**Problem**: If all three agents vote `hold`, the simulation freezes while a sector burns.  
**Solution**: The engine detects the all-hold case and forces the highest-scoring agent's vote to escalate into a minimum probe:

```python
# From voting.py — resolve()
if not action_votes:  # All agents voted hold
    worst_sector = max(sectors, key=lambda s: s["severity_score"])
    if worst_sector["severity_score"] > 0.1 and has_resources:
        action = "dispatch_supply" if supply_caches > 0 else "dispatch_medical"
        # Force the best-scoring hold voter to dispatch
        votes = [...override...]
```

Terminal log: `[VOTE] All-Hold Override → Forcing minimum probe to A1`

### Rule 2: Zone Stacking Penalty

**Problem**: All three agents targeting the same sector wastes coverage. Two other sectors may be actively burning.  
**Solution**: Any sector targeted by 2 or more agents incurs a **20% score reduction** on all votes pointing there:

```python
# From voting.py — resolve()
if target_counts[t] >= 2:  # 2+ agents voting for same sector
    v["priority_score"] = round(v["priority_score"] * 0.80, 4)
```

This does not veto the action — the sector may still win. It just reduces its dominance so that a second, equally urgent sector has a chance to surface.  
Terminal log: `[VOTE] Zone Stacking Penalty: CASPER → A1 score reduced to 0.64`

### Rule 3: MELCHIOR Depletion Signal

**Problem**: When only 2 total resources remain, sending them to already-covered sectors is wasteful.  
**Solution**: When `total_remaining ≤ 2`, the engine redirects all votes away from sectors that already have at least one unit deployed:

```python
# From voting.py — resolve()
if total_remaining <= 2:
    covered_sectors = {s["id"] for s in sectors if deployed_units > 0}
    action_votes = [v for v in action_votes if v["target_sector"] not in covered_sectors]
```

This ensures the last units go to new, unprotected sectors rather than reinforcing an already-staffed area.  
Terminal log: `[VOTE] MELCHIOR Depletion Signal: Redirecting from already-covered sectors`

---

## 10. The Escalation Loop

This is the **core of the self-improving intel system**. After every tick, `server.py` checks whether any dispatched "probe" units have physically reached a sector and can confirm the disaster:

```python
# From server.py — _simulation_loop() Phase 3
for sector in sim["state"]["sectors"]:
    units_present = sum(sector["resources_deployed"].values())
    if units_present > 0 and (
        sector["fire_intensity"] > 0 or sector["infrastructure"] != "intact"
    ):
        if not sector.get("_probe_verified", False):
            sector["_probe_verified"] = True
            print(f"[INTEL] Sector {sector['id']} ESCALATED to HIGH (Confirmed by Field Units)")
```

### Escalation Timeline Example

```
Tick 1  → Sector A1 fire_intensity: 0.3
          → SOS count: 4 (below threshold)
          → Confidence: LOW
          → Dispatch: 1 Scout Unit

Tick 2  → Scout unit present in A1
          → _probe_verified = True  (Escalation trigger)
          → Confidence: HIGH  (next derive_confidence call)
          → [INTEL] Sector A1 ESCALATED to HIGH

Tick 3  → VotingEngine sees Confidence: HIGH
          → dispatch_fraction = 1.0
          → Dispatch: 3-unit Full Squad
```

---

## 11. Real-World India Context

The Sentinel Intel System is specifically designed around India's unique disaster response infrastructure:

### Urban Scenarios (City Fire, Building Collapse)
| Sentinel Signal | Real-World Equivalent |
| :--- | :--- |
| `sos_count` | Filtered 112 calls, WhatsApp forwards in RWA groups |
| `news_confirmed` | ANI/NDTV breaking news alerts |
| `infrastructure_alert` | ICCC (Integrated Command & Control Centre) smart grid alerts |
| `_probe_verified` | NDRF scout unit or Civil Defence volunteer confirmation |

### Forest Fire Scenarios
| Sentinel Signal | Real-World Equivalent |
| :--- | :--- |
| `sos_count` | Forest Beat Officer radio reports |
| `news_confirmed` | ISRO Bhuvan thermal hotspot alert or state media |
| `infrastructure_alert` | Power line short-circuit detection in forest range |
| `_probe_verified` | Drone camera live-feed confirmation |

### The "Silent Disaster" Problem
India's greatest challenge in remote/rural areas: **no one is nearby to report**. Sentinel handles this via the `infrastructure_alert` signal — even if zero SOS calls come in, a power grid failure automatically triggers a LOW-confidence probe dispatch. The system never waits for a human report to begin responding.

---

## 12. File-by-File Implementation Reference

### `backend/engine/city.py`
- **`tick()`**: Initializes `intel_feed`, `intel_signals` per sector; calls `_derive_confidence()` and `_compute_risk_index()` every tick.
- **`_compute_risk_index(sector)`**: 3-factor Zone Risk Index (civilian × 0.45 + hazard × 0.35 + coverage deficit × 0.20).
- **`_derive_confidence(sector)`**: Sensor fusion logic. Returns `"HIGH"`, `"MEDIUM"`, or `"LOW"`.

### `backend/server.py`
- **`_simulation_loop()` Phase 1**: SOS Simulator + News Monitor. Updates `intel_signals` before the city engine ticks.
- **`_simulation_loop()` Phase 3**: Escalation Loop. Sets `_probe_verified = True` when field units confirm a hazard.
- **`_ai_vote()`** / **`_mock_ai_vote()`**: Both use the same tiered batch dispatch logic.
- **`handle_load_scenario()`**: Calls `intel_tracker.reset()` and re-initializes all sector `intel_signals` on every scenario load to prevent state bleed.

### `backend/agents/voting.py`
- **`__init__(intel_tracker=None)`**: Accepts `IntelTracker` dependency.
- **`resolve(votes, state)`**: Runs 3 cross-agent rules (all-hold override, stacking penalty, depletion signal), then calculates `dispatch_fraction`.
- **`_get_intel_confidence(state, target_id)`**: Reads `sector["_confidence_tier"]` set by `city.py`.
- **`_CONFIDENCE_DISPATCH`**: Static mapping of tier → fraction.

### `backend/agents/intel_tracker.py`
- **`record(agent, predicted_impact, actual_delta, tick)`**: Logs prediction accuracy per agent.
- **`get_accuracy(agent)`**: Returns rolling 0.0–1.0 accuracy score.
- **`get_all_accuracy()`**: Used in `vote_result` payload for frontend display.
- **`reset()`**: Called on every scenario load.

---

## 13. Data Flow Diagram

```
Every Tick:
┌─────────────────────────────────────────────────────────────┐
│  server.py — Phase 1 (BEFORE city.py tick)                  │
│                                                             │
│  For each sector with fire > 0.1 or infra damaged:          │
│    raw_noise = randint(5–30)                                │
│    sos_count = int(raw_noise × 0.8)   ← Spam Filter         │
│    if fire > 0.6 and random() < 0.20:                       │
│        news_confirmed = True          ← News Monitor         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  city.py — tick() (Phase 2)                                 │
│                                                             │
│  For each sector:                                           │
│    infrastructure_alert = (infra != "intact")               │
│    _confidence_tier = _derive_confidence(sector)            │
│      → reads sos_count, news_confirmed, infra_alert         │
│      → returns LOW / MEDIUM / HIGH                          │
│    risk_index = _compute_risk_index(sector)                 │
│      → civilian_factor×0.45 + hazard_factor×0.35           │
│        + coverage_deficit×0.20                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  server.py — Phase 3 (AFTER city.py tick)                   │
│                                                             │
│  Escalation Loop:                                           │
│    if units_present > 0 and hazard confirmed:               │
│        _probe_verified = True  → forces HIGH next tick      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Agents deliberate (Casper → Melchior → Balthasar)          │
│                                                             │
│  Each agent sees: SEV / RISK / CONF in sector prompt        │
│  Each agent outputs: proposed_action + priority_score       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  VotingEngine.resolve() — Cross-Agent Rules                 │
│                                                             │
│  Rule 1: All-Hold Override → force probe to worst sector    │
│  Rule 2: Zone Stacking Penalty → -20% score if 2+ agents   │
│          pile on same sector                                │
│  Rule 3: MELCHIOR Depletion → redirect last 2 units to     │
│          uncovered sectors only                             │
│                                                             │
│  → _get_intel_confidence() reads _confidence_tier           │
│  → dispatch_fraction = CONFIDENCE_DISPATCH[tier]            │
│  → units_to_send = 3 (HIGH) or 1 (MEDIUM/LOW)               │
│  → Sequential dispatch with 0.5s delay per unit             │
│  → Emits: dispatch_fraction, intel_confidence, held_in_reserve│
└─────────────────────────────────────────────────────────────┘
```

---

## 14. Terminal Log Reference

When running `python server.py`, you will see these intel-related logs:

| Log Prefix | Meaning |
| :--- | :--- |
| `[NEWS] Flash Report: Large blaze confirmed in A1` | News Monitor promoted sector A1 — now MEDIUM/HIGH confidence |
| `[INTEL] Sector B2 ESCALATED to HIGH (Confirmed by Field Units)` | Escalation Loop: probe unit physically verified the sector |
| `[VOTE] All-Hold Override → Forcing minimum probe to A1` | All 3 agents voted hold but a sector was still critical |
| `[VOTE] Zone Stacking Penalty: CASPER → A1 score reduced to 0.64` | 2+ agents targeting same sector; score penalized 20% |
| `[VOTE] MELCHIOR Depletion Signal: Redirecting from already-covered sectors` | Last 2 resources redirected away from covered sectors |
| `[SIM] Tick 5` | One physics tick completed, all signals updated |
| `[AI] Asking CASPER…` | LLM agent deliberation begins for this tick |
| `[AI] Vote resolved — highest_score \| CASPER->dispatch_supply` | VotingEngine result with dispatch method |

---

*This document is maintained by the Antigravity AI development team for the Sentinel Tactical Disaster Simulation.*  
*For simulation balancing, see `SENTINEL_INTEL_SYSTEM_V2.md` in the root Sentinel folder.*
