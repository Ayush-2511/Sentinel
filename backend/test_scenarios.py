import os
import time
import copy
from dotenv import load_dotenv
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar
from agents.voting import VotingEngine

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
                {"id": 1, "pos": [2, 2], "health": 15, "status": "critical", "assigned_unit": None},
                {"id": 2, "pos": [8, 8], "health": 20, "status": "critical", "assigned_unit": None},
                {"id": 3, "pos": [5, 5], "health": 25, "status": "critical", "assigned_unit": None}
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
                {"id": 1, "pos": [1, 1], "health": 10, "status": "critical", "assigned_unit": None},
                {"id": 2, "pos": [9, 9], "health": 12, "status": "critical", "assigned_unit": None}
            ]
        }
    },
    "3": {
        "name": "ENTRAPMENT (Structural Crisis)",
        "description": "Civilians trapped in collapsed zones. Balthasar should prioritize rescue.",
        "state": {
            **create_base_state(),
            "civilians": [
                {"id": 1, "pos": [4, 4], "health": 50, "status": "stable", "assigned_unit": None},
                {"id": 2, "pos": [6, 2], "health": 45, "status": "stable", "assigned_unit": None}
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
                {"id": 1, "pos": [3, 3], "health": 15, "status": "critical", "assigned_unit": None},
                {"id": 2, "pos": [7, 7], "health": 10, "status": "critical", "assigned_unit": None}
            ]
        }
    }
}

SCENARIOS["3"]["state"]["grid"][4][4] = 1 
SCENARIOS["3"]["state"]["grid"][6][2] = 1 
SCENARIOS["4"]["state"]["grid"][3][3] = 1 
SCENARIOS["4"]["state"]["grid"][7][7] = 2 

def update_simulated_state(state, winner_data):
    """Update state based on winning action to allow for sequential loops."""
    new_state = copy.deepcopy(state)
    action = winner_data["winning_action"]
    civ_id = winner_data["winning_target_civilian_id"]

    if action == "dispatch_medical" and new_state["resources"]["medical_teams"] > 0:
        new_state["resources"]["medical_teams"] -= 1
        for c in new_state["civilians"]:
            if c["id"] == civ_id:
                c["assigned_unit"] = "medic"
                
    elif action == "dispatch_rescue" and new_state["resources"]["rescue_units"] > 0:
        new_state["resources"]["rescue_units"] -= 1
        for c in new_state["civilians"]:
            if c["id"] == civ_id:
                c["assigned_unit"] = "rescue"

    elif action == "dispatch_supply" and new_state["resources"]["supply_caches"] > 0:
        new_state["resources"]["supply_caches"] -= 1
        
    return new_state

def run_scenario(choice):
    if choice not in SCENARIOS:
        print("Invalid choice.")
        return

    scenario = SCENARIOS[choice]
    current_state = copy.deepcopy(scenario["state"])
    voting_engine = VotingEngine()
    
    print(f"\n{'='*60}")
    print(f"RUNNING SCENARIO: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"{'='*60}")

    agents = [
        Casper(api_key=api_key),
        Melchior(api_key=api_key),
        Balthasar(api_key=api_key)
    ]

    loop_count = 1
    while loop_count <= 5: # Limit to 5 actions per cycle
        print(f"\n--- LOOP #{loop_count} ---")
        print(f"Resources: MED:{current_state['resources']['medical_teams']} RES:{current_state['resources']['rescue_units']} SUP:{current_state['resources']['supply_caches']}")
        
        votes = []
        for agent in agents:
            name = agent.__class__.__name__.upper()
            try:
                vote = agent.vote(current_state)
                votes.append(vote)
                print(f"[{name}] Wants: {vote['proposed_action']} at {vote.get('target_zone', 'N/A')} (Prio: {vote['priority_score']})")
            except Exception as e:
                print(f"[{name}] Error: {e}")

        if not votes:
            break

        result = voting_engine.resolve(votes, current_state)
        print(f"\n>>> RESOLUTION: {result['winner']} wins via {result['resolution_method']}")
        print(f">>> ACTION: {result['winning_action']} -> {result['winning_target']}")

        if result["winning_action"] == "hold":
            print("\nWinning action is HOLD. Ending cycle.")
            break

        # Update state for the next loop
        current_state = update_simulated_state(current_state, result)
        loop_count += 1
        
        # Check if resources are exhausted
        res = current_state["resources"]
        if res["medical_teams"] == 0 and res["rescue_units"] == 0 and res["supply_caches"] == 0:
            print("\nAll resources exhausted. Ending cycle.")
            break

    print(f"\n{'='*60}")
    print(f"SCENARIO COMPLETE. TOTAL ACTIONS TAKEN: {loop_count-1 if result['winning_action'] == 'hold' else loop_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    if not api_key or api_key == "your_groq_key_here":
        print("ERROR: Please set GROQ_API_KEY in your .env file.")
    else:
        while True:
            print("\nSENTINEL - MULTI-ACTION TEST SUITE")
            for k, v in SCENARIOS.items():
                print(f"{k}. {v['name']}")
            print("q. Quit")
            
            choice = input("\nSelect a scenario to run: ").strip().lower()
            if choice == 'q':
                break
            run_scenario(choice)
