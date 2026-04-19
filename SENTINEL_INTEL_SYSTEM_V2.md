# Sentinel 2.0: Filtered Intelligence & Asymmetric Response

This document summarizes the upgrades made to the Sentinel Intelligence (Intel) system. The project has transitioned from a "Full Vision" simulation to a "Verified Intelligence" model, mirroring real-world disaster management protocols in India.

## 🏛️ Core Philosophy: "Verified Pulse"
In a real disaster, the cost of under-responding (lives lost) is far higher than over-responding (supplies wasted). However, resources are finite. Sentinel now uses **Sensor Fusion** to scale its response volume based on **Intel Surety**.

---

## 📶 The Three Layers of Intelligence

### 1. The Citizen Pulse (Filtered SOS)
*   **Mechanism**: Simulated mobile SOS signals from civilians.
*   **The Filter**: Sentinel uses an AI-driven "Spam & DDoS" filter that verifies GPS proximity and device reputation.
*   **Surety Contribution**: Low-to-Medium. Sparse reports are treated as "Rumors," while high volumes (20+ unique signals) trigger a significant alert.

### 2. The Institutional Pulse (News & Infrastructure)
*   **Mechanism**: Monitoring local news APIs (ANI/NDTV simulation) and Smart City "Heartbeats" (Power/Network status).
*   **Surety Contribution**: High. A news report combined with a localized power outage provides near-instant verification of a major event.

### 3. The Physical Pulse (Field Escalation)
*   **Mechanism**: Verification by NDRF scout units or Forest Rangers.
*   **The Loop**: A "Low Confidence" sector receives a **Probe** unit. Once that unit is physically present and verifies civilians, the sector is **Escalated to HIGH confidence** for the next tick, authorizing a full tactical batch.

---

## 🚁 Asymmetric Dispatch Logic
The `VotingEngine` no longer sends "all or nothing." It scales the volume of units based on the `Intel Confidence Tier`:

| Tier | Surety Source | Dispatch % | Unit Batch |
| :--- | :--- | :--- | :--- |
| **HIGH** | News + SOS + Infra / Probe Verified | **100%** | **3 Units** (Full Squad) |
| **MEDIUM** | News Confirmed or 10+ SOS Signals | **45%** | **1 Unit** (Significant Probe) |
| **LOW** | Sparse SOS Reports (Unverified) | **15%** | **1 Unit** (Minimum Scout) |

---

## 🛠️ Technical Implementation Summary

### `backend/engine/city.py`
*   **Intel Signals**: Added `intel_signals` state to each sector (`sos_count`, `news_confirmed`, `infra_alert`).
*   **Confidence Logic**: Implemented `_derive_confidence()` to calculate the surety level per-sector based on the signal mix.

### `backend/server.py`
*   **SOS Simulator**: Every tick, random noise is generated and filtered into meaningful SOS counts for impacted areas.
*   **News Monitor**: Implemented a 20% probabilistic "News Confirmation" for high-severity sectors.
*   **Escalation Loop**: Added a post-tick check that upgrades sectors to `HIGH` once units are physically present and see a hazard.
*   **Deadlock Fix**: Upgraded the global lock to `RLock` to support the multi-unit sequential dispatch batches.

### `backend/agents/voting.py`
*   **Dispatch Fractions**: Implemented the `_CONFIDENCE_DISPATCH` mapping.
*   **Transparency**: Added `dispatch_fraction`, `intel_confidence`, and `held_in_reserve` to the resolution payload sent to the frontend.

---

## 🧪 Testing the Intel System
1.  **Watch for Probes**: Send medical units to a sector with only `LOW` confidence. Verify only **1 unit** is dispatched.
2.  **Verify Escalation**: Let the simulation tick once the probe arrives. Look for `[INTEL] Sector XY ESCALATED to HIGH` in the terminal.
3.  **Watch the Batch**: On the next turn, vote for that same sector. Verify the system now sends **3 units** sequentially.
4.  **News Flashes**: Look for `[NEWS]` logs to see sectors jumping to `MEDIUM` confidence before units even arrive.

---
*Created by Antigravity AI for Sentinel Tactical Disaster Simulation.*
