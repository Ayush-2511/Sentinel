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

## 🧠 2. Meet the Agents
We have three AI "specialists" called Casper, Melchior, and Balthasar. Each has a personality and a specific priority.

1. **🏥 Casper (The Medical Specialist)**:
   - **Goal**: Save the dying.
   - **Strategy**: Casper doesn't care about fire or buildings; he only cares about "Critical" civilians. He will always push to send medical teams to where people are hurting most.

2. **⚖️ Melchior (The Strategist)**:
   - **Goal**: Resource efficiency and conservation.
   - **Strategy**: Melchior is the adult in the room. He tries to balance urgency with long-term survival. He acts as the **Tiebreaker** if the other two agents disagree.

3. **🏗️ Balthasar (The Rescue Specialist)**:
   - **Goal**: Structural safety and evacuation.
   - **Strategy**: Balthasar focuses on collapsed buildings and clearing paths. He pushes to send rescue units to free trapped civilians.

---

## 🗺️ 3. Understanding the Map
The city is divided into **12 Sectors** (like blocks). Each block has a state:

- **Colors**:
  - **⬛ Deep Blue**: Safe/Stable area.
  - **🟧 Amber/Orange**: Medium fire or rising danger.
  - **🟥 Dark Red**: High-intensity fire/Critical danger.
  - **🟫 Dark Brown**: Infrastructure destroyed (Collapsed).
- **Tooltips**: If you hover over a block, you can see exactly how many civilians are safe, critical, or rescued.

---

## 🔥 4. The Physics of Disaster
We’ve built a realistic "Physics Engine" that runs in the background:

- **Fire Spread**: Fire doesn't just stay in one place. It grows over time and "jumps" to neighbor blocks if it gets too intense.
- **Containment**: This is our secret weapon. If you send **any unit** to a burning block, they start "containing" it. This reduces the chance of fire spreading to neighbors by **70%**.
- **Securing an Area**: Once all civilians in a block are stable or rescued, the area is considered "Secured." Fire will naturally start to decay in secured areas.

---

## 🕹️ 5. How the Game Works
The simulation runs in "Ticks" (intervals). Every few seconds:
1. The **City Engine** updates the fire and casualties.
2. The **AI Agents** look at the new data one-by-one.
3. They **Vote** on where to send resources (Medical, Rescue, or Supply).
4. **Consensus** is reached, the unit moves, and the city reacts.

---

## 🚀 6. Quick Start for Members
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

## 📝 7. Pro Tips
- **Watch the Logs**: The "Decision Log" panel shows exactly *why* an agent made a choice.
- **Boxing the fire**: The best strategy is often to surround a fire with units to "contain" it while the Supply Caches put it out.
- **Mock AI**: If you don't have an API key, the system will run with "Mock AI" so you can still test the UI.

---
*Stay Sharp, Sentinel. The city is counting on you.*
