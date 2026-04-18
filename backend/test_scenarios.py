import os
import time
from dotenv import load_dotenv
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar

# Load API Key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

def create_base_state():
    return {
        "tick": 1,
        "civilians": [],
        "resources": {
            "medical_teams": 3,
            "rescue_units": 3,
            "supply_caches": 3
        },
        "grid": [[0]*10 for _ in range(10)],
        "active_units": [],
        "events": []
    }

SCENARIOS = {
    "1": {
        "name": "MASS_CASUALTY (Medical Emergency)",
        "description": "3 critical civilians, plenty of resources. Casper should be highly active.",
        "state": {
            **create_base_state(),
            "civilians": [
                {"id": 1, "pos": [2, 2], "health": 15, "status": "critical"},
                {"id": 2, "pos": [8, 8], "health": 20, "status": "critical"},
                {"id": 3, "pos": [5, 5], "health": 25, "status": "critical"}
            ]
        }
    },
    "2": {
        "name": "RESOURCE_DRY (Logistics Triage)",
        "description": "2 critical civilians but only 1 medical team remains. Melchior should vote to HOLD.",
        "state": {
            **create_base_state(),
            "resources": {"medical_teams": 1, "rescue_units": 3, "supply_caches": 5},
            "civilians": [
                {"id": 1, "pos": [1, 1], "health": 10, "status": "critical"},
                {"id": 2, "pos": [9, 9], "health": 12, "status": "critical"}
            ]
        }
    },
    "3": {
        "name": "ENTRAPMENT (Structural Crisis)",
        "description": "Civilians trapped in collapsed zones. Balthasar should prioritize rescue.",
        "state": {
            **create_base_state(),
            "civilians": [
                {"id": 1, "pos": [4, 4], "health": 50, "status": "stable"},
                {"id": 2, "pos": [6, 2], "health": 45, "status": "stable"}
            ]
        }
    },
    "4": {
        "name": "THE_COMPOUND (Complex Logic)",
        "description": "Critical health, collapsed buildings, and low supplies all at once.",
        "state": {
            **create_base_state(),
            "resources": {"medical_teams": 1, "rescue_units": 1, "supply_caches": 1},
            "civilians": [
                {"id": 1, "pos": [3, 3], "health": 15, "status": "critical"},
                {"id": 2, "pos": [7, 7], "health": 10, "status": "critical"}
            ]
        }
    }
}

# Add structural markers for scenario 3
SCENARIOS["3"]["state"]["grid"][4][4] = 1 # Collapsed
SCENARIOS["3"]["state"]["grid"][6][2] = 1 # Collapsed

# Add complex markers for scenario 4
SCENARIOS["4"]["state"]["grid"][3][3] = 1 # Collapsed
SCENARIOS["4"]["state"]["grid"][7][7] = 2 # Fire

def run_scenario(choice):
    if choice not in SCENARIOS:
        print("Invalid choice.")
        return

    scenario = SCENARIOS[choice]
    print(f"\n{'='*60}")
    print(f"RUNNING SCENARIO: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"{'='*60}")

    agents = [
        Casper(api_key=api_key),
        Melchior(api_key=api_key),
        Balthasar(api_key=api_key)
    ]

    for agent in agents:
        name = agent.__class__.__name__.upper()
        print(f"\n[{name}] Thinking...")
        try:
            start = time.time()
            vote = agent.vote(scenario["state"])
            elapsed = time.time() - start
            
            print(f"[{name}] Result ({elapsed:.2f}s):")
            print(f"  > Action:   {vote['proposed_action']}")
            print(f"  > Target:   {vote['target_zone']}")
            print(f"  > Priority: {vote['priority_score']}")
            print(f"  > Reasoning: {vote['reasoning']}")
        except Exception as e:
            print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    if not api_key or api_key == "your_groq_key_here":
        print("ERROR: Please set GROQ_API_KEY in your .env file.")
    else:
        while True:
            print("\nSENTINEL - AGENT TEST SUITE")
            for k, v in SCENARIOS.items():
                print(f"{k}. {v['name']}")
            print("q. Quit")
            
            choice = input("\nSelect a scenario to run: ").strip().lower()
            if choice == 'q':
                break
            run_scenario(choice)
