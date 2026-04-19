"""
SENTINEL — Resource Manager
Handles unit budgeting, hard-caps, and dispatch logging.
"""

class ResourceManager:
    def __init__(self):
        import os
        os.makedirs("logs", exist_ok=True)
        self.dispatch_history = []  # List of {tick, agent, action, target, units, reason}
        self._load_from_file()

    def _load_from_file(self):
        """Loads historical logs from disk (Last 50 entries)."""
        import json
        import os
        log_path = os.path.join("logs", "resource_dispatches.jsonl")
        if not os.path.exists(log_path):
            return
            
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
                # Take last 50 lines to keep UI snappy
                entries = [json.loads(l.strip()) for l in lines[-50:]]
                # Reverse so newest is at the top [0]
                self.dispatch_history = entries[::-1]
                print(f"[RESOURCE] Restored {len(self.dispatch_history)} events from persistent log.")
        except Exception as e:
            print(f"[RESOURCE] Log recovery failed: {e}")

    def calculate_budget(self, resolution, state):
        """
        Calculates how many units to send based on priority, risk, and global stocks.
        Returns: (units_to_send, requested_units, reason)
        """
        action = resolution["action"]
        target = resolution["target"]
        priority = resolution.get("priority_score", 0.5)
        
        # Resource mapping
        pool_map = {
            "dispatch_medical": "medical_teams",
            "dispatch_rescue": "rescue_units",
            "dispatch_supply": "supply_caches"
        }
        res_key = pool_map.get(action)
        if not res_key:
            return 0, 0, "No resource type matched"

        stock = state["global_resources"].get(res_key, 0)
        
        # 1. DERIVE INTENDED/REQUESTED UNITS (What the situation ideally calls for)
        sector = next((s for s in state["sectors"] if s["id"] == target), None)
        risk = sector.get("risk_index", 0.0) if sector else 0.0
        fire = sector.get("fire_intensity", 0.0) if sector else 0.0

        if (risk > 0.8 or fire > 0.6) and priority > 0.8:
            requested = 3
        elif (risk > 0.4 or fire > 0.2) and priority > 0.6:
            requested = 2
        else:
            requested = 1

        # 2. APPLY HARD CAPS & STOCK LIMITS
        if stock <= 0:
            return 0, requested, "RES_EXHAUSTED"
        
        if stock < 3 and requested > 1:
            return 1, requested, f"CONSERVATION_CAP (Low Stock: {stock})"

        # 3. DYNAMIC BUDGETING (Sent units)
        sent = min(requested, stock)
        
        # Refine sent based on extreme threat protection
        if requested == 3 and stock < 5:
            sent = 2
            return sent, requested, "RESOURCE_PRESERVATION (Stock < 5)"
            
        return sent, requested, "SUCCESSFUL_ALLOCATION"

    def log_dispatch(self, tick, agent, action, target, sent, requested, reason):
        """Records a tactical dispatch event with REQ/SNT/REJ tracking."""
        event = {
            "tick": tick,
            "agent": agent,
            "action": action.replace("dispatch_", "").upper(),
            "target": target,
            "req": requested,
            "snt": sent,
            "rej": max(0, requested - sent),
            "reason": reason
        }
        self.dispatch_history.insert(0, event)
        
        # ── Persistent File Logging ──
        try:
            import json
            import os
            log_path = os.path.join("logs", "resource_dispatches.jsonl")
            with open(log_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"[RESOURCE] Log write failed: {e}")

        # Keep only last 50 events for frontend
        if len(self.dispatch_history) > 50:
            self.dispatch_history.pop()

    def get_history(self):
        return self.dispatch_history
