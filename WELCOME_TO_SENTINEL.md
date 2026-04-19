# 🛡️ Sentinel 2.0: The Ultimate Guide
### *A Team Member's Handbook for Localized Disaster Coordination*

Welcome to **Sentinel 2.0**, a tactical AI system designed to manage city-scale catastrophes. This project isn't just a dashboard; it’s a living simulation where autonomous "brains" work together to save lives in Lucknow.

---

## 🏗️ 1. What is Sentinel?
Imagine a major disaster hits a city. Dispatchers are overwhelmed, resources are limited, and seconds cost lives. **Sentinel** is an AI-driven "Command Center." 

- **Autonomous Decision Making**: Three different AI agents look at the city map, argue over the best move, and vote on what to do.
- **Dynamic Simulation**: Fire spreads, buildings collapse, and people become "critical" in real-time.
- **Real City Geography**: We use the actual coordinates and sectors of **Lucknow** (from Hazratganj to Gomti Nagar).

---

## 🧠 2. Meet the Agents (The 3 AI)
We have three AI "specialists" called Casper, Melchior, and Balthasar. Each has a personality and a specific priority.

1. **🏥 Casper (The Medical Specialist)**:
   - **Goal**: Save the dying.
   - **Strategy**: Casper evaluates civilian health and prioritizes life-saving triage. He focuses entirely on "Critical" civilians and pushes to dispatch medical units to where the casualties are highest.

2. **⚖️ Melchior (The Strategist & Logistics)**:
   - **Goal**: Resource efficiency, containment, and conservation.
   - **Strategy**: Melchior is the adult in the room. He tries to balance urgency with long-term survival, tracking supply caches and optimizing delivery routes. He acts as the **Tiebreaker** if the other two agents disagree.

3. **🏗️ Balthasar (The Rescue Specialist)**:
   - **Goal**: Structural safety and evacuation.
   - **Strategy**: Balthasar focuses on collapsed buildings, hazardous zones, and clearing paths. He pushes to send rescue units to free trapped civilians.

---

## 🗺️ 3. Understanding the Map
The city is divided into **12 Sectors** (like blocks). Each block has a state:

- **Colors**:
  - **⬛ Deep Blue**: Safe/Stable area.
  - **🟧 Amber/Orange**: Medium fire or rising danger.
  - **🟥 Dark Red**: High-intensity fire/Critical danger.
  - **🟫 Dark Brown**: Infrastructure destroyed (Collapsed).
- **Tooltips**: If you hover over a block, you can see exactly how many civilians are safe, critical, or rescued.

The map provides real-time geographic intel to both the user and the AI, updating dynamically as the disaster spreads or subsides.

---

## 🗳️ 4. The Voting System
Instead of relying on a single AI that can hallucinate, Sentinel uses a multi-agent voting architecture:
1. **Analyze**: The three agents independently review the current state of the city and the active intel.
2. **Propose**: Each agent proposes an action based on its unique persona and goals.
3. **Debate & Vote**: They vote on where to send resources. If there is a conflict (e.g., medical vs. rescue), they debate to reach a consensus.
4. **Execute**: Once a majority or tie-breaker is reached, the decision is finalized, and the chosen sector is targeted.

---

## 📦 5. Resources Allotment
In a disaster, you can't save everyone at once. Sentinel manages strict resource pools:
- **Medical Teams**: Dispatched to stabilize critical civilians.
- **Rescue Units**: Deployed to clear collapsed infrastructure and free trapped people.
- **Supply Teams**: Sent to extinguish fires and deliver essential gear.

**Containment**: Sending any unit to a burning block starts "containing" it, reducing the chance of fire spreading to neighbors by **70%**. 
**Recall**: Resources aren't infinite. Units must return to base or be recalled after deployment to become available again. Careful allotment is the key to preventing complete city collapse.

---

## 📡 6. The Intel System
Information is power, but in a crisis, it's chaotic.
- **Intel Tracker**: Sentinel features a dedicated Intel Tracking system that monitors events in real-time.
- **DDoS and Spam Prevention**: Real emergency systems receive enormous noise. The intel pipeline actively filters out duplicate device reports, detects GPS spoofing, and removes bot/DDoS patterns. This ensures the AI agents only react to verified, high-quality civilian SOS signals rather than spam.
- **Dynamic Prioritization**: Not all events are equal. The system categorizes intel by severity (e.g., a massive fire vs. a minor injury) and scales the resource dispatch based on the signal's confidence tier.
- **Agent Awareness**: The AI agents read the active intel stream. If new intel arrives about a sudden building collapse, Balthasar will immediately flag it and argue for a redirection of rescue resources.

---

## 🕹️ 7. How the Game Works
The simulation runs in "Ticks" (intervals). Every few seconds:
1. The **City Engine** updates the fire, casualties, and intel.
2. The **AI Agents** look at the new data one-by-one.
3. They **Vote** on where to send resources.
4. **Consensus** is reached, the unit moves, and the city reacts.

---

## 🚀 8. Quick Start for Members
If you just cloned the repo and want to see the magic happen:

### Backend Setup
1. Go to `backend/` and run `pip install -r requirements.txt`.
2. Add your `GROQ_API_KEY` to the `.env` file.
3. Run `python server.py`. It will start on **port 5001**.

### Frontend Setup
1. Go to `frontend/` and run `npm install`.
2. Run `npm run dev`.
3. Open `http://localhost:5173` in your browser.
4. Click **"URBAN FIRE"** or **"EARTHQUAKE"** and watch the AI take over!

---

## 📝 9. Pro Tips
- **Watch the Logs**: The "Decision Log" panel shows exactly *why* an agent made a choice.
- **Boxing the fire**: The best strategy is often to surround a fire with units to "contain" it while the Supply Caches put it out.
- **Mock AI**: If you don't have an API key, the system will run with "Mock AI" so you can still test the UI.

---
*Stay Sharp, Sentinel. The city is counting on you.*
