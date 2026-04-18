import os
import time
from dotenv import load_dotenv
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar

# Load API Key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key or api_key == "your_groq_key_here":
    print("ERROR: Please set a valid GROQ_API_KEY in the .env file.")
    exit(1)

# Mock state representing a complex disaster situation
mock_state = {
    "tick": 1,
    "civilians": [
        {"id": 1, "pos": [3, 4], "health": 15, "status": "critical"},
        {"id": 2, "pos": [7, 2], "health": 60, "status": "stable"}
    ],
    "resources": {
        "medical_teams": 2,
        "rescue_units": 3,
        "supply_caches": 4
    },
    "grid": [[0]*10 for _ in range(10)],
    "active_units": [],
    "events": []
}

# Add context for different agents
mock_state["grid"][3][4] = 1  # Collapsed building near critical civilian
mock_state["grid"][7][2] = 2  # Fire near stable civilian

print("--- INITIALIZING AGENTS (GROQ) ---")
agents = [
    Casper(api_key=api_key),
    Melchior(api_key=api_key),
    Balthasar(api_key=api_key)
]

print("\n--- REQUESTING VOTES FROM ALL AGENTS ---")
for agent in agents:
    agent_name = agent.__class__.__name__.upper()
    print(f"\n[{agent_name}] Thinking...")
    try:
        start_time = time.time()
        vote = agent.vote(mock_state)
        end_time = time.time()
        
        print(f"[{agent_name}] VOTE RESULT ({end_time - start_time:.2f}s):")
        print(f"  Action: {vote['proposed_action']}")
        print(f"  Target Zone: {vote['target_zone']}")
        print(f"  Priority: {vote['priority_score']}")
        print(f"  Reasoning: {vote['reasoning']}")
        
    except Exception as e:
        print(f"[{agent_name}] Error: {e}")

print("\n--- TEST COMPLETE ---")
