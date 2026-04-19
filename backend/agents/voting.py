"""
SENTINEL — Voting Engine
Resolves 3 agent votes into one or more winning actions (Joint Operations).
"""


class VotingEngine:
    def __init__(self, intel_tracker=None):
        self._intel_tracker = intel_tracker

    def resolve(self, votes: list, state: dict) -> dict:
        """
        Refactored for Triarchic Specialist Model (v3.0).
        Melchior is the Logistics Commander and the "Deciding Vote."
        """
        if not votes:
            return self._empty_result(state.get("tick", 0))

        # Step 1: Identify the Commander's Vote
        commander_vote = next((v for v in votes if v["agent"] == "MELCHIOR"), None)
        specialist_votes = [v for v in votes if v["agent"] in ["CASPER", "BALTHASAR"]]
        
        # If no Commander vote (error), fallback to highest specialist score
        if not commander_vote or commander_vote["proposed_action"] == "hold":
            sorted_specs = sorted(specialist_votes, key=lambda v: v["priority_score"], reverse=True)
            if not sorted_specs or sorted_specs[0]["proposed_action"] == "hold":
                return self._empty_result(state.get("tick", 0))
            
            top = sorted_specs[0]
            return {
                "tick": state.get("tick", 0),
                "votes": votes,
                "resolutions": [{
                    "agent": top["agent"],
                    "action": top["proposed_action"],
                    "target": top["target_sector"],
                    "is_joint": False
                }],
                "method": "specialist_fallback",
                "primary_target": top.get("target_sector")
            }

        # Step 2: Melchior's Deciding Vote
        # Check if Melchior is "Ratifying" a specialist's choice (Consensus)
        primary_target = commander_vote.get("target_sector")
        resolutions = []
        
        # Add Melchior's decision
        resolutions.append({
            "agent": "MELCHIOR",
            "action": commander_vote["proposed_action"],
            "target": primary_target,
            "is_joint": False,
            "priority_score": commander_vote.get("priority_score", 0.0)
        })

        # Check for Joint Ops (Did a specialist agree on the sector?)
        is_joint = False
        for sv in specialist_votes:
            if sv.get("target_sector") == primary_target and sv["proposed_action"] != "hold":
                resolutions.append({
                    "agent": sv["agent"],
                    "action": sv["proposed_action"],
                    "target": sv["target_sector"],
                    "is_joint": True,
                    "priority_score": sv.get("priority_score", 0.0)
                })
                is_joint = True

        # Step 3: Result Packaging
        intel_conf = self._get_intel_confidence(state, primary_target)

        return {
            "tick": state.get("tick", 0),
            "votes": votes,
            "resolutions": resolutions,
            "method": "commander_decisive_win" if not is_joint else "consensus_joint_op",
            "primary_target": primary_target,
            "dispatch_fraction": 1.0, # Handled by ResourceManager now
            "intel_confidence": intel_conf
        }

    def _get_intel_confidence(self, state, target_id):
        """Find the surety level for the targeted sector."""
        if not target_id: return "LOW"
        sector = next((s for s in state.get("sectors", []) if s["id"] == target_id), None)
        if sector:
            return sector.get("_confidence_tier", "LOW")
        return "LOW"

    # ── Confidence dispatch fractions ────────────────────────────────────────
    _CONFIDENCE_DISPATCH = {
        "HIGH":        1.0,   # Fully Verified
        "MEDIUM":      0.45,  # News or Multiple Reports
        "LOW":         0.15,  # Unverified Rumor / Probe
    }

    def _empty_result(self, tick=0):
        return {
            "tick": tick,
            "votes": [],
            "resolutions": [],
            "method": "no_votes",
            "primary_target": None
        }
