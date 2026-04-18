import os
import time
import copy
import json
from dotenv import load_dotenv
from agents.casper import Casper
from agents.melchior import Melchior
from agents.balthasar import Balthasar
from agents.voting import VotingEngine

# Load API Key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), "scenarios")

def load_all_scenarios():
    """Dynamically load all JSON scenarios from the scenarios directory."""
    scenarios = {}
    if not os.path.exists(SCENARIOS_DIR):
        print(f"Warning: Scenarios directory not found at {SCENARIOS_DIR}")
        return scenarios
    
    files = [f for f in os.listdir(SCENARIOS_DIR) if f.endswith(".json")]
    for i, file in enumerate(sorted(files), 1):
        path = os.path.join(SCENARIOS_DIR, file)
        try:
            with open(path, "r") as f:
                data = json.load(f)
                # Ensure every civilian has an assigned_unit field for consistency
                if "civilians" in data:
                    for civ in data["civilians"]:
                        if "assigned_unit" not in civ:
                            civ["assigned_unit"] = None
                
                scenarios[str(i)] = {
                    "name": data.get("display_name", data.get("name", file)),
                    "description": f"Loaded from {file}",
                    "state": {
                        **data,
                        "tick": 1,
                        "active_units": [],
                        "events": []
                    }
                }
        except Exception as e:
            print(f"Error loading {file}: {e}")
            
    return scenarios

def update_simulated_state(state, winner_data):
    """
    Update state based on winning action to allow for sequential loops.
    Uses 'winning_target_civilian_id' to stay in sync with VotingEngine.
    """
    new_state = copy.deepcopy(state)
    action = winner_data["winning_action"]
    civ_id = winner_data.get("winning_target_civilian_id")

    if action == "dispatch_medical" and new_state["resources"]["medical_teams"] > 0:
        new_state["resources"]["medical_teams"] -= 1
        if civ_id:
            for c in new_state["civilians"]:
                if c["id"] == civ_id:
                    c["assigned_unit"] = "medic"
                
    elif action == "dispatch_rescue" and new_state["resources"]["rescue_units"] > 0:
        new_state["resources"]["rescue_units"] -= 1
        if civ_id:
            for c in new_state["civilians"]:
                if c["id"] == civ_id:
                    c["assigned_unit"] = "rescue"

    elif action == "dispatch_supply" and new_state["resources"]["supply_caches"] > 0:
        new_state["resources"]["supply_caches"] -= 1
        
    return new_state

def run_scenario(scenario):
    current_state = copy.deepcopy(scenario["state"])
    voting_engine = VotingEngine()
    
    print(f"\n{'='*60}")
    print(f"RUNNING SCENARIO: {scenario['name']}")
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
                start = time.time()
                vote = agent.vote(current_state)
                elapsed = time.time() - start
                votes.append(vote)
                print(f"[{name}] Wants: {vote['proposed_action']} at {vote.get('target_zone', 'N/A')} (Prio: {vote['priority_score']}) [{elapsed:.2f}s]")
            except Exception as e:
                print(f"[{name}] Error: {e}")

        if not votes:
            break

        # Resolve Voting
        result = voting_engine.resolve(votes, current_state)
        winning_vote = next((v for v in votes if v["agent"] == result["winner"]), None)

        print(f"\n{'-'*60}")
        print(f"🗳️  VOTING RESOLUTION: {result['winner']}")
        print(f"{'-'*60}")
        print(f"DECIDED ACTION: {result['winning_action'].upper()}")
        print(f"TARGET AREA:    {result['winning_target']}")
        print(f"METHOD:         {result['resolution_method'].replace('_', ' ').title()}")
        
        if winning_vote:
            print(f"\nREASONING:      {winning_vote['reasoning']}")
            print(f"PRIORITY SCORE: {winning_vote['priority_score']}")

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
        
        print("\n" + "~"*60)
        print("UPDATING ENVIRONMENT FOR NEXT DECISION...")
        print("~"*60)
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"SCENARIO COMPLETE. TOTAL ACTIONS TAKEN: {loop_count-1 if result['winning_action'] == 'hold' else loop_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    if not api_key or api_key == "your_groq_key_here":
        print("ERROR: Please set GROQ_API_KEY in your .env file.")
    else:
        scenarios = load_all_scenarios()
        if not scenarios:
            print("No scenarios found in backend/scenarios/. Exiting.")
            exit(1)
            
        while True:
            print("\nSENTINEL - DYNAMIC SCENARIO TEST SUITE")
            for k, v in scenarios.items():
                print(f"{k}. {v['name']}")
            print("q. Quit")
            
            choice = input("\nSelect a scenario to run: ").strip().lower()
            if choice == 'q':
                break
            if choice in scenarios:
                run_scenario(scenarios[choice])
            else:
                print("Invalid selection.")
