import numpy as np
import math

class GridEngine:
    """Simple 10x10 grid engine with fire spread and proximity-based health decay."""
    
    def __init__(self, size=10):
        self.size = size

    def tick(self, state):
        """Advance the simulation by one tick."""
        state = state.copy()
        state["tick"] += 1
        
        # 1. Spread fire slowly
        state = self._fire_tick(state)
        
        # 2. Decay civilian health based on proximity to fire
        state = self._health_tick(state)
        
        return state

    def _fire_tick(self, state):
        """Fire spreads slowly to adjacent building cells."""
        fire = np.array(state["fire_map"], dtype=float)
        integrity = np.array(state["building_integrity"], dtype=float)
        new_fire = fire.copy()

        rows, cols = np.where(fire > 0.5)
        for r, c in zip(rows, cols):
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    # Fire can only spread to cells that have something to burn
                    if integrity[nr, nc] > 0 and new_fire[nr, nc] < 0.1:
                        new_fire[nr, nc] = min(5.0, fire[r, c] * 0.15)

        # Fire grows slightly each tick where it already exists
        new_fire[new_fire > 0.1] = np.minimum(5.0, new_fire[new_fire > 0.1] + 0.1)
        
        # Fire decays on empty ground (no fuel)
        new_fire[integrity <= 0] *= 0.5
        
        state["fire_map"] = new_fire.tolist()

        # Damage building integrity where fire burns
        integrity[fire > 0.1] -= fire[fire > 0.1] * 1.0
        integrity = np.clip(integrity, 0, 100)
        state["building_integrity"] = integrity.tolist()

        return state

    def _health_tick(self, state):
        """Civilians lose health based on distance to nearest fire. Saved civilians are skipped."""
        fire = np.array(state["fire_map"], dtype=float)
        fire_cells = np.argwhere(fire > 0.1)
        
        for civ in state["civilians"]:
            if civ.get("saved") or civ["health"] <= 0:
                continue
            
            r, c = civ["pos"]
            
            if len(fire_cells) > 0:
                distances = np.sqrt(np.sum((fire_cells - np.array([r, c]))**2, axis=1))
                min_dist = float(np.min(distances))
            else:
                min_dist = 999
            
            # Proximity damage: closer = more hurt
            # dist 0 -> 10 dmg/tick,  dist 1 -> 5,  dist 3 -> 2.5,  dist 10+ -> ~0.9
            damage = 10.0 / (min_dist + 1.0)
            
            civ["health"] = max(0, round(civ["health"] - damage, 1))
            civ["hurt_rate"] = round(damage, 2)
            
            if civ["health"] <= 0:
                civ["status"] = "dead"
            elif civ["health"] < 30:
                civ["status"] = "critical"
            else:
                civ["status"] = "stable"
        
        return state

    def execute_action(self, state, action, target_civ_id=None):
        """Execute an AI decision on the state."""
        state = state.copy()
        
        if action == "dispatch_medical" and target_civ_id is not None:
            for civ in state["civilians"]:
                if civ["id"] == target_civ_id and civ["health"] > 0:
                    civ["saved"] = True
                    civ["status"] = "saved"
                    break
            state["resources"]["medical_teams"] = max(0, state["resources"]["medical_teams"] - 1)
            
        elif action == "dispatch_supply":
            # Extinguish fire in a 3x3 area around the worst fire
            fire = np.array(state["fire_map"], dtype=float)
            if np.max(fire) > 0:
                worst = np.unravel_index(np.argmax(fire), fire.shape)
                r, c = int(worst[0]), int(worst[1])
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.size and 0 <= nc < self.size:
                            fire[nr, nc] = 0
                state["fire_map"] = fire.tolist()
            state["resources"]["supply_caches"] = max(0, state["resources"]["supply_caches"] - 1)
        
        return state
    
    def get_unsaved_civilians(self, state):
        """Return list of civilians that still need saving (alive and not saved)."""
        return [c for c in state["civilians"] if c["health"] > 0 and not c.get("saved")]
    
    def is_simulation_over(self, state):
        """Check if the loop should end."""
        unsaved = self.get_unsaved_civilians(state)
        if len(unsaved) == 0:
            return True, "ALL CIVILIANS SAVED OR DEAD"
        if state["resources"]["medical_teams"] <= 0 and state["resources"]["supply_caches"] <= 0:
            return True, "ALL RESOURCES EXHAUSTED"
        return False, ""
